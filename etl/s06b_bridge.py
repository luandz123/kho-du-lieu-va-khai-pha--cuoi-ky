"""6B: insert only movie/genre bridge into the verified post-6A database."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from psycopg2 import sql
from psycopg2.extras import execute_values

from etl.s05_staging import (ROOT, TARGET_DB, SafeError, assert_project, catalog,
                            config, connect, sha256, target_counts, verify_sources)
from etl.s06a_dimensions import (DIM_COLUMNS, integer, read_prepared, snapshot_check,
                                verify_dimensions, verify_two_view_hashes)

EXPECTED_HASH = "9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf"
RAW = ROOT / "data/raw/p1_s05/ml-1m"


def namespace(schema):
    if schema != "dw" and not re.fullmatch(r"s06b_test_[0-9a-f]{12}", schema):
        raise SafeError("INVALID_BRIDGE_NAMESPACE")
    return sql.Identifier(schema)


def unique_map(rows, label):
    result, keys = {}, set()
    for natural, surrogate in rows:
        if natural is None or surrogate is None or not isinstance(surrogate, int) or surrogate <= 0:
            raise SafeError("INVALID_" + label + "_MAPPING")
        if natural in result or surrogate in keys:
            raise SafeError("NON_UNIQUE_" + label + "_MAPPING")
        result[natural] = surrogate
        keys.add(surrogate)
    return result


def prepare_bridge(movies, movie_mapping, genre_mapping, allowed_genres):
    """Fail on missing/ambiguous mappings or duplicate source pairs; never drop rows."""
    movie_map = unique_map(movie_mapping, "MOVIE")
    genre_map = unique_map(genre_mapping, "GENRE")
    pairs, mapped, counts, seen = [], [], {}, set()
    for _, raw_id, _title, raw_genres in movies:
        mid = integer(raw_id, 1, 2**31 - 1, "MOVIE_ID")
        if mid in counts:
            raise SafeError("DUPLICATE_SOURCE_MOVIE")
        if mid not in movie_map:
            raise SafeError("MISSING_MOVIE_MAPPING")
        if not isinstance(raw_genres, str) or not raw_genres:
            raise SafeError("EMPTY_SOURCE_GENRES")
        parts = raw_genres.split("|")
        counts[mid] = len(parts)
        for genre in parts:
            pair = (mid, genre)
            if pair in seen:
                raise SafeError("DUPLICATE_SOURCE_MOVIE_GENRE")
            if genre not in allowed_genres:
                raise SafeError("UNKNOWN_SOURCE_GENRE")
            if genre not in genre_map:
                raise SafeError("MISSING_GENRE_MAPPING")
            seen.add(pair)
            pairs.append(pair)
            mapped.append((movie_map[mid], genre_map[genre]))
    if set(counts) != set(movie_map):
        raise SafeError("SOURCE_AND_DIMENSION_MOVIE_SET_DIFFER")
    return {"pairs": sorted(pairs), "mapped": sorted(mapped), "genre_counts": counts}


def read_bridge(conn):
    codes = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))["source_code_sets"]
    with conn.cursor() as cur:
        cur.execute("SELECT source_line,movie_id_raw,title_raw,genres_raw FROM staging.movies_raw ORDER BY source_line")
        movies = cur.fetchall()
        cur.execute("SELECT movie_id,movie_key FROM dw.dim_movie ORDER BY movie_id")
        movie_map = cur.fetchall()
        cur.execute("SELECT genre_name,genre_key FROM dw.dim_genre ORDER BY genre_name")
        genre_map = cur.fetchall()
    prepared = prepare_bridge(movies, movie_map, genre_map, set(codes["genres"]))
    manifest = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))
    if len(prepared["pairs"]) != manifest["row_counts"]["movie_genres"]:
        raise SafeError("BRIDGE_SOURCE_COUNT_DIFFERS_FROM_MANIFEST")
    return prepared


def dimension_fingerprints(conn):
    """All physical fields including surrogate keys; publish only aggregate hashes."""
    result = {}
    with conn.cursor() as cur:
        for table in DIM_COLUMNS:
            cur.execute(sql.SQL("SELECT * FROM dw.{} ORDER BY 1").format(sql.Identifier(table)))
            rows = cur.fetchall()
            body = json.dumps(rows, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8")
            result[table] = {"rows": len(rows), "all_fields_sha256": hashlib.sha256(body).hexdigest()}
    return result


def preserved_state(conn, raw_dir):
    assert_project(conn)
    cat = catalog(conn)
    snapshot = snapshot_check(conn, raw_dir)
    dims = verify_dimensions(conn, read_prepared(conn))
    hashes = verify_two_view_hashes(conn)
    counts = target_counts(conn)
    empty = {k: v for k, v in counts.items() if k not in {"dw." + t for t in DIM_COLUMNS} | {"dw.bridge_movie_genre"}}
    if any(empty.values()):
        raise SafeError("FACT_OR_ANALYTICS_NOT_EMPTY_STOP_FOR_PROVENANCE")
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM dw.v_ml_ratings")
        if cur.fetchone()[0] != 0:
            raise SafeError("RATINGS_VIEW_NOT_EMPTY")
    return {"catalog_matches": cat["columns_match"] and cat["keys_match"], "s05_snapshot": snapshot,
            "dimensions": dims, "canonical_two_views": hashes, "dimension_fingerprints": dimension_fingerprints(conn),
            "unloaded_target_counts": empty, "ratings_view_rows": 0}


def bridge_count(conn, schema="dw"):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT count(*) FROM {}.bridge_movie_genre").format(namespace(schema)))
        return cur.fetchone()[0]


def insert_bridge(conn, prepared, schema="dw"):
    ns = namespace(schema)
    if bridge_count(conn, schema):
        raise SafeError("BRIDGE_NOT_EMPTY_STOP_FOR_PROVENANCE")
    if not prepared["mapped"] or len(prepared["mapped"]) != len(prepared["pairs"]):
        raise SafeError("INVALID_PREPARED_BRIDGE")
    with conn.cursor() as cur:
        command = sql.SQL("INSERT INTO {}.bridge_movie_genre (movie_key,genre_key) VALUES %s").format(ns)
        execute_values(cur, command.as_string(conn), prepared["mapped"], page_size=1000)


def verify_bridge(conn, prepared, schema="dw"):
    ns = namespace(schema)
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT movie_key,genre_key FROM {}.bridge_movie_genre ORDER BY movie_key,genre_key").format(ns))
        physical = cur.fetchall()
        if physical != prepared["mapped"] or len(physical) != len(set(physical)):
            raise SafeError("BRIDGE_PHYSICAL_PAIR_OR_PK_MISMATCH")
        # LEFT JOIN ensures missing references cannot disappear from reconciliation.
        cur.execute(sql.SQL("SELECT m.movie_id,g.genre_name FROM {s}.bridge_movie_genre b LEFT JOIN {s}.dim_movie m ON m.movie_key=b.movie_key LEFT JOIN {s}.dim_genre g ON g.genre_key=b.genre_key").format(s=ns))
        pairs = cur.fetchall()
        if any(mid is None or g is None for mid, g in pairs):
            raise SafeError("BRIDGE_ORPHAN_FK")
        if sorted(pairs) != prepared["pairs"]:
            raise SafeError("BRIDGE_LOGICAL_PAIR_MISMATCH")
        counts = {}
        for mid, _ in pairs:
            counts[mid] = counts.get(mid, 0) + 1
        if counts != prepared["genre_counts"]:
            raise SafeError("PER_MOVIE_GENRE_COUNT_MISMATCH")
    return {"rows": len(pairs), "duplicate_pairs": 0, "orphan_fks": 0,
            "all_source_pairs_exact": True, "per_movie_genre_counts_exact": True,
            "movies": len(counts), "multi_genre_movies": sum(n > 1 for n in counts.values())}


def canonical_bridge_frame(columns, rows):
    if list(columns) != ["movie_id", "genre_name"]:
        raise SafeError("BRIDGE_VIEW_COLUMN_ORDER_MISMATCH")
    return pd.DataFrame(rows, columns=columns).sort_values(["movie_id", "genre_name"], kind="stable").reset_index(drop=True)


def verify_bridge_view(conn, prepared):
    # Also verifies that the same serializer Git blob and physical checkout remain reviewed.
    verify_two_view_hashes(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM dw.v_ml_movie_genres ORDER BY movie_id,genre_name")
        columns, rows = [c.name for c in cur.description], cur.fetchall()
    if rows != prepared["pairs"]:
        raise SafeError("BRIDGE_VIEW_NOT_EXACT_SOURCE_PAIRS")
    frame = canonical_bridge_frame(columns, rows)
    actual = importlib.import_module("mining.data_io").compute_canonical_hash("movie_genres", frame)
    manifest = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))
    if actual != EXPECTED_HASH or actual != manifest["canonical_hashes"]["movie_genres"]:
        raise SafeError("BRIDGE_CANONICAL_HASH_MISMATCH")
    return {"rows": len(rows), "columns": columns, "sha256": actual, "canonical_hash_matches": True}


def verify_post(conn, raw_dir, baseline=None):
    preserved = preserved_state(conn, raw_dir)
    prepared = read_bridge(conn)
    bridge = verify_bridge(conn, prepared)
    view = verify_bridge_view(conn, prepared)
    if baseline is None:
        load_reports = []
        for path in (ROOT / "results/warehouse").glob("s06b_load_*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("status") == "PASS" and data.get("result", {}).get("transaction") == "COMMITTED":
                load_reports.append(data)
        if len(load_reports) != 1:
            raise SafeError("UNAMBIGUOUS_6B_LOAD_BASELINE_REQUIRED")
        baseline = load_reports[0]["result"]["before"]
    if preserved != baseline:
        raise SafeError("PRESERVED_STATE_CHANGED")
    return {"preserved": preserved, "bridge": bridge, "canonical_movie_genres": view,
            "dimensions_including_surrogates_unchanged": True, "staging_unchanged": True, "g2_complete": False}


def preflight(c, raw_dir):
    conn = connect(c)
    try:
        conn.set_session(readonly=True, isolation_level="REPEATABLE READ")
        with conn:
            state = preserved_state(conn, raw_dir)
            if bridge_count(conn):
                raise SafeError("BRIDGE_NOT_EMPTY_STOP_FOR_PROVENANCE")
            prepared = read_bridge(conn)
            return {"readonly": True, "preserved": state, "bridge_rows": 0, "expected_source_pairs": len(prepared["pairs"])}
    finally:
        conn.close()


def load_bridge(c, raw_dir):
    conn = connect(c)
    phase = "PRE_COMMIT"
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(20261027,1)")
                cur.execute("LOCK TABLE staging.users_raw,staging.movies_raw,staging.ratings_raw IN SHARE MODE")
                cur.execute("LOCK TABLE dw.dim_user,dw.dim_movie,dw.dim_genre,dw.dim_date,dw.bridge_movie_genre,dw.fact_rating,analytics.model_registry,analytics.user_cluster,analytics.cluster_genre_profile IN SHARE ROW EXCLUSIVE MODE")
            before = preserved_state(conn, raw_dir)
            if bridge_count(conn):
                raise SafeError("BRIDGE_NOT_EMPTY_STOP_FOR_PROVENANCE")
            prepared = read_bridge(conn)
            insert_bridge(conn, prepared)
            result = verify_post(conn, raw_dir, baseline=before)
            verify_sources(raw_dir, json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8")))
            phase = "COMMIT_REQUESTED"
        return {"transaction": "COMMITTED", "before": before, **result}
    except SafeError as exc:
        exc.details.update(transaction="ROLLED_BACK")
        raise
    except Exception as exc:
        error = SafeError("DATABASE_OR_LOCAL_BRIDGE_ERROR")
        error.details = {"transaction": "COMMIT_OUTCOME_UNVERIFIED" if phase == "COMMIT_REQUESTED" else "NOT_COMMITTED_OR_CONNECTION_UNVERIFIED",
                         "sqlstate": getattr(exc, "pgcode", None)}
        raise error from None
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preflight", "load", "verify"])
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    args = parser.parse_args()
    run = uuid.uuid4().hex
    start = time.monotonic()
    report = {"step": "6B_" + args.action.upper(), "run_id": run,
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "database": TARGET_DB,
              "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "code_sha256": sha256(Path(__file__)), "code_state": "WORKING_TREE_HASH_AT_RUN",
              "dimension_helper_sha256": sha256(ROOT / "etl/s06a_dimensions.py"),
              "staging_helper_sha256": sha256(ROOT / "etl/s05_staging.py"), "personal_rows_in_report": False}
    try:
        c = config(args.env_file)
        if args.action == "preflight":
            result = preflight(c, args.raw_dir)
        elif args.action == "load":
            result = load_bridge(c, args.raw_dir)
        else:
            conn = connect(c)
            try:
                conn.set_session(readonly=True, isolation_level="REPEATABLE READ")
                with conn:
                    result = {"readonly": True, **verify_post(conn, args.raw_dir)}
            finally:
                conn.close()
        report.update(status="PASS", result=result)
    except Exception as exc:
        report.update(status="FAIL", error_category=exc.code if isinstance(exc, SafeError) else "LOCAL_OR_CONNECTION_ERROR")
        if isinstance(exc, SafeError):
            report.update(exc.details)
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    path = ROOT / "results/warehouse" / ("s06b_" + args.action + "_" + run + ".json")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "run_id": run, "report": str(path.relative_to(ROOT)),
                      "error_category": report.get("error_category")}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
