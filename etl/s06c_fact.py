"""6C only: load source ratings into the empty fact; no integrated refresh."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import subprocess
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from itertools import islice, zip_longest
from pathlib import Path

import pandas as pd
from psycopg2 import sql
from psycopg2.extras import execute_values

from etl.s05_staging import ROOT, TARGET_DB, SafeError, assert_project, catalog, config, connect, sha256, verify_sources
from etl.s06a_dimensions import integer, read_prepared, snapshot_check, utc_instant, verify_dimensions, verify_two_view_hashes
from etl.s06b_bridge import RAW, dimension_fingerprints, read_bridge, unique_map, verify_bridge, verify_bridge_view

COLUMNS = ["user_id", "movie_id", "rating", "timestamp", "rated_at"]
EXPECTED_HASH = "06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf"


def namespace(schema):
    if schema != "dw" and not re.fullmatch(r"s06c_test_[0-9a-f]{12}", schema):
        raise SafeError("INVALID_FACT_NAMESPACE")
    return sql.Identifier(schema)


def mappings(user_rows, movie_rows, date_rows):
    return {"user": unique_map(user_rows, "USER"), "movie": unique_map(movie_rows, "MOVIE"),
            "date": unique_map(date_rows, "DATE")}


def read_mappings(conn, schema="dw"):
    ns = namespace(schema)
    result = []
    with conn.cursor() as cur:
        for table, natural, key in [("dim_user", "user_id", "user_key"), ("dim_movie", "movie_id", "movie_key"), ("dim_date", "full_date", "date_key")]:
            cur.execute(sql.SQL("SELECT {},{} FROM {}.{}").format(sql.Identifier(natural), sql.Identifier(key), ns, sql.Identifier(table)))
            result.append(cur.fetchall())
    return mappings(*result)


def parse_rating(row):
    _line, u, m, r, ts = row
    uid = integer(u, 1, 2**31 - 1, "USER_ID")
    mid = integer(m, 1, 2**31 - 1, "MOVIE_ID")
    rating = integer(r, 1, 5, "RATING")
    seconds = integer(ts, -(2**63), 2**63 - 1, "TIMESTAMP")
    instant = utc_instant(seconds)
    return uid, mid, rating, seconds, instant


def mapped_rating(row, maps):
    uid, mid, rating, seconds, instant = parse_rating(row)
    for kind, natural in [("user", uid), ("movie", mid), ("date", instant.date())]:
        if natural not in maps[kind]:
            raise SafeError("MISSING_" + kind.upper() + "_MAPPING")
    return (maps["user"][uid], maps["movie"][mid], maps["date"][instant.date()], rating, seconds, instant)


def mapped_rows(rows, maps):
    seen = set()
    for row in rows:
        value = mapped_rating(row, maps)
        pair = value[:2]
        if pair in seen:
            raise SafeError("DUPLICATE_SOURCE_USER_MOVIE")
        seen.add(pair)
        yield value


def source_rows(conn, *, canonical_order=False):
    name = "s06c_source_" + uuid.uuid4().hex
    with conn.cursor(name=name) as cur:
        cur.itersize = 10000
        order = "user_id_raw::integer,movie_id_raw::integer,timestamp_raw::bigint,rating_raw::integer" if canonical_order else "source_line"
        cur.execute("SELECT source_line,user_id_raw,movie_id_raw,rating_raw,timestamp_raw FROM staging.ratings_raw ORDER BY " + order)
        yield from cur


def fact_count(conn, schema="dw"):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT count(*) FROM {}.fact_rating").format(namespace(schema)))
        return cur.fetchone()[0]


def insert_fact(conn, rows, maps, schema="dw", progress=None):
    ns = namespace(schema)
    if fact_count(conn, schema):
        raise SafeError("FACT_NOT_EMPTY_STOP_FOR_PROVENANCE")
    iterator = iter(mapped_rows(rows, maps))
    total = 0
    with conn.cursor() as cur:
        command = sql.SQL("INSERT INTO {}.fact_rating (user_key,movie_key,date_key,rating,rating_timestamp,rated_at) VALUES %s").format(ns).as_string(conn)
        while batch := list(islice(iterator, 1000)):
            execute_values(cur, command, batch, page_size=1000)
            total += len(batch)
            if progress is not None:
                progress["inserted_rows"] = total
    if total == 0:
        raise SafeError("EMPTY_SOURCE_RATINGS")
    return total


def preserved_state(conn, raw_dir):
    assert_project(conn)
    cat = catalog(conn)
    snapshot = snapshot_check(conn, raw_dir)
    dims = verify_dimensions(conn, read_prepared(conn))
    hashes = verify_two_view_hashes(conn)
    prepared_bridge = read_bridge(conn)
    bridge = verify_bridge(conn, prepared_bridge)
    bridge_view = verify_bridge_view(conn, prepared_bridge)
    fingerprints = dimension_fingerprints(conn)
    accepted = json.loads((ROOT / "results/warehouse/s06b_load_691f5ae7935d43988ca05254cd5ba5f1.json").read_text(encoding="utf-8"))
    if fingerprints != accepted["result"]["before"]["dimension_fingerprints"]:
        raise SafeError("DIMENSION_SURROGATE_OR_FIELDS_CHANGED_SINCE_6B")
    with conn.cursor() as cur:
        cur.execute("SELECT movie_key,genre_key FROM dw.bridge_movie_genre ORDER BY movie_key,genre_key")
        physical = cur.fetchall()
        bridge_digest = hashlib.sha256(json.dumps(physical, separators=(",", ":")).encode("utf-8")).hexdigest()
        empty = {}
        for table in ["model_registry", "user_cluster", "cluster_genre_profile"]:
            cur.execute(sql.SQL("SELECT count(*) FROM analytics.{}").format(sql.Identifier(table)))
            empty["analytics." + table] = cur.fetchone()[0]
        if any(empty.values()):
            raise SafeError("ANALYTICS_NOT_EMPTY_STOP_FOR_PROVENANCE")
    return {"catalog_matches": cat["columns_match"] and cat["keys_match"], "s05_snapshot": snapshot,
            "dimensions": dims, "dimension_fingerprints": fingerprints, "canonical_users_movies": hashes,
            "bridge": bridge, "bridge_physical_sha256": bridge_digest, "canonical_movie_genres": bridge_view,
            "analytics_counts": empty}


def verify_integrity(conn, schema="dw"):
    ns = namespace(schema)
    with conn.cursor() as cur:
        cur.execute(sql.SQL("""SELECT count(*),count(DISTINCT (f.user_key,f.movie_key)),
            count(DISTINCT f.rating_key),count(*) FILTER (WHERE f.rating_key<=0),
            count(*) FILTER (WHERE u.user_key IS NULL OR m.movie_key IS NULL OR d.date_key IS NULL),
            count(*) FILTER (WHERE f.rating NOT BETWEEN 1 AND 5 OR f.rating IS NULL),
            count(*) FILTER (WHERE EXTRACT(EPOCH FROM f.rated_at) IS DISTINCT FROM f.rating_timestamp
                OR f.rated_date IS DISTINCT FROM (f.rated_at AT TIME ZONE 'UTC')::date
                OR d.full_date IS DISTINCT FROM f.rated_date)
            FROM {s}.fact_rating f LEFT JOIN {s}.dim_user u ON u.user_key=f.user_key
            LEFT JOIN {s}.dim_movie m ON m.movie_key=f.movie_key
            LEFT JOIN {s}.dim_date d ON d.date_key=f.date_key""").format(s=ns))
        total, pairs, keys, bad_keys, orphan, invalid, bad_time = cur.fetchone()
        if total != pairs or total != keys or any([bad_keys, orphan, invalid, bad_time]):
            raise SafeError("FACT_KEYS_RATING_OR_UTC_MISMATCH")
    return {"rows": total, "duplicate_user_movie_pairs": total - pairs, "orphan_fks": orphan,
            "invalid_rating": invalid, "timestamp_rated_at_date_mismatches": bad_time,
            "surrogate_keys_unique_positive": True}


class CanonicalDigest:
    """Use the reviewed serializer per ordered chunk; emit a single CSV header."""
    def __init__(self):
        self.digest = hashlib.sha256()
        self.first = True

    def update(self, rows):
        frame = pd.DataFrame(rows, columns=COLUMNS)
        data = importlib.import_module("mining.data_io").serialize_df_to_canonical_csv_bytes("ratings", frame)
        if not self.first:
            data = data.split(b"\n", 1)[1]
        self.digest.update(data)
        self.first = False

    def hexdigest(self):
        if self.first:
            self.update([])
        return self.digest.hexdigest()


def verify_ratings(conn):
    integrity = verify_integrity(conn)
    totals, stars, users, movies = 0, Counter(), set(), set()
    low, high = None, None
    expected_digest, actual_digest = CanonicalDigest(), CanonicalDigest()
    source = source_rows(conn, canonical_order=True)
    count = 0
    with conn.cursor(name="s06c_view_" + uuid.uuid4().hex) as cur:
        cur.itersize = 10000
        cur.execute('SELECT * FROM dw.v_ml_ratings ORDER BY user_id,movie_id,"timestamp",rating')
        # Named cursors expose description only after the first fetch.
        actual_batch = cur.fetchmany(10000)
        if [c.name for c in cur.description] != COLUMNS:
            raise SafeError("RATINGS_VIEW_SCHEMA_MISMATCH")
        while actual_batch:
            expected_batch = []
            for _ in actual_batch:
                raw = next(source, None)
                if raw is None:
                    raise SafeError("RATINGS_VIEW_EXTRA_ROWS")
                uid, mid, rating, seconds, instant = parse_rating(raw)
                expected_batch.append((uid, mid, rating, seconds, instant.strftime("%Y-%m-%dT%H:%M:%SZ")))
                totals += rating
                stars[rating] += 1
                users.add(uid)
                movies.add(mid)
                low = seconds if low is None else min(low, seconds)
                high = seconds if high is None else max(high, seconds)
            if actual_batch != expected_batch:
                raise SafeError("RATINGS_VIEW_ALL_FIELDS_SOURCE_MISMATCH")
            count += len(actual_batch)
            expected_digest.update(expected_batch)
            actual_digest.update(actual_batch)
            actual_batch = cur.fetchmany(10000)
    if next(source, None) is not None:
        source.close()
        raise SafeError("RATINGS_VIEW_MISSING_SOURCE_ROWS")
    source.close()
    actual_hash, expected_hash = actual_digest.hexdigest(), expected_digest.hexdigest()
    manifest = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))
    if count != integrity["rows"] or count != manifest["row_counts"]["ratings"] or actual_hash != expected_hash or actual_hash != EXPECTED_HASH or actual_hash != manifest["canonical_hashes"]["ratings"]:
        raise SafeError("RATINGS_CANONICAL_COUNT_OR_HASH_MISMATCH")
    with conn.cursor() as cur:
        cur.execute("SELECT count(*),sum(rating),count(DISTINCT user_key),count(DISTINCT movie_key),min(rating_timestamp),max(rating_timestamp) FROM dw.fact_rating")
        if cur.fetchone() != (count, totals, len(users), len(movies), low, high):
            raise SafeError("FACT_AGGREGATES_DIFFER_FROM_SOURCE")
        cur.execute("SELECT rating,count(*) FROM dw.fact_rating GROUP BY rating ORDER BY rating")
        if dict(cur.fetchall()) != dict(stars):
            raise SafeError("FACT_STAR_DISTRIBUTION_DIFFERS_FROM_SOURCE")
    return {**integrity, "view_rows": count, "all_logical_fields_match_source": True, "rating_sum": totals,
            "star_counts": dict(sorted(stars.items())), "users_with_ratings": len(users), "movies_with_ratings": len(movies),
            "min_timestamp": low, "max_timestamp": high, "min_rated_at_utc": utc_instant(low).isoformat().replace("+00:00", "Z"),
            "max_rated_at_utc": utc_instant(high).isoformat().replace("+00:00", "Z"),
            "canonical_sha256": actual_hash, "source_canonical_sha256": expected_hash, "canonical_hash_matches": True}


def preflight(c, raw_dir):
    conn = connect(c)
    try:
        conn.set_session(readonly=True, isolation_level="REPEATABLE READ")
        with conn:
            before = preserved_state(conn, raw_dir)
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM dw.v_ml_ratings")
                view_count = cur.fetchone()[0]
            if fact_count(conn) or view_count:
                raise SafeError("FACT_OR_VIEW_NOT_EMPTY_STOP_FOR_PROVENANCE")
            return {"readonly": True, "preserved": before, "fact_rows": 0, "ratings_view_rows": 0}
    finally:
        conn.close()


def verify_post(conn, raw_dir, baseline=None):
    preserved = preserved_state(conn, raw_dir)
    if baseline is None:
        matches = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "results/warehouse").glob("s06c_load_*.json")]
        matches = [d for d in matches if d.get("status") == "PASS" and d.get("result", {}).get("transaction") == "COMMITTED"]
        if len(matches) != 1:
            raise SafeError("UNAMBIGUOUS_6C_BASELINE_REQUIRED")
        baseline = matches[0]["result"]["before"]
    if preserved != baseline:
        raise SafeError("STAGING_DIMENSION_OR_BRIDGE_CHANGED")
    fact = verify_ratings(conn)
    four = {k: v["sha256"] for k, v in preserved["canonical_users_movies"]["views"].items()}
    four.update(movie_genres=preserved["canonical_movie_genres"]["sha256"], ratings=fact["canonical_sha256"])
    return {"preserved": preserved, "fact": fact, "four_canonical_hashes": four,
            "staging_dimensions_surrogates_bridge_unchanged": True, "g2_complete": False, "full_refresh_complete": False}


def load_fact(c, raw_dir):
    conn = connect(c)
    phase, progress = "PRE_COMMIT", {}
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(20261027,1)")
                cur.execute("LOCK TABLE staging.users_raw,staging.movies_raw,staging.ratings_raw IN SHARE MODE")
                cur.execute("LOCK TABLE dw.dim_user,dw.dim_movie,dw.dim_genre,dw.dim_date,dw.bridge_movie_genre,dw.fact_rating,analytics.model_registry,analytics.user_cluster,analytics.cluster_genre_profile IN SHARE ROW EXCLUSIVE MODE")
            before = preserved_state(conn, raw_dir)
            insert_fact(conn, source_rows(conn), read_mappings(conn), progress=progress)
            checked = verify_post(conn, raw_dir, baseline=before)
            verify_sources(raw_dir, json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8")))
            phase = "COMMIT_REQUESTED"
        return {"transaction": "COMMITTED", "inserted_rows": progress["inserted_rows"], "before": before, **checked}
    except SafeError as exc:
        exc.details.update(transaction="ROLLED_BACK", insert_attempts=progress)
        raise
    except Exception as exc:
        error = SafeError("FACT_DATABASE_OR_LOCAL_ERROR")
        error.details = {"transaction": "COMMIT_OUTCOME_UNVERIFIED" if phase == "COMMIT_REQUESTED" else "NOT_COMMITTED_OR_CONNECTION_UNVERIFIED",
                         "insert_attempts": progress, "sqlstate": getattr(exc, "pgcode", None)}
        raise error from None
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preflight", "load", "verify"])
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    args = parser.parse_args()
    run, start = uuid.uuid4().hex, time.monotonic()
    report = {"step": "6C_" + args.action.upper(), "run_id": run, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "database": TARGET_DB, "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "code_state": "WORKING_TREE_HASH_AT_RUN", "code_sha256": sha256(Path(__file__)), "personal_rows_in_report": False,
              "helper_sha256": {p: sha256(ROOT / p) for p in ["etl/s05_staging.py", "etl/s06a_dimensions.py", "etl/s06b_bridge.py"]}}
    try:
        c = config(args.env_file)
        if args.action == "preflight":
            result = preflight(c, args.raw_dir)
        elif args.action == "load":
            result = load_fact(c, args.raw_dir)
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
    path = ROOT / "results/warehouse" / ("s06c_" + args.action + "_" + run + ".json")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "run_id": run, "report": str(path.relative_to(ROOT)), "error_category": report.get("error_category")}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
