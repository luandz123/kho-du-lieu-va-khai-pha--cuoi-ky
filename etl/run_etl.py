"""6D: one atomic project full refresh; manifest/report publication after COMMIT."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from psycopg2 import sql

from etl.s05_staging import (ROOT, SPECS, TARGET_DB, SafeError, catalog, config,
                            connect, copy_staging, sha256, verify_sources, verify_staging)
from etl.integration_target import assert_warehouse as assert_project
from etl.s06a_dimensions import insert_dimensions, read_prepared, verify_dimensions, verify_two_view_hashes
from etl.s06b_bridge import RAW, insert_bridge, read_bridge, verify_bridge, verify_bridge_view
from etl.s06c_fact import insert_fact, read_mappings, source_rows, verify_ratings

TARGETS = ("analytics.user_cluster", "analytics.cluster_genre_profile", "dw.fact_rating", "dw.bridge_movie_genre",
           "dw.dim_user", "dw.dim_movie", "dw.dim_date", "dw.dim_genre",
           "staging.users_raw", "staging.movies_raw", "staging.ratings_raw")
CODE_PATHS = ("etl/run_etl.py", "etl/s05_staging.py", "etl/s06a_dimensions.py", "etl/s06b_bridge.py", "etl/s06c_fact.py")


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def scope(fixture_schema=None):
    if fixture_schema is None:
        return "analytics.model_registry", TARGETS
    if not re.fullmatch(r"s06d_test_[0-9a-f]{12}", fixture_schema):
        raise SafeError("INVALID_REFRESH_FIXTURE_NAMESPACE")
    return fixture_schema + ".model_registry", tuple(fixture_schema + "." + p.split(".")[1] for p in TARGETS)


def identifier(qualified):
    return sql.Identifier(*qualified.split("."))


def model_state(conn, registry="analytics.model_registry"):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT row_to_json(r) FROM {} r ORDER BY model_version").format(identifier(registry)))
        rows = [r[0] for r in cur.fetchall()]
    metadata = [{k: v for k, v in r.items() if k not in {"is_active", "is_valid_for_dw"}} for r in rows]
    return {"registry_rows": len(rows), "active": sum(r["is_active"] for r in rows),
            "valid": sum(r["is_valid_for_dw"] for r in rows), "metadata_except_flags_sha256": digest_json(metadata)}


def atomic_refresh(conn, load, verify, *, fixture_schema=None, progress=None):
    """Shared real transaction orchestration for production and isolated fixtures."""
    registry, targets = scope(fixture_schema)
    progress = progress if progress is not None else {}
    phase = "PRE_COMMIT"
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(20261027,1)")
                if fixture_schema is None:
                    assert_project(conn)
                    catalog(conn)  # Validate again under the transaction lock, before writes.
                cur.execute(sql.SQL("LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE").format(identifier(registry)))
                before = model_state(conn, registry)
                cur.execute(sql.SQL("UPDATE {} SET is_active=false,is_valid_for_dw=false").format(identifier(registry)))
                progress["model_invalidated"] = True
                # One explicit statement includes every referencing table; registry is retained.
                cur.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY").format(sql.SQL(",").join(map(identifier, targets))))
                progress["truncate_statements"] = 1
                loaded = load(conn)
                checked = verify(conn)
                after = model_state(conn, registry)
                if after["active"] or after["valid"] or after["registry_rows"] != before["registry_rows"] or after["metadata_except_flags_sha256"] != before["metadata_except_flags_sha256"]:
                    raise SafeError("MODEL_INVALIDATION_OR_METADATA_MISMATCH")
                progress["precommit_checks_passed"] = True
                phase = "COMMIT_REQUESTED"
        return {"transaction": "COMMITTED", "loaded": loaded, "checks": checked,
                "model_before": before, "model_after": after, "truncate_statements": 1}
    except Exception as exc:
        err = SafeError(exc.code if isinstance(exc, SafeError) else "REFRESH_SQL_OR_LOCAL_ERROR")
        err.details = {"database_outcome": "COMMIT_OUTCOME_UNVERIFIED" if phase == "COMMIT_REQUESTED" else "ROLLED_BACK",
                       "sqlstate": getattr(exc, "pgcode", None), "progress": progress.copy()}
        # A healthy connection context rolled back pre-commit errors. For broken
        # connections do not claim an observed rollback; reconnection is required.
        if phase != "COMMIT_REQUESTED" and conn.closed:
            err.details["database_outcome"] = "CONNECTION_LOST_RECONCILIATION_REQUIRED"
        raise err from None


def verify_warehouse(conn, raw_dir):
    """Logical checks only: no historical empty-fact or surrogate fingerprints."""
    assert_project(conn)
    cat = catalog(conn)
    source = json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8"))
    sources = verify_sources(raw_dir, source)
    staging = verify_staging(conn, raw_dir)
    dims = verify_dimensions(conn, read_prepared(conn))
    two = verify_two_view_hashes(conn)
    prepared = read_bridge(conn)
    bridge = verify_bridge(conn, prepared)
    genre_view = verify_bridge_view(conn, prepared)
    ratings = verify_ratings(conn)
    models = model_state(conn)
    with conn.cursor() as cur:
        results = {}
        for name in ["analytics.user_cluster", "analytics.cluster_genre_profile", "analytics.v_active_user_cluster", "analytics.v_active_cluster_genre_profile"]:
            cur.execute(sql.SQL("SELECT count(*) FROM {}").format(identifier(name)))
            results[name] = cur.fetchone()[0]
    if models["active"] or models["valid"] or any(results.values()):
        raise SafeError("OLD_MODEL_OR_RESULTS_STILL_USABLE_AFTER_REFRESH")
    hashes = {t: v["sha256"] for t, v in two["views"].items()}
    hashes.update(movie_genres=genre_view["sha256"], ratings=ratings["canonical_sha256"])
    counts = {t: v["rows"] for t, v in two["views"].items()}
    counts.update(movie_genres=genre_view["rows"], ratings=ratings["rows"])
    verify_sources(raw_dir, source)  # End-of-check guard after the full rating scan.
    return {"catalog_matches": cat["columns_match"] and cat["keys_match"], "source": sources, "staging": staging,
            "dimensions": dims, "bridge": bridge, "ratings": ratings, "canonical_hashes": hashes,
            "row_counts": counts, "models": models, "analytics_results": results,
            "all_four_views_match_contract": True, "ratings_not_multiplied_by_genres": True}


def populate(conn, raw_dir, source, progress):
    counts = {table: source["files"][spec[0]]["line_count"] for table, spec in SPECS.items()}
    counters = {}
    copy_staging(conn, raw_dir, counts, stats=counters)
    progress["staging"] = counters
    insert_dimensions(conn, read_prepared(conn))
    progress["dimensions_loaded"] = True
    prepared = read_bridge(conn)
    insert_bridge(conn, prepared)
    progress["bridge_rows"] = len(prepared["mapped"])
    fact = {}
    insert_fact(conn, source_rows(conn), read_mappings(conn), progress=fact)
    progress["fact"] = fact
    return {"staging_counters": counters, "bridge_rows": len(prepared["mapped"]), "fact_rows": fact["inserted_rows"]}


def readonly_check(c, raw_dir):
    conn = connect(c)
    try:
        conn.set_session(readonly=True, isolation_level="REPEATABLE READ")
        with conn:
            return {"readonly_session": True, "dedicated_read_only_account_verified": False,
                    "checks": verify_warehouse(conn, raw_dir)}
    finally:
        conn.close()


def full_refresh(c, raw_dir):
    source = json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8"))
    verify_sources(raw_dir, source)  # Before opening the write transaction.
    conn = connect(c)
    progress = {}
    try:
        with conn:
            assert_project(conn)
            catalog(conn)
        return atomic_refresh(conn, lambda active: populate(active, raw_dir, source, progress),
                              lambda active: verify_warehouse(active, raw_dir), progress=progress)
    except SafeError as exc:
        if exc.details.get("database_outcome") in {"COMMIT_OUTCOME_UNVERIFIED", "CONNECTION_LOST_RECONCILIATION_REQUIRED"}:
            conn.close()
            try:
                reconciled = readonly_check(c, raw_dir)
                exc.details["reconciliation"] = {"snapshot_checks_pass": True,
                    "canonical_hashes": reconciled["checks"]["canonical_hashes"],
                    "model_state": reconciled["checks"]["models"], "commit_attribution_still_unverified": True}
            except Exception:
                exc.details["reconciliation"] = {"snapshot_checks_pass": False, "commit_attribution_still_unverified": True}
        raise
    finally:
        conn.close()


def version_info():
    files = {p: sha256(ROOT / p) for p in CODE_PATHS}
    return {"name": "P1-S06D-v1", "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "code_state": "WORKING_TREE_HASH_AT_RUN", "bundle_sha256": digest_json(files), "file_sha256": files}


def safe_config(c):
    # Never hash or serialize .env, password, user credential or connection URI.
    value = {"host": c["POSTGRES_HOST"], "port": int(c["POSTGRES_PORT"]), "database": TARGET_DB, "timezone": "UTC",
             "refresh_targets": list(TARGETS), "schema_sha256": sha256(ROOT / "database/schema.sql"),
             "contract_sha256": sha256(ROOT / "docs/shared/data_contract.json"),
             "source_manifest_sha256": sha256(ROOT / "data/source_manifest.json"),
             "canonical_manifest_sha256": sha256(ROOT / "results/eda/canonical_manifest.json")}
    return {"nonsecret_settings": value, "nonsecret_config_sha256": digest_json(value), "credentials_excluded": True}


def atomic_json(path, value):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix="." + path.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def manifest_for(report):
    checks = report["result"]["checks"]
    return {"contract_version": 2, "run_id": report["run_id"], "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "database": TARGET_DB, "canonical_hashes": checks["canonical_hashes"], "row_counts": checks["row_counts"],
            "rating_sum": checks["ratings"]["rating_sum"], "star_counts": checks["ratings"]["star_counts"],
            "min_rated_at_utc": checks["ratings"]["min_rated_at_utc"], "max_rated_at_utc": checks["ratings"]["max_rated_at_utc"],
            "source_hashes": {k: v["sha256"] for k, v in checks["source"].items()},
            "etl_version": report["etl_version"], "nonsecret_config_sha256": report["config"]["nonsecret_config_sha256"],
            "model_state": checks["models"], "p2_intake_status": "NOT_CONFIRMED", "g2_status": "PREPARED_FOR_REVIEW"}


def publish(report, path, manifest_path=None):
    """Only filesystem work here: failure cannot roll back an already committed DB."""
    try:
        atomic_json(path, report)
        if manifest_path is not None:
            atomic_json(manifest_path, manifest_for(report))
        return True
    except Exception:
        report.update(status="DB_COMMITTED_G2_PUBLICATION_FAILED" if report.get("database_committed") else "REPORT_PUBLICATION_FAILED",
                      g2_metadata_published=False, error_category="ATOMIC_ARTIFACT_WRITE_FAILED")
        try:
            atomic_json(path, report)
        except Exception:
            pass
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["refresh", "verify"])
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    args = parser.parse_args()
    run, start = uuid.uuid4().hex, time.monotonic()
    report = {"step": "6D", "action": args.action, "run_id": run, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "etl_version": version_info(), "personal_rows_in_report": False, "database_committed": False}
    try:
        c = config(args.env_file)
        report["config"] = safe_config(c)
        if args.action == "refresh":
            report["result"] = full_refresh(c, args.raw_dir)
            report["database_committed"] = True
        else:
            report["result"] = readonly_check(c, args.raw_dir)
        report["status"] = "PASS"
    except Exception as exc:
        report.update(status="FAIL", error_category=exc.code if isinstance(exc, SafeError) else "LOCAL_OR_CONNECTION_ERROR")
        if isinstance(exc, SafeError):
            report.update(exc.details)
            if exc.details.get("database_outcome") in {"COMMIT_OUTCOME_UNVERIFIED", "CONNECTION_LOST_RECONCILIATION_REQUIRED"}:
                report["database_committed"] = None
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    path = ROOT / "results/warehouse" / ("s06d_" + args.action + "_" + run + ".json")
    ok = publish(report, path, ROOT / "results/warehouse/dw_manifest.json" if report["database_committed"] else None)
    print(json.dumps({"status": report["status"], "run_id": run, "database_committed": report["database_committed"],
                      "database_outcome": report.get("database_outcome"), "report": str(path.relative_to(ROOT)), "error_category": report.get("error_category")}))
    return 0 if ok and report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
