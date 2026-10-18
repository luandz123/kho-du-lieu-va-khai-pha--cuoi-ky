"""P1 local verification of unchanged P2 adapter: raw / local CSV / actual DW."""
import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from etl.run_etl import atomic_json, version_info
from etl.s05_staging import SafeError, assert_project, catalog, config, connect, sha256, verify_sources
from etl.s06b_bridge import RAW


def local_csv(path, body):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".export-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(body); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    run, start = uuid.uuid4().hex, time.monotonic()
    report = {"step": "G2_ADAPTER_LOCAL_VERIFICATION", "run_id": run, "status": "FAIL",
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "etl_version": version_info(),
              "check_code_sha256": sha256(Path(__file__)), "p2_intake_confirmed": False,
              "personal_rows_in_report": False, "csv_committed_to_git": False}
    conn = None
    try:
        adapter = importlib.import_module("mining.data_io")
        expected = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))
        source = json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8"))
        report["verified_source"] = verify_sources(RAW, source)
        blob = subprocess.check_output(["git", "show", "HEAD:mining/data_io.py"], cwd=ROOT)
        import hashlib
        report["p2_adapter_git_blob_sha256"] = hashlib.sha256(blob).hexdigest()
        reviewed = json.loads((ROOT / "docs/P1/s04_inputs_pr5.json").read_text(encoding="utf-8"))
        if (ROOT / "mining/data_io.py").read_bytes().replace(b"\r\n", b"\n") != blob or report["p2_adapter_git_blob_sha256"] != reviewed["script_provenance_checks"]["mining/data_io.py"]["actual"]:
            raise SafeError("P2_ADAPTER_VERSION_NOT_REVIEWED")
        directory = ROOT / "data/processed" / ("p1_g2_" + run)
        directory.mkdir(parents=True, exist_ok=False)
        raw = adapter.load_raw_data(raw_dir=RAW)
        for table, frame in raw.items():
            local_csv(directory / (table + ".csv"), adapter.serialize_df_to_canonical_csv_bytes(table, frame))
        csv = adapter.load_csv_data(processed_dir=directory)
        conn = connect(config(args.env_file))
        conn.set_session(readonly=True, isolation_level="REPEATABLE READ")
        with conn:
            assert_project(conn); catalog(conn)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                dw = adapter.load_dw_data(connection_or_engine=conn)
            with conn.cursor() as cur:
                cur.execute("SHOW transaction_read_only")
                readonly = cur.fetchone()[0] == "on"
                if not readonly:
                    raise SafeError("ADAPTER_SESSION_NOT_READ_ONLY")
                cur.execute("SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user")
                admin = cur.fetchone()
                cur.execute("SELECT bool_or(has_table_privilege(current_user,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE')) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('staging','dw','analytics') AND c.relkind='r'")
                write = cur.fetchone()[0]
            report["connection_privileges"] = {"session_read_only": readonly, "role_superuser": admin[0],
                "role_can_create_database": admin[1], "role_can_create_role": admin[2],
                "role_has_project_table_write_privileges": write, "dedicated_read_only_account_verified": False,
                "p2_remote_connectivity_verified": False}
        tables = {}
        for table in ["users", "movies", "movie_genres", "ratings"]:
            hashes = {name: adapter.compute_canonical_hash(table, frames[table]) for name, frames in [("raw", raw), ("csv", csv), ("dw", dw)]}
            if set(hashes.values()) != {expected["canonical_hashes"][table]} or any(len(frames[table]) != expected["row_counts"][table] for frames in [raw, csv, dw]):
                raise SafeError("RAW_CSV_DW_HASH_OR_COUNT_MISMATCH")
            pd.testing.assert_frame_equal(raw[table], csv[table], check_dtype=False)
            pd.testing.assert_frame_equal(raw[table], dw[table], check_dtype=False)
            if any(list(frames[table].columns) != adapter.TABLE_SCHEMAS[table] for frames in [raw, csv, dw]):
                raise SafeError("ADAPTER_TABLE_COLUMN_ORDER_MISMATCH")
            tables[table] = {"rows": len(dw[table]), "columns": adapter.TABLE_SCHEMAS[table], "sha256": hashes,
                             "all_cells_raw_csv_dw_equal": True, "local_csv_sha256": sha256(directory / (table + ".csv"))}
        verify_sources(RAW, source)
        report.update(status="PASS", tables=tables, local_csv_directory=str(directory.relative_to(ROOT)),
                      adapter_p2_files_modified=False, views_read_directly_on_postgresql=True,
                      dw_manifest_run_id=json.loads((ROOT / "results/warehouse/dw_manifest.json").read_text(encoding="utf-8"))["run_id"])
    except Exception as exc:
        report.update(error_category=exc.code if isinstance(exc, SafeError) else "ADAPTER_OR_LOCAL_VERIFICATION_ERROR",
                      exception_type=type(exc).__name__)
    finally:
        if conn:
            conn.close()
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    path = ROOT / "results/warehouse" / ("s06d_adapter_" + run + ".json")
    atomic_json(path, report)
    print(json.dumps({"status": report["status"], "report": str(path.relative_to(ROOT)), "error_category": report.get("error_category")}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
