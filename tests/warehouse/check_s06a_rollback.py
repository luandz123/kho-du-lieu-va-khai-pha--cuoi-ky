"""Explicit fixture-only DB test for 6A; no production INSERT/TRUNCATE/DELETE."""
import argparse
import json
import sys
import time
import uuid
from pathlib import Path

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from etl.s05_staging import (SafeError, assert_project, config, connect, sha256,
                            target_counts, verify_staging)
from etl.s06a_dimensions import (DIM_COLUMNS, dimension_counts, insert_dimensions,
                                prepare_dimensions, verify_dimensions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    run_id = uuid.uuid4().hex
    schema = "s06a_test_" + run_id[:12]
    report = {"step": "6A_FIXTURE", "run_id": run_id, "status": "FAIL", "fixture": "INVENTED_ONLY",
              "schema": schema, "test_code_sha256": sha256(Path(__file__)),
              "loader_code_sha256": sha256(ROOT / "etl/s06a_dimensions.py")}
    start = time.monotonic()
    created = False
    conn = None
    try:
        conn = connect(config(args.env_file))
        contract = json.loads((ROOT / "docs/shared/data_contract.json").read_text(encoding="utf-8"))
        codes = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))["source_code_sets"]
        users = [(i + 1, str(101 + i), "F" if i % 2 else "M", age, "4") for i, age in enumerate(contract["age_labels"])]
        movies = [(1, "701", 'Éxample, "fixture" (2001)', "Comedy|Drama"), (2, "702", "No year fixture", "Drama")]
        prepared = prepare_dimensions(users, movies, 946684799, 946684800, contract, codes)
        with conn:
            assert_project(conn)
            before = target_counts(conn)
            stage_before = verify_staging(conn, ROOT / "data/raw/p1_s05/ml-1m")
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
                for table in DIM_COLUMNS:
                    cur.execute(sql.SQL("CREATE TABLE {}.{} (LIKE dw.{} INCLUDING ALL)").format(sql.Identifier(schema), sql.Identifier(table), sql.Identifier(table)))
        created = True
        bad = {"rows": {k: list(v) for k, v in prepared["rows"].items()}, "utc": prepared["utc"]}
        bad["rows"]["dim_date"].append(bad["rows"]["dim_date"][0])
        progress = {}
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_advisory_xact_lock(20261027,1)")
                insert_dimensions(conn, bad, schema, progress)
        except psycopg2.Error as exc:
            if exc.pgcode != "23505":
                raise
            report["expected_sqlstate"] = exc.pgcode
        else:
            raise SafeError("FIXTURE_ERROR_DID_NOT_OCCUR")
        with conn:
            after_failure = dimension_counts(conn, schema)
        if any(after_failure.values()) or set(progress) != {"dim_user", "dim_movie", "dim_genre"}:
            raise SafeError("FOUR_DIMENSION_ROLLBACK_NOT_PROVEN")
        with conn:
            with conn.cursor() as cur:
                cur.execute("SET LOCAL TIME ZONE 'Asia/Bangkok'")
            insert_dimensions(conn, prepared, schema)
            verified = verify_dimensions(conn, prepared, schema)
        with conn:
            if before != target_counts(conn) or stage_before != verify_staging(conn, ROOT / "data/raw/p1_s05/ml-1m"):
                raise SafeError("PRODUCTION_CHANGED_DURING_FIXTURE")
        report.update(status="PASS", inserted_before_date_failure=progress, after_rollback_counts=after_failure,
                      all_four_rolled_back=True, production_staging_and_targets_unchanged=True,
                      successful_fixture_dimensions=verified, fixture_timezone="Asia/Bangkok",
                      seven_age_labels_verified=True, null_year_and_special_title_exact=True,
                      utc_midnight_and_generated_calendar_verified=True, identity_sequence_gaps_are_allowed=True)
    except Exception as exc:
        report.update(error_category=exc.code if isinstance(exc, SafeError) else "FIXTURE_DATABASE_OR_LOCAL_ERROR", sqlstate=getattr(exc, "pgcode", None))
        if conn:
            conn.rollback()
    finally:
        if conn and created:
            try:
                with conn:
                    with conn.cursor() as cur:
                        for table in reversed(DIM_COLUMNS):
                            cur.execute(sql.SQL("DROP TABLE {}.{}").format(sql.Identifier(schema), sql.Identifier(table)))
                        cur.execute(sql.SQL("DROP SCHEMA {}").format(sql.Identifier(schema)))
                report["fixture_schema_removed"] = True
            except Exception:
                report.update(status="FAIL", error_category="FIXTURE_CLEANUP_REQUIRED", fixture_schema_removed=False)
        if conn:
            conn.close()
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    path = ROOT / "results/warehouse" / ("s06a_fixture_" + run_id + ".json")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "report": str(path.relative_to(ROOT)), "error_category": report.get("error_category")}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
