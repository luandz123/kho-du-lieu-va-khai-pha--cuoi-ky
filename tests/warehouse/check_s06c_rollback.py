"""Fixture-only 6C integration: partial-insert rollback and explicit UTC mapping."""
import argparse
import json
import subprocess
import sys
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from etl.s05_staging import SafeError, config, connect, sha256
from etl.s06c_fact import RAW, fact_count, insert_fact, preserved_state, read_mappings, verify_integrity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    run = uuid.uuid4().hex
    schema = "s06c_test_" + run[:12]
    ns = sql.Identifier(schema)
    start, conn, created = time.monotonic(), None, False
    report = {"step": "6C_FIXTURE", "run_id": run, "status": "FAIL", "fixture": "INVENTED_ONLY", "schema": schema,
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "code_sha256": sha256(ROOT / "etl/s06c_fact.py"),
              "test_code_sha256": sha256(Path(__file__)),
              "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    rows = [(i, str(i), "701", str(1 + i % 5), "946684799" if i % 2 else "946684800") for i in range(1, 1001)]
    try:
        conn = connect(config(args.env_file))
        with conn:
            before = preserved_state(conn, RAW)
            fact_before = fact_count(conn)
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(ns))
                cur.execute(sql.SQL("CREATE TABLE {}.dim_user (user_id integer UNIQUE NOT NULL,user_key integer PRIMARY KEY)").format(ns))
                cur.execute(sql.SQL("CREATE TABLE {}.dim_movie (movie_id integer UNIQUE NOT NULL,movie_key integer PRIMARY KEY)").format(ns))
                cur.execute(sql.SQL("CREATE TABLE {}.dim_date (full_date date UNIQUE NOT NULL,date_key integer PRIMARY KEY,UNIQUE(date_key,full_date))").format(ns))
                cur.execute(sql.SQL("CREATE TABLE {}.bridge_movie_genre (movie_key integer,genre_name text,PRIMARY KEY(movie_key,genre_name))").format(ns))
                cur.execute(sql.SQL("CREATE TABLE {}.fact_rating (LIKE dw.fact_rating INCLUDING ALL)").format(ns))
                cur.execute(sql.SQL("ALTER TABLE {s}.fact_rating ADD FOREIGN KEY(user_key) REFERENCES {s}.dim_user(user_key), ADD FOREIGN KEY(movie_key) REFERENCES {s}.dim_movie(movie_key), ADD FOREIGN KEY(date_key,rated_date) REFERENCES {s}.dim_date(date_key,full_date)").format(s=ns))
                execute_values(cur, sql.SQL("INSERT INTO {}.dim_user VALUES %s").format(ns).as_string(conn), [(i, i + 9000) for i in range(1, 1002)])
                cur.execute(sql.SQL("INSERT INTO {}.dim_movie VALUES (701,8001)").format(ns))
                cur.execute(sql.SQL("INSERT INTO {}.dim_date VALUES ('1999-12-31',7001),('2000-01-01',7002)").format(ns))
                cur.execute(sql.SQL("INSERT INTO {}.bridge_movie_genre VALUES (8001,'Comedy'),(8001,'Drama')").format(ns))
            maps = read_mappings(conn, schema)
        created = True
        cases = []
        bad_rows = [
            ((1001, "999999", "701", "5", "946684800"), "MISSING_USER_MAPPING"),
            ((1001, "1001", "999999", "5", "946684800"), "MISSING_MOVIE_MAPPING"),
            ((1001, "1001", "701", "5", "946857600"), "MISSING_DATE_MAPPING"),
            ((1001, "1001", "701", "6", "946684800"), "OUT_OF_RANGE_RATING"),
            (rows[0], "DUPLICATE_SOURCE_USER_MOVIE"),
        ]
        for bad, expected in bad_rows:
            progress = {}
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT pg_advisory_xact_lock(20261027,1)")
                    insert_fact(conn, iter(rows + [bad]), maps, schema, progress)
            except SafeError as exc:
                if exc.code != expected:
                    raise
            else:
                raise SafeError("FIXTURE_INVALID_SOURCE_ACCEPTED")
            with conn:
                remaining = fact_count(conn, schema)
            if progress.get("inserted_rows") != 1000 or remaining != 0:
                raise SafeError("PARTIAL_FACT_ROLLBACK_NOT_PROVEN")
            cases.append({"fault": expected, "inserted_before_error": 1000, "after_rollback": 0})
        for kind, state in [("check", "23514"), ("unique", "23505")]:
            try:
                with conn:
                    insert_fact(conn, iter(rows), maps, schema)
                    with conn.cursor() as cur:
                        uid, rating = (10001, 6) if kind == "check" else (9001, 2)
                        cur.execute(sql.SQL("INSERT INTO {}.fact_rating (user_key,movie_key,date_key,rating,rating_timestamp,rated_at) VALUES (%s,8001,7002,%s,946684800,%s)").format(ns), (uid, rating, datetime(2000, 1, 1, tzinfo=timezone.utc)))
            except psycopg2.Error as exc:
                if exc.pgcode != state:
                    raise
            else:
                raise SafeError("FIXTURE_SQL_ERROR_DID_NOT_OCCUR")
            with conn:
                if fact_count(conn, schema) != 0:
                    raise SafeError("SQL_FAILURE_FACT_ROLLBACK_NOT_PROVEN")
            cases.append({"fault": kind, "sqlstate": state, "inserted_before_error": 1000, "after_rollback": 0})
        with conn:
            with conn.cursor() as cur:
                cur.execute("SET LOCAL TIME ZONE 'Asia/Bangkok'")
            insert_fact(conn, iter(rows), maps, schema)
            integrity = verify_integrity(conn, schema)
            with conn.cursor() as cur:
                cur.execute(sql.SQL("SELECT rated_date,count(*) FROM {}.fact_rating GROUP BY rated_date ORDER BY rated_date").format(ns))
                if cur.fetchall() != [(date(1999, 12, 31), 500), (date(2000, 1, 1), 500)]:
                    raise SafeError("FIXTURE_UTC_DAY_SPLIT_MISMATCH")
                cur.execute(sql.SQL("SELECT count(*) FROM {}.dim_movie").format(ns))
                if cur.fetchone()[0] != 1 or integrity["rows"] != 1000:
                    raise SafeError("MULTIGENRE_MULTIPLIED_FACT_OR_MOVIE")
        # Strict production catalog allows no extra tables; remove our fixture first.
        with conn:
            with conn.cursor() as cur:
                for table in ["fact_rating", "bridge_movie_genre", "dim_date", "dim_movie", "dim_user"]:
                    cur.execute(sql.SQL("DROP TABLE {}.{}").format(ns, sql.Identifier(table)))
                cur.execute(sql.SQL("DROP SCHEMA {}").format(ns))
        created = False
        report["fixture_schema_removed"] = True
        with conn:
            if preserved_state(conn, RAW) != before or fact_count(conn) != fact_before:
                raise SafeError("PRODUCTION_CHANGED_DURING_FIXTURE")
        report.update(status="PASS", rollback_cases=cases, valid_fixture=integrity,
                      fixture_session_timezone="Asia/Bangkok", utc_boundary_days_each_500=True,
                      one_movie_two_genres_source_ratings=1000, one_movie_two_genres_fact_rows=1000,
                      dim_movie_rows_unchanged=1, production_unchanged=True)
    except Exception as exc:
        report.update(error_category=exc.code if isinstance(exc, SafeError) else "FIXTURE_DATABASE_OR_LOCAL_ERROR", sqlstate=getattr(exc, "pgcode", None))
        if conn:
            conn.rollback()
    finally:
        if conn and created:
            try:
                with conn:
                    with conn.cursor() as cur:
                        for table in ["fact_rating", "bridge_movie_genre", "dim_date", "dim_movie", "dim_user"]:
                            cur.execute(sql.SQL("DROP TABLE {}.{}").format(ns, sql.Identifier(table)))
                        cur.execute(sql.SQL("DROP SCHEMA {}").format(ns))
                report["fixture_schema_removed"] = True
            except Exception:
                report.update(status="FAIL", error_category="FIXTURE_CLEANUP_REQUIRED", fixture_schema_removed=False)
        if conn:
            conn.close()
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    path = ROOT / "results/warehouse" / ("s06c_fixture_" + run + ".json")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "report": str(path.relative_to(ROOT)), "error_category": report.get("error_category")}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
