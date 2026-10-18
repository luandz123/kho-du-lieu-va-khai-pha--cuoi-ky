"""Real PostgreSQL fixture test, isolated schema; no production writes."""
import argparse
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from etl.s05_staging import SafeError, config, connect, sha256, target_counts
from etl.s06b_bridge import RAW, bridge_count, insert_bridge, prepare_bridge, preserved_state, verify_bridge


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    run = uuid.uuid4().hex
    schema = "s06b_test_" + run[:12]
    ns = sql.Identifier(schema)
    report = {"step": "6B_FIXTURE", "run_id": run, "status": "FAIL", "fixture": "INVENTED_ONLY", "schema": schema,
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "code_sha256": sha256(ROOT / "etl/s06b_bridge.py"), "test_code_sha256": sha256(Path(__file__))}
    start, created, conn = time.monotonic(), False, None
    movies = [(1, "701", 'Éxample, "fixture"', "Drama|Comedy"), (2, "702", "Second", "Drama")]
    mm, gm = [(701, 9001), (702, 9011)], [("Comedy", 57), ("Drama", 63)]
    allowed = {"Comedy", "Drama"}
    try:
        conn = connect(config(args.env_file))
        with conn:
            before = preserved_state(conn, RAW)
            counts_before = target_counts(conn)
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(ns))
                cur.execute(sql.SQL("CREATE TABLE {}.dim_movie (movie_id integer UNIQUE NOT NULL,movie_key integer PRIMARY KEY)").format(ns))
                cur.execute(sql.SQL("CREATE TABLE {}.dim_genre (genre_name text UNIQUE NOT NULL,genre_key integer PRIMARY KEY)").format(ns))
                cur.execute(sql.SQL("CREATE TABLE {s}.bridge_movie_genre (movie_key integer NOT NULL REFERENCES {s}.dim_movie(movie_key),genre_key integer NOT NULL REFERENCES {s}.dim_genre(genre_key),PRIMARY KEY(movie_key,genre_key))").format(s=ns))
                for mid, key in mm:
                    cur.execute(sql.SQL("INSERT INTO {}.dim_movie VALUES (%s,%s)").format(ns), (mid, key))
                for genre, key in gm:
                    cur.execute(sql.SQL("INSERT INTO {}.dim_genre VALUES (%s,%s)").format(ns), (genre, key))
        created = True
        rejected = []
        for source, movie_map, genre_map, expected in [
                (movies, mm[:1], gm, "MISSING_MOVIE_MAPPING"),
                (movies, mm, gm[:1], "MISSING_GENRE_MAPPING"),
                ([(1, "701", "Duplicate", "Drama|Drama")], mm, gm, "DUPLICATE_SOURCE_MOVIE_GENRE")]:
            try:
                with conn:
                    prepare_bridge(source, movie_map, genre_map, allowed)
            except SafeError as exc:
                if exc.code != expected:
                    raise
                rejected.append(expected)
            else:
                raise SafeError("INVALID_FIXTURE_SOURCE_NOT_REJECTED")
        prepared = prepare_bridge(movies, mm, gm, allowed)
        rollbacks = []
        for fault, state in [("foreign_key", "23503"), ("duplicate_pair", "23505")]:
            inserted_before_error = 0
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT pg_advisory_xact_lock(20261027,1)")
                    insert_bridge(conn, prepared, schema)
                    inserted_before_error = bridge_count(conn, schema)
                    with conn.cursor() as cur:
                        pair = (9001, 999999) if fault == "foreign_key" else prepared["mapped"][0]
                        cur.execute(sql.SQL("INSERT INTO {}.bridge_movie_genre VALUES (%s,%s)").format(ns), pair)
            except psycopg2.Error as exc:
                if exc.pgcode != state:
                    raise
            else:
                raise SafeError("FIXTURE_DATABASE_ERROR_DID_NOT_OCCUR")
            with conn:
                remaining = bridge_count(conn, schema)
            if inserted_before_error != 3 or remaining != 0:
                raise SafeError("BRIDGE_TRANSACTION_ROLLBACK_NOT_PROVEN")
            rollbacks.append({"fault": fault, "sqlstate": state, "inserted_before_error": 3, "after_rollback": 0})
        with conn:
            insert_bridge(conn, prepared, schema)
            valid = verify_bridge(conn, prepared, schema)
            with conn.cursor() as cur:
                cur.execute(sql.SQL("SELECT movie_id,movie_key FROM {}.dim_movie ORDER BY movie_id").format(ns))
                if cur.fetchall() != mm:
                    raise SafeError("MULTIGENRE_CHANGED_DIM_MOVIE")
                cur.execute(sql.SQL("SELECT genre_name,genre_key FROM {}.dim_genre ORDER BY genre_name").format(ns))
                if cur.fetchall() != gm:
                    raise SafeError("BRIDGE_CHANGED_DIM_GENRE")
        # The unchanged S05 catalog guard rejects ANY extra base tables. Remove
        # only our fixture before invoking that strict production catalog check.
        with conn:
            with conn.cursor() as cur:
                for table in ["bridge_movie_genre", "dim_genre", "dim_movie"]:
                    cur.execute(sql.SQL("DROP TABLE {}.{}").format(ns, sql.Identifier(table)))
                cur.execute(sql.SQL("DROP SCHEMA {}").format(ns))
        created = False
        report["fixture_schema_removed"] = True
        with conn:
            if preserved_state(conn, RAW) != before or target_counts(conn) != counts_before:
                raise SafeError("PRODUCTION_CHANGED_DURING_BRIDGE_FIXTURE")
        report.update(status="PASS", mapping_and_source_rejections=rejected, rollback_cases=rollbacks,
                      valid_multigenre_fixture=valid, fixture_dim_movie_rows_before=2, fixture_dim_movie_rows_after=2,
                      fixture_surrogates_differ_from_source_ids=True, production_staging_and_dimensions_unchanged=True,
                      production_target_counts_unchanged=True)
    except Exception as exc:
        report.update(error_category=exc.code if isinstance(exc, SafeError) else "FIXTURE_DATABASE_OR_LOCAL_ERROR", sqlstate=getattr(exc, "pgcode", None))
        if conn:
            conn.rollback()
    finally:
        if conn and created:
            try:
                with conn:
                    with conn.cursor() as cur:
                        for table in ["bridge_movie_genre", "dim_genre", "dim_movie"]:
                            cur.execute(sql.SQL("DROP TABLE {}.{}").format(ns, sql.Identifier(table)))
                        cur.execute(sql.SQL("DROP SCHEMA {}").format(ns))
                report["fixture_schema_removed"] = True
            except Exception:
                report.update(status="FAIL", error_category="FIXTURE_CLEANUP_REQUIRED", fixture_schema_removed=False)
        if conn:
            conn.close()
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    path = ROOT / "results/warehouse" / ("s06b_fixture_" + run + ".json")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "report": str(path.relative_to(ROOT)), "error_category": report.get("error_category")}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
