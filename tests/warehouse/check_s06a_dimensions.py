"""Read-only post-6A check; never invoke the load or bootstrap entry points."""
import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from etl.s05_staging import SafeError, assert_project, catalog, config, connect, sha256, target_counts
from etl.s06a_dimensions import read_prepared, snapshot_check, verify_dimensions, verify_two_view_hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    run = uuid.uuid4().hex
    report = {"step": "6A_VERIFY_READ_ONLY", "run_id": run, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "check_code_sha256": sha256(Path(__file__)), "loader_code_sha256": sha256(ROOT / "etl/s06a_dimensions.py")}
    start = time.monotonic()
    conn = None
    try:
        conn = connect(config(args.env_file))
        conn.set_session(readonly=True)
        with conn:
            assert_project(conn)
            schema = catalog(conn)
            snapshot = snapshot_check(conn, ROOT / "data/raw/p1_s05/ml-1m")
            prepared = read_prepared(conn)
            dims = verify_dimensions(conn, prepared)
            hashes = verify_two_view_hashes(conn)
            counts = target_counts(conn)
            empty = {k: v for k, v in counts.items() if k not in {"dw.dim_user", "dw.dim_movie", "dw.dim_genre", "dw.dim_date"}}
            if any(empty.values()):
                raise SafeError("NON_6A_TARGET_NOT_EMPTY")
            with conn.cursor() as cur:
                cur.execute("SELECT (SELECT count(*) FROM dw.v_ml_movie_genres),(SELECT count(*) FROM dw.v_ml_ratings)")
                if cur.fetchone() != (0, 0):
                    raise SafeError("BRIDGE_FACT_VIEW_NOT_EMPTY")
                cur.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 's06a_test_%'")
                if cur.fetchone()[0]:
                    raise SafeError("FIXTURE_SCHEMA_LEFTOVER")
            report.update(status="PASS", readonly=True, dimensions=dims, canonical_two_views=hashes,
                          unloaded_target_counts=empty, s05_snapshot=snapshot, catalog_matches=schema["keys_match"] and schema["columns_match"],
                          fixture_schemas_remaining=0, g2_complete=False)
    except Exception as exc:
        report.update(status="FAIL", error_category=exc.code if isinstance(exc, SafeError) else "LOCAL_OR_DATABASE_ERROR", sqlstate=getattr(exc, "pgcode", None))
    finally:
        if conn:
            conn.close()
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    path = ROOT / "results/warehouse" / ("s06a_verify_" + run + ".json")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "report": str(path.relative_to(ROOT))}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
