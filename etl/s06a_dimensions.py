"""6A only: validate S05 snapshot, insert four empty dimensions atomically.

No bootstrap, truncate, delete, upsert, bridge/fact/analytics load, or full refresh.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import subprocess
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

from etl.s05_staging import (ROOT, TARGET_DB, SafeError, assert_project, catalog,
                            config, connect, sha256, target_counts,
                            verify_sources, verify_staging)

DIM_COLUMNS = {
    "dim_user": ("user_id", "gender", "age_group", "occupation"),
    "dim_movie": ("movie_id", "title", "release_year"),
    "dim_genre": ("genre_name",),
    "dim_date": ("full_date",),
}
KEYS = {"dim_user": "user_key", "dim_movie": "movie_key", "dim_genre": "genre_key", "dim_date": "date_key"}
S05_SNAPSHOT = ROOT / "results/warehouse/s05_load_f5f11bcd42314042b34bfa1ff66e1f56.json"


def integer(value, lower, upper, label):
    if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]+", value):
        raise SafeError("INVALID_INTEGER_" + label)
    parsed = int(value)
    if not lower <= parsed <= upper:
        raise SafeError("OUT_OF_RANGE_" + label)
    return parsed


def utc_instant(seconds):
    try:
        return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    except (OverflowError, ValueError):
        raise SafeError("TIMESTAMP_OUTSIDE_SUPPORTED_DATE_RANGE") from None


def prepare_dimensions(users, movies, minimum, maximum, contract, codes):
    """Pure transform from retained raw fields; no DB/data mutation or logging."""
    user_rows, movie_rows, genres = [], [], set()
    user_ids, movie_ids = set(), set()
    occupation_codes = {int(k) for k in codes["occupations"]}
    allowed_genres = set(codes["genres"])
    for _, raw_id, gender, age, occupation in users:
        uid = integer(raw_id, 1, 2**31 - 1, "USER_ID")
        age_code = integer(age, 1, 56, "AGE")
        occ = integer(occupation, 0, 32767, "OCCUPATION")
        if uid in user_ids:
            raise SafeError("DUPLICATE_USER_ID")
        if gender not in contract["gender"] or str(age_code) not in contract["age_labels"] or occ not in occupation_codes:
            raise SafeError("USER_CODE_NOT_IN_CONTRACT")
        user_ids.add(uid)
        user_rows.append((uid, gender, contract["age_labels"][str(age_code)], occ))
    for _, raw_id, title, raw_genres in movies:
        mid = integer(raw_id, 1, 2**31 - 1, "MOVIE_ID")
        if mid in movie_ids:
            raise SafeError("DUPLICATE_MOVIE_ID")
        if not isinstance(title, str) or not title or not isinstance(raw_genres, str):
            raise SafeError("NULL_OR_EMPTY_MOVIE_FIELD")
        parts = raw_genres.split("|")
        if len(parts) != len(set(parts)):
            raise SafeError("DUPLICATE_GENRE_WITHIN_MOVIE")
        if any(g not in allowed_genres for g in parts):
            raise SafeError("GENRE_NOT_IN_MANIFEST")
        match = re.search(r"\(([0-9]{4})\)$", title)
        year = int(match[1]) if match else None
        movie_ids.add(mid)
        movie_rows.append((mid, title, year))
        genres.update(parts)  # Natural grain of dim_genre, not dedup of source movies.
    lo = integer(str(minimum), -(2**63), 2**63 - 1, "TIMESTAMP")
    hi = integer(str(maximum), -(2**63), 2**63 - 1, "TIMESTAMP")
    if lo > hi:
        raise SafeError("INVALID_TIMESTAMP_BOUNDS")
    start, end = utc_instant(lo), utc_instant(hi)
    days = (end.date() - start.date()).days + 1
    return {
        "rows": {"dim_user": sorted(user_rows), "dim_movie": sorted(movie_rows),
                 "dim_genre": [(g,) for g in sorted(genres)],
                 "dim_date": [(start.date() + timedelta(days=i),) for i in range(days)]},
        "utc": {"min_timestamp": lo, "max_timestamp": hi,
                "min_rated_at": start.isoformat().replace("+00:00", "Z"),
                "max_rated_at": end.isoformat().replace("+00:00", "Z"),
                "first_date": start.date().isoformat(), "last_date": end.date().isoformat(), "inclusive_days": days},
    }


def dimension_counts(conn, schema="dw"):
    result = {}
    with conn.cursor() as cur:
        for table in DIM_COLUMNS:
            cur.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table)))
            result[table] = cur.fetchone()[0]
    return result


def insert_dimensions(conn, prepared, schema="dw", progress=None):
    if schema != "dw" and not re.fullmatch(r"s06[ad]_test_[0-9a-f]{12}", schema):
        raise SafeError("INVALID_DIMENSION_NAMESPACE")
    if any(dimension_counts(conn, schema).values()):
        raise SafeError("DIMENSIONS_NOT_EMPTY_STOP_FOR_PROVENANCE")
    with conn.cursor() as cur:
        for table, columns in DIM_COLUMNS.items():
            command = sql.SQL("INSERT INTO {}.{} ({}) VALUES %s").format(
                sql.Identifier(schema), sql.Identifier(table), sql.SQL(",").join(map(sql.Identifier, columns)))
            execute_values(cur, command.as_string(conn), prepared["rows"][table], page_size=1000)
            if progress is not None:
                progress[table] = len(prepared["rows"][table])


def verify_dimensions(conn, prepared, schema="dw"):
    result = {}
    with conn.cursor() as cur:
        for table, columns in DIM_COLUMNS.items():
            command = sql.SQL("SELECT {} FROM {}.{} ORDER BY {}").format(
                sql.SQL(",").join(map(sql.Identifier, columns)), sql.Identifier(schema),
                sql.Identifier(table), sql.Identifier(columns[0]))
            cur.execute(command)
            actual = cur.fetchall()
            if actual != prepared["rows"][table]:
                raise SafeError("DIMENSION_FIELD_MISMATCH", file=table)
            key = sql.Identifier(KEYS[table])
            cur.execute(sql.SQL("SELECT count(*),count(DISTINCT {}),count(*) FILTER (WHERE {}>0) FROM {}.{}").format(
                key, key, sql.Identifier(schema), sql.Identifier(table)))
            total, unique, positive = cur.fetchone()
            if total != unique or total != positive:
                raise SafeError("INVALID_SURROGATE_KEY", file=table)
            result[table] = {"rows": total, "all_logical_fields_exact": True, "surrogate_unique_positive": True}
        cur.execute(sql.SQL("SELECT full_date,calendar_year,quarter_number,month_number,day_of_month FROM {}.dim_date ORDER BY full_date").format(sql.Identifier(schema)))
        dates = cur.fetchall()
        expected = [(d, d.year, (d.month - 1) // 3 + 1, d.month, d.day) for (d,) in prepared["rows"]["dim_date"]]
        if dates != expected:
            raise SafeError("GENERATED_DATE_COLUMNS_OR_CONTINUITY_MISMATCH")
        result["dim_date"].update(generated_calendar_columns_exact=True, no_missing_or_duplicate_dates=True, **prepared["utc"])
    return result


def snapshot_check(conn, raw_dir):
    source = json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8"))
    hashes = verify_sources(raw_dir, source)
    actual = verify_staging(conn, raw_dir)
    expected = json.loads(S05_SNAPSHOT.read_text(encoding="utf-8"))["result"]["staging"]
    if actual != expected:
        raise SafeError("STAGING_NOT_APPROVED_S05_SNAPSHOT")
    return {"source": hashes, "staging": actual, "snapshot_run_id": "f5f11bcd42314042b34bfa1ff66e1f56"}


def read_prepared(conn):
    contract = json.loads((ROOT / "docs/shared/data_contract.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))
    with conn.cursor() as cur:
        cur.execute("SELECT source_line,user_id_raw,gender_raw,age_code_raw,occupation_raw FROM staging.users_raw ORDER BY source_line")
        users = cur.fetchall()
        cur.execute("SELECT source_line,movie_id_raw,title_raw,genres_raw FROM staging.movies_raw ORDER BY source_line")
        movies = cur.fetchall()
        cur.execute("SELECT count(*) FROM staging.ratings_raw WHERE timestamp_raw IS NULL OR timestamp_raw !~ '^-?[0-9]+$'")
        if cur.fetchone()[0]:
            raise SafeError("INVALID_STAGING_TIMESTAMP")
        cur.execute("SELECT min(timestamp_raw::numeric)::text,max(timestamp_raw::numeric)::text FROM staging.ratings_raw")
        minimum, maximum = cur.fetchone()
    prepared = prepare_dimensions(users, movies, minimum, maximum, contract, manifest["source_code_sets"])
    if len(prepared["rows"]["dim_user"]) != manifest["row_counts"]["users"] or len(prepared["rows"]["dim_movie"]) != manifest["row_counts"]["movies"]:
        raise SafeError("DIMENSION_SOURCE_COUNT_MISMATCH")
    codes = manifest["source_code_sets"]
    rows = prepared["rows"]["dim_user"]
    if {r[1] for r in rows} != set(codes["gender"]) or {r[2] for r in rows} != set(codes["age_groups"].values()) or {r[3] for r in rows} != {int(k) for k in codes["occupations"]}:
        raise SafeError("OBSERVED_USER_CODE_SET_MISMATCH")
    if {g for (g,) in prepared["rows"]["dim_genre"]} != set(codes["genres"]):
        raise SafeError("OBSERVED_GENRE_SET_MISMATCH")
    return prepared


def canonical_dimension_frame(table, columns, rows):
    """The reviewed serializer does not sort; callers must supply contract order."""
    frame = pd.DataFrame(rows, columns=columns)
    if table == "movies":
        frame["release_year"] = frame["release_year"].astype("Int64")
    key = {"users": "user_id", "movies": "movie_id"}[table]
    return frame.sort_values(key, kind="stable").reset_index(drop=True)


def verify_two_view_hashes(conn):
    adapter_path = ROOT / "mining/data_io.py"
    blob = subprocess.check_output(["git", "show", "HEAD:mining/data_io.py"], cwd=ROOT)
    reviewed = json.loads((ROOT / "docs/P1/s04_inputs_pr5.json").read_text(encoding="utf-8"))
    if adapter_path.read_bytes().replace(b"\r\n", b"\n") != blob or hashlib.sha256(blob).hexdigest() != reviewed["script_provenance_checks"]["mining/data_io.py"]["actual"]:
        raise SafeError("SERIALIZER_NOT_REVIEWED_VERSION")
    adapter = importlib.import_module("mining.data_io")
    manifest = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))
    result = {}
    with conn.cursor() as cur:
        for table in ("users", "movies"):
            key = {"users": "user_id", "movies": "movie_id"}[table]
            cur.execute("SELECT * FROM dw.v_ml_" + table + " ORDER BY " + key)
            frame = canonical_dimension_frame(table, [c.name for c in cur.description], cur.fetchall())
            actual = adapter.compute_canonical_hash(table, frame)
            if actual != manifest["canonical_hashes"][table] or len(frame) != manifest["row_counts"][table]:
                raise SafeError("DIMENSION_CANONICAL_VIEW_MISMATCH", file=table)
            result[table] = {"rows": len(frame), "sha256": actual, "canonical_hash_matches": True}
    return {"views": result, "serializer_git_blob_sha256": hashlib.sha256(blob).hexdigest(), "g2_complete": False}


def load_dimensions(c, raw_dir):
    conn = connect(c)
    progress = {}
    phase = "PRE_COMMIT"
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(20261027,1)")
                cur.execute("LOCK TABLE staging.users_raw,staging.movies_raw,staging.ratings_raw IN SHARE MODE")
                cur.execute("LOCK TABLE dw.dim_user,dw.dim_movie,dw.dim_genre,dw.dim_date,dw.bridge_movie_genre,dw.fact_rating,analytics.model_registry,analytics.user_cluster,analytics.cluster_genre_profile IN SHARE ROW EXCLUSIVE MODE")
            assert_project(conn)
            actual_catalog = catalog(conn)
            before = target_counts(conn)
            if any(before.values()):
                raise SafeError("TARGETS_NOT_EMPTY_STOP_FOR_PROVENANCE")
            snapshot = snapshot_check(conn, raw_dir)
            prepared = read_prepared(conn)
            insert_dimensions(conn, prepared, progress=progress)
            verified = verify_dimensions(conn, prepared)
            hashes = verify_two_view_hashes(conn)
            after = target_counts(conn)
            not_loaded = {k: v for k, v in after.items() if k not in {"dw." + d for d in DIM_COLUMNS}}
            if any(not_loaded.values()):
                raise SafeError("OUTSIDE_6A_TARGET_CHANGED")
            with conn.cursor() as cur:
                cur.execute("SELECT (SELECT count(*) FROM dw.v_ml_movie_genres),(SELECT count(*) FROM dw.v_ml_ratings)")
                if cur.fetchone() != (0, 0):
                    raise SafeError("BRIDGE_FACT_VIEWS_NOT_EMPTY")
            # End-of-run source guard; staging stayed SHARE-locked throughout.
            verify_sources(raw_dir, json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8")))
            phase = "COMMIT_REQUESTED"
        return {"transaction": "COMMITTED", "catalog_matches": actual_catalog["columns_match"] and actual_catalog["keys_match"],
                "s05_snapshot": snapshot, "dimensions": verified, "canonical_two_views": hashes,
                "genre_set_matches_manifest_and_source": True, "unloaded_target_counts": not_loaded,
                "empty_views": {"dw.v_ml_movie_genres": 0, "dw.v_ml_ratings": 0}, "inserted": progress}
    except SafeError as exc:
        exc.details.update(transaction="ROLLED_BACK", insert_attempts=progress)
        raise
    except Exception as exc:
        error = SafeError("DATABASE_OR_LOCAL_LOAD_ERROR")
        error.details = {"transaction": "COMMIT_OUTCOME_UNVERIFIED" if phase == "COMMIT_REQUESTED" else "NOT_COMMITTED_OR_CONNECTION_UNVERIFIED",
                         "insert_attempts": progress, "sqlstate": getattr(exc, "pgcode", None)}
        raise error from None
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/p1_s05/ml-1m")
    args = parser.parse_args()
    run_id = uuid.uuid4().hex
    start = time.monotonic()
    report = {"step": "6A", "run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "database": TARGET_DB, "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "code_state": "WORKING_TREE_HASH_AT_RUN", "code_sha256": sha256(Path(__file__)),
              "s05_helper_sha256": sha256(ROOT / "etl/s05_staging.py"), "personal_data_rows_in_report": False}
    exit_code = 0
    try:
        report["result"] = load_dimensions(config(args.env_file), args.raw_dir)
        report["status"] = "PASS"
    except Exception as exc:
        report.update(status="FAIL", error_category=exc.code if isinstance(exc, SafeError) else "LOCAL_OR_CONNECTION_ERROR",
                      sqlstate=getattr(exc, "pgcode", None), logical_table=getattr(exc, "file", None))
        if isinstance(exc, SafeError):
            report.update(exc.details)
        exit_code = 2
    report.update(duration_seconds=round(time.monotonic() - start, 3), exit_code=exit_code)
    path = ROOT / "results/warehouse" / ("s06a_load_" + run_id + ".json")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "run_id": run_id, "report": str(path.relative_to(ROOT)),
                      "duration_seconds": report["duration_seconds"], **({"error_category": report["error_category"]} if exit_code else {})}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
