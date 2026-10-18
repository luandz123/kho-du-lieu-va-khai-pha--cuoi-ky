"""Full pipeline rollback with seeded old data/model in one isolated fixture schema."""
import argparse
import importlib
import json
import re
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from etl.run_etl import atomic_json, atomic_refresh, digest_json, identifier, model_state, scope, version_info
from etl.s05_staging import SPECS, SafeError, assert_project, catalog, config, connect, copy_staging, sha256
from etl.s06a_dimensions import insert_dimensions, prepare_dimensions, verify_dimensions
from etl.s06b_bridge import insert_bridge, prepare_bridge, verify_bridge
from etl.s06c_fact import insert_fact, read_mappings, verify_integrity


def fixture_files(folder, old=False, fault=None):
    folder.mkdir()
    files = {"users.dat": "101::F::18::4::00000\n",
             "movies.dat": ('701::Old fixture::Comedy|Drama\n' if old else '701::Éxample, "new" (2001)::Comedy|Drama\n'),
             "ratings.dat": "101::701::" + ("3" if old else "5") + "::946684800\n"}
    if fault == "parse":
        files["movies.dat"] = "malformed::fixture\n"
    elif fault == "mapping":
        files["ratings.dat"] = "999::701::5::946684800\n"
    elif fault == "rating":
        files["ratings.dat"] = "101::701::6::946684800\n"
    elif fault == "duplicate":
        files["ratings.dat"] *= 2
    for name, text in files.items():
        (folder / name).write_bytes(text.encode("latin-1"))
    return {table: len(files[spec[0]].splitlines()) for table, spec in SPECS.items()}


def all_snapshot(conn, tables, registry):
    result = {}
    with conn.cursor() as cur:
        for table in (*tables, registry):
            cur.execute(sql.SQL("SELECT row_to_json(r) FROM {} r ORDER BY row_to_json(r)::text").format(identifier(table)))
            rows = [r[0] for r in cur.fetchall()]
            result[table.split(".")[1]] = {"rows": len(rows), "all_fields_sha256": digest_json(rows)}
        sequences = {}
        for table, key in [("dim_user", "user_key"), ("dim_movie", "movie_key"), ("dim_date", "date_key"), ("dim_genre", "genre_key"), ("fact_rating", "rating_key")]:
            schema = registry.split(".")[0]
            cur.execute("SELECT pg_get_serial_sequence(%s,%s)", (schema + "." + table, key))
            sequence = cur.fetchone()[0]
            cur.execute(sql.SQL("SELECT last_value,is_called FROM {}").format(identifier(sequence)))
            sequences[table] = cur.fetchone()
    return {"tables": result, "sequences": sequences, "model": model_state(conn, registry)}


def populate_fixture(conn, schema, raw, counts, progress, fault=None):
    ns = sql.Identifier(schema)
    stats = {}
    progress["copy_counters"] = stats
    copy_staging(conn, raw, counts, schema, stats)
    contract = json.loads((ROOT / "docs/shared/data_contract.json").read_text(encoding="utf-8"))
    codes = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))["source_code_sets"]
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.users_raw ORDER BY source_line").format(ns)); users = cur.fetchall()
        cur.execute(sql.SQL("SELECT * FROM {}.movies_raw ORDER BY source_line").format(ns)); movies = cur.fetchall()
        cur.execute(sql.SQL("SELECT min(timestamp_raw::numeric)::text,max(timestamp_raw::numeric)::text FROM {}.ratings_raw").format(ns)); low, high = cur.fetchone()
    prepared = prepare_dimensions(users, movies, low, high, contract, codes)
    insert_dimensions(conn, prepared, schema)
    verify_dimensions(conn, prepared, schema)
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT movie_id,movie_key FROM {}.dim_movie").format(ns)); mm = cur.fetchall()
        cur.execute(sql.SQL("SELECT genre_name,genre_key FROM {}.dim_genre").format(ns)); gm = cur.fetchall()
        cur.execute(sql.SQL("SELECT * FROM {}.ratings_raw ORDER BY source_line").format(ns)); ratings = cur.fetchall()
    bridge = prepare_bridge(movies, mm, gm, set(codes["genres"]))
    insert_bridge(conn, bridge, schema)
    verify_bridge(conn, bridge, schema)
    insert_fact(conn, iter(ratings), read_mappings(conn, schema), schema)
    if fault == "fk":
        with conn.cursor() as cur:
            cur.execute(sql.SQL("INSERT INTO {s}.fact_rating (user_key,movie_key,date_key,rating,rating_timestamp,rated_at) SELECT 999999,movie_key,date_key,3,rating_timestamp,rated_at FROM {s}.fact_rating LIMIT 1").format(s=ns))
    return {"staging_rows": counts, "fact_rows": len(ratings)}


def verify_fixture(conn, schema, expected, fault=None):
    adapter = importlib.import_module("mining.data_io")
    hashes = {}
    with conn.cursor() as cur:
        for table, order in [("users", "user_id"), ("movies", "movie_id"), ("movie_genres", "movie_id,genre_name"), ("ratings", 'user_id,movie_id,"timestamp",rating')]:
            cur.execute(sql.SQL("SELECT * FROM {}.{} ORDER BY " + order).format(sql.Identifier(schema), sql.Identifier("v_ml_" + table)))
            frame = pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])
            if table == "movies":
                frame["release_year"] = frame["release_year"].astype("Int64")
            hashes[table] = adapter.compute_canonical_hash(table, frame)
        if hashes != expected or fault == "checksum":
            raise SafeError("FIXTURE_CANONICAL_CHECKSUM_MISMATCH")
    return {"canonical_hashes": hashes, "fact": verify_integrity(conn, schema)}


def production_signature(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT (SELECT count(*) FROM dw.fact_rating),(SELECT sum(rating) FROM dw.fact_rating),(SELECT count(*) FROM staging.ratings_raw),(SELECT count(*) FROM dw.bridge_movie_genre),(SELECT count(*) FROM analytics.model_registry)")
        return cur.fetchone()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    run, start = uuid.uuid4().hex, time.monotonic()
    schema = "s06d_test_" + run[:12]
    registry, tables = scope(schema)
    report = {"step": "6D_ROLLBACK_FIXTURE", "run_id": run, "status": "FAIL", "fixture": "INVENTED_DATA_AND_MODEL_ONLY",
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "etl_version": version_info(),
              "test_code_sha256": sha256(Path(__file__)), "schema": schema}
    conn, created, table_names, view_names = None, False, [], []
    try:
        conn = connect(config(args.env_file))
        with conn:
            assert_project(conn); catalog(conn)
            production_before = production_signature(conn)
            ddl = re.sub(r"--[^\n]*", "", (ROOT / "database/schema.sql").read_text(encoding="utf-8"))
            statements = re.findall(r"^CREATE (?:TABLE|(?:UNIQUE )?INDEX|VIEW)\s[\s\S]*?;", ddl, flags=re.M)
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
                for statement in statements:
                    translated = re.sub(r"\b(?:staging|dw|analytics)\.", schema + ".", statement)
                    cur.execute(translated)
                    if statement.startswith("CREATE TABLE"):
                        table_names.append(re.match(r"CREATE TABLE \w+\.(\w+)", statement)[1])
                    elif statement.startswith("CREATE VIEW"):
                        view_names.append(re.match(r"CREATE VIEW \w+\.(\w+)", statement)[1])
            if len(table_names) != 12 or len(view_names) != 6:
                raise SafeError("FIXTURE_APPROVED_DDL_EXTRACTION_MISMATCH")
        created = True
        with tempfile.TemporaryDirectory(prefix="p1-6d-fixture-") as temp:
            folder = Path(temp)
            old, new = folder / "old", folder / "new"
            old_counts = fixture_files(old, old=True)
            new_counts = fixture_files(new)
            adapter = importlib.import_module("mining.data_io")
            old_hashes = {t: adapter.compute_canonical_hash(t, f) for t, f in adapter.load_raw_data(old).items()}
            new_hashes = {t: adapter.compute_canonical_hash(t, f) for t, f in adapter.load_raw_data(new).items()}
            atomic_refresh(conn, lambda c: populate_fixture(c, schema, old, old_counts, {}), lambda c: verify_fixture(c, schema, old_hashes), fixture_schema=schema)
            with conn:
                with conn.cursor() as cur:
                    # Real constraints, entirely invented metadata; not a trained model or G3.
                    cur.execute(sql.SQL("INSERT INTO {}.model_registry (model_version,contract_version,source_hashes,canonical_hashes,k,seed,preprocessing,genre_order,libraries,training_config_hash,model_created_at,is_valid_for_dw,is_active) VALUES ('fixture_NOT_REAL_MODEL',2,%s::jsonb,%s::jsonb,2,42,'{{}}',ARRAY['Comedy','Drama'],'{{}}',%s,'2000-01-01T00:00:00Z',true,true)").format(sql.Identifier(schema)),
                                (json.dumps({k: "fixture" for k in ["users.dat", "movies.dat", "ratings.dat", "README"]}), json.dumps(old_hashes), "0" * 64))
                    cur.execute(sql.SQL("INSERT INTO {}.user_cluster VALUES ('fixture_NOT_REAL_MODEL',101,0,'assigned')").format(sql.Identifier(schema)))
                    cur.execute(sql.SQL("INSERT INTO {}.cluster_genre_profile VALUES ('fixture_NOT_REAL_MODEL',0,'Comedy',0.5,1),('fixture_NOT_REAL_MODEL',0,'Drama',0.5,1)").format(sql.Identifier(schema)))
                baseline = all_snapshot(conn, tables, registry)
            cases = []
            for fault in ["parse", "mapping", "fk", "rating", "duplicate", "checksum"]:
                path = folder / fault
                counts = fixture_files(path, fault=fault)
                progress = {}
                try:
                    atomic_refresh(conn, lambda c: populate_fixture(c, schema, path, counts, progress, fault),
                                   lambda c: verify_fixture(c, schema, new_hashes, fault), fixture_schema=schema, progress=progress)
                except SafeError as exc:
                    if exc.details.get("database_outcome") != "ROLLED_BACK":
                        raise
                    category, state = exc.code, exc.details.get("sqlstate")
                    expected = {"parse": "MALFORMED_FIELD_COUNT", "mapping": "MISSING_USER_MAPPING", "fk": "REFRESH_SQL_OR_LOCAL_ERROR",
                                "rating": "OUT_OF_RANGE_RATING", "duplicate": "DUPLICATE_SOURCE_USER_MOVIE", "checksum": "FIXTURE_CANONICAL_CHECKSUM_MISMATCH"}[fault]
                    if category != expected or (fault == "fk" and state != "23503"):
                        raise SafeError("FIXTURE_FAILED_FOR_UNEXPECTED_REASON")
                else:
                    raise SafeError("EXPECTED_PIPELINE_ERROR_DID_NOT_OCCUR")
                with conn:
                    restored = all_snapshot(conn, tables, registry)
                if restored != baseline or not progress.get("model_invalidated") or progress.get("truncate_statements") != 1:
                    raise SafeError("SEEDED_DATA_MODEL_OR_IDENTITY_NOT_RESTORED")
                cases.append({"fault": fault, "category": category, "sqlstate": state, "truncate_statements": 1,
                              "all_seeded_tables_restored": True, "identity_sequences_restored": True,
                              "active_valid_model_and_results_restored": True, "snapshot_sha256": digest_json(restored)})
            success = atomic_refresh(conn, lambda c: populate_fixture(c, schema, new, new_counts, {}), lambda c: verify_fixture(c, schema, new_hashes), fixture_schema=schema)
            with conn:
                state = model_state(conn, registry)
                if state["active"] or state["valid"] or state["registry_rows"] != 1:
                    raise SafeError("FIXTURE_OLD_MODEL_STILL_USABLE")
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("SELECT (SELECT count(*) FROM {s}.user_cluster),(SELECT count(*) FROM {s}.cluster_genre_profile)").format(s=sql.Identifier(schema)))
                    if cur.fetchone() != (0, 0):
                        raise SafeError("FIXTURE_OLD_CLUSTER_RESULTS_REMAIN")
            report.update(status="PASS", rollback_cases=cases, seeded_snapshot_sha256=digest_json(baseline),
                          seeded_fact_rows=1, seeded_cluster_rows=1, seeded_profile_rows=2,
                          all_12_seeded_tables_and_identity_state_checked=True,
                          successful_fixture_refresh=success, old_model_retained_inactive_invalid=True)
        with conn:
            with conn.cursor() as cur:
                for view in reversed(view_names):
                    cur.execute(sql.SQL("DROP VIEW {}.{}").format(sql.Identifier(schema), sql.Identifier(view)))
                for table in reversed(table_names):
                    cur.execute(sql.SQL("DROP TABLE {}.{}").format(sql.Identifier(schema), sql.Identifier(table)))
                cur.execute(sql.SQL("DROP SCHEMA {}").format(sql.Identifier(schema)))
        created = False
        report["fixture_schema_removed"] = True
        with conn:
            catalog(conn)
            if production_signature(conn) != production_before:
                raise SafeError("PRODUCTION_SIGNATURE_CHANGED_DURING_FIXTURE")
        report["production_signature_unchanged"] = True
    except Exception as exc:
        report.update(status="FAIL", error_category=exc.code if isinstance(exc, SafeError) else "FIXTURE_SQL_OR_LOCAL_ERROR", sqlstate=getattr(exc, "pgcode", None))
        if conn:
            conn.rollback()
    finally:
        if conn and created:
            try:
                with conn:
                    with conn.cursor() as cur:
                        for view in reversed(view_names):
                            cur.execute(sql.SQL("DROP VIEW {}.{}").format(sql.Identifier(schema), sql.Identifier(view)))
                        for table in reversed(table_names):
                            cur.execute(sql.SQL("DROP TABLE {}.{}").format(sql.Identifier(schema), sql.Identifier(table)))
                        cur.execute(sql.SQL("DROP SCHEMA {}").format(sql.Identifier(schema)))
                report["fixture_schema_removed"] = True
            except Exception:
                report.update(status="FAIL", error_category="FIXTURE_CLEANUP_REQUIRED", fixture_schema_removed=False)
        if conn:
            conn.close()
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    path = ROOT / "results/warehouse" / ("s06d_rollback_" + run + ".json")
    atomic_json(path, report)
    print(json.dumps({"status": report["status"], "report": str(path.relative_to(ROOT)), "error_category": report.get("error_category")}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
