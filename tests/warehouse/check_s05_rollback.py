"""Explicit integration test: invented fixture in an isolated, self-created schema.

No CASCADE or production-table mutation. Cleanup names are guarded before DROP.
Run explicitly with --env-file; never imported by test discovery.
"""
import argparse
import hashlib
import json
import sys
import tempfile
import time
import uuid
from pathlib import Path

from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from etl.s05_staging import (SPECS, SafeError, assert_project, config, connect,
                            refresh_body, sha256, target_counts, verify_staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    run_id = uuid.uuid4().hex
    schema = "s05_test_" + run_id[:12]
    try:
        conn = connect(config(args.env_file))
    except Exception:
        print(json.dumps({"status": "FAIL", "error_category": "LOCAL_CONNECTION_UNAVAILABLE"}))
        return 2
    started = time.monotonic()
    report = {"run_id": run_id, "fixture": "INVENTED_NOT_MOVIELENS_ROWS", "schema": schema,
              "code_sha256": sha256(Path(__file__)), "status": "FAIL"}
    created = False
    try:
        with conn:
            assert_project(conn)
            before_targets = target_counts(conn)
            before_production = verify_staging(conn, ROOT / "data/raw/p1_s05/ml-1m")
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
                for table in SPECS:
                    cur.execute(sql.SQL("CREATE TABLE {}.{} (LIKE staging.{} INCLUDING ALL)").format(sql.Identifier(schema), sql.Identifier(table), sql.Identifier(table)))
            created = True
        with tempfile.TemporaryDirectory(prefix="btl_s05_fixture_") as temp:
            raw = Path(temp)
            (raw / "users.dat").write_text("101::F::18::4::inventedZIP\n", encoding="latin-1")
            (raw / "movies.dat").write_text('701::Fixture é, "film" (2001)::Comedy|Drama\n', encoding="latin-1")
            (raw / "ratings.dat").write_text("101::701::4::123\n", encoding="latin-1")
            wanted = {table: 1 for table in SPECS}
            with conn:
                baseline = refresh_body(conn, raw, wanted, schema)
            # Replacement users+movies are actually COPY-loaded before ratings fails.
            (raw / "users.dat").write_text("999::M::25::1::inventedZIP\n", encoding="latin-1")
            (raw / "movies.dat").write_text("999::Different fixture::Drama\n", encoding="latin-1")
            (raw / "ratings.dat").write_text("MALFORMED_FIXTURE\n", encoding="latin-1")
            stats = {}
            try:
                with conn:
                    refresh_body(conn, raw, wanted, schema, stats)
            except SafeError as exc:
                if exc.code != "MALFORMED_FIELD_COUNT":
                    raise
                report["expected_error"] = exc.code
            else:
                raise SafeError("ROLLBACK_TEST_DID_NOT_FAIL")
            report["failure_counters_before_rollback"] = stats
            # Restore fixture input only, not database, and compare DB against seed.
            (raw / "users.dat").write_text("101::F::18::4::inventedZIP\n", encoding="latin-1")
            (raw / "movies.dat").write_text('701::Fixture é, "film" (2001)::Comedy|Drama\n', encoding="latin-1")
            (raw / "ratings.dat").write_text("101::701::4::123\n", encoding="latin-1")
            with conn:
                after = verify_staging(conn, raw, schema)
                after_targets = target_counts(conn)
                after_production = verify_staging(conn, ROOT / "data/raw/p1_s05/ml-1m")
            if after != baseline or before_targets != after_targets or before_production != after_production:
                raise SafeError("ROLLBACK_DID_NOT_RESTORE")
            report.update(status="PASS", fixture_tables_restored_exactly=True,
                          production_dw_analytics_unchanged=True,
                          production_staging_unchanged_exactly=True,
                          inserted_users_movies_before_failure=all(stats[t]["loaded"] == 1 for t in ("users_raw", "movies_raw")),
                          fixture_baseline=baseline, target_counts=after_targets)
    except Exception as exc:
        report["error_category"] = exc.code if isinstance(exc, SafeError) else "INTEGRATION_TEST_ERROR"
        report["sqlstate"] = getattr(exc, "pgcode", None)
        conn.rollback()
    finally:
        if created:
            with conn:
                with conn.cursor() as cur:
                    # Only the exact UUID schema created above; no CASCADE.
                    for table in SPECS:
                        cur.execute(sql.SQL("DROP TABLE {}.{}").format(sql.Identifier(schema), sql.Identifier(table)))
                    cur.execute(sql.SQL("DROP SCHEMA {}").format(sql.Identifier(schema)))
            report["fixture_schema_removed"] = True
        conn.close()
    report["duration_seconds"] = round(time.monotonic() - started, 3)
    path = ROOT / "results/warehouse" / ("s05_rollback_" + run_id + ".json")
    with path.open("x", encoding="utf-8") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"status": report["status"], "report": str(path.relative_to(ROOT)), "error_category": report.get("error_category")}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
