"""S05 only: verify inputs, bootstrap approved DDL, load/verify raw staging.

No dimension/fact/analytics transform or loading. Secrets and row contents never log.
"""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import importlib
import json
import re
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
TARGET_DB = "movielens_btl"
SPECS = {
    "users_raw": ("users.dat", 5, ("user_id_raw", "gender_raw", "age_code_raw", "occupation_raw")),
    "movies_raw": ("movies.dat", 3, ("movie_id_raw", "title_raw", "genres_raw")),
    "ratings_raw": ("ratings.dat", 4, ("user_id_raw", "movie_id_raw", "rating_raw", "timestamp_raw")),
}


class SafeError(Exception):
    """Only a stable category and non-sensitive file/line context may be emitted."""

    def __init__(self, code, *, file=None, line=None):
        super().__init__(code)
        self.code, self.file, self.line = code, file, line
        self.details = {}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def config(env_file):
    c = dotenv_values(env_file, interpolate=False)
    if any(not c.get(k) for k in (
        "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"
    )):
        raise SafeError("MISSING_LOCAL_CONFIG")
    try:
        port = int(c["POSTGRES_PORT"])
        if not 1 <= port <= 65535:
            raise ValueError()
    except ValueError:
        raise SafeError("INVALID_PORT") from None
    return c


def connect(c, *, maintenance=False):
    return psycopg2.connect(
        host=c["POSTGRES_HOST"], port=int(c["POSTGRES_PORT"]),
        dbname=c["POSTGRES_DB"] if maintenance else TARGET_DB,
        user=c["POSTGRES_USER"], password=c["POSTGRES_PASSWORD"],
        connect_timeout=5, application_name="btl_p1_s05",
        options="-c timezone=UTC -c lock_timeout=5000 -c statement_timeout=180000",
    )


def raw_rows(raw_dir, table):
    """One source line -> one retained raw row; ZIP never leaves this reader."""
    filename, fields, columns = SPECS[table]
    with (Path(raw_dir) / filename).open("rb") as stream:
        for number, raw in enumerate(stream, 1):
            raw = raw.removesuffix(b"\n").removesuffix(b"\r")
            values = raw.decode("latin-1").split("::")
            if len(values) != fields:
                raise SafeError("MALFORMED_FIELD_COUNT", file=filename, line=number)
            retained = values[:len(columns)]  # users ZIP is the fifth field, excluded.
            if any(not value or "\x00" in value for value in retained):
                raise SafeError("EMPTY_OR_NUL_FIELD", file=filename, line=number)
            yield (number, *retained)


def verify_sources(raw_dir, manifest):
    result = {}
    for filename, spec in manifest["files"].items():
        path = Path(raw_dir) / filename
        if not path.is_file():
            raise SafeError("SOURCE_MISSING", file=filename)
        actual_hash = sha256(path)
        with path.open("rb") as stream:
            lines = sum(1 for _ in stream)
        if actual_hash != spec["sha256"] or lines != spec["line_count"]:
            raise SafeError("SOURCE_HASH_OR_COUNT_MISMATCH", file=filename)
        result[filename] = {"sha256": actual_hash, "line_count": lines, "matches": True}
    return result


def verify_inputs(raw_dir):
    source = json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8"))
    canonical = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))
    result = {"source": verify_sources(raw_dir, source), "canonical": {}}
    reviewed = json.loads((ROOT / "docs/P1/s04_inputs_pr5.json").read_text(encoding="utf-8"))
    adapter_blob = subprocess.check_output(["git", "show", "HEAD:mining/data_io.py"], cwd=ROOT)
    physical = (ROOT / "mining/data_io.py").read_bytes()
    if physical.replace(b"\r\n", b"\n") != adapter_blob or hashlib.sha256(adapter_blob).hexdigest() != reviewed["script_provenance_checks"]["mining/data_io.py"]["actual"]:
        raise SafeError("ADAPTER_DIFFERS_FROM_REVIEWED_VERSION")
    result["reviewed_adapter_git_blob_sha256"] = hashlib.sha256(adapter_blob).hexdigest()
    result["adapter_checkout_note"] = "Windows CRLF only; normalized checkout equals reviewed LF Git blob. Source/data hashes are never normalized."
    adapter = importlib.import_module("mining.data_io")
    tables = adapter.load_raw_data(Path(raw_dir))
    for name, frame in tables.items():
        digest = adapter.compute_canonical_hash(name, frame)
        if digest != canonical["canonical_hashes"][name] or len(frame) != canonical["row_counts"][name]:
            raise SafeError("CANONICAL_MISMATCH", file=name)
        result["canonical"][name] = {"rows": len(frame), "sha256": digest, "matches": True}
    result["adapter_sha256"] = sha256(ROOT / "mining/data_io.py")
    result["serializer_sha256"] = result["adapter_sha256"]
    result["adapter_git_commit"] = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", "mining/data_io.py"], cwd=ROOT, text=True
    ).strip()
    result["manifest_metadata_note"] = "source_code_commit field is historical; use observed adapter commit/hash above"
    del tables
    gc.collect()
    return result


def origin_marker():
    return "BTL MovieLens P1 S05; contract=2; schema_sha256=" + sha256(ROOT / "database/schema.sql")


def assert_project(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database()")
        name, marker = cur.fetchone()
        if name != TARGET_DB or marker != origin_marker():
            raise SafeError("UNVERIFIED_PROJECT_DATABASE")


def catalog(conn):
    expected = json.loads((ROOT / "docs/P1/s04_design_checks_v2.json").read_text(encoding="utf-8"))
    inventory = expected["sql_inventory"]
    with conn.cursor() as cur:
        cur.execute("SELECT table_schema||'.'||table_name FROM information_schema.tables WHERE table_type='BASE TABLE' AND table_schema NOT IN ('pg_catalog','information_schema')")
        actual_tables = {r[0] for r in cur.fetchall()}
        if actual_tables != set(inventory):
            raise SafeError("CATALOG_TABLE_SET_MISMATCH")
        cur.execute("""SELECT n.nspname||'.'||c.relname,a.attname,format_type(a.atttypid,a.atttypmod),a.attnotnull,a.attidentity,a.attgenerated
            FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname IN ('staging','dw','analytics') AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped ORDER BY n.nspname,c.relname,a.attnum""")
        columns = {}
        for table, col, typ, nn, identity, generated in cur.fetchall():
            typ = {"timestamp with time zone": "timestamptz"}.get(typ, typ)
            columns.setdefault(table, {})[col] = {"type": typ, "nullable_sql": not nn, "identity": bool(identity), "generated": bool(generated)}
        if columns != {t: spec["columns"] for t, spec in inventory.items()} or any(list(columns[t]) != list(spec["columns"]) for t, spec in inventory.items()):
            raise SafeError("CATALOG_COLUMN_MISMATCH")
        cur.execute("""SELECT n.nspname||'.'||c.relname,k.contype,k.convalidated,
            ARRAY(SELECT a.attname FROM unnest(k.conkey) WITH ORDINALITY x(id,ord) JOIN pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=x.id ORDER BY x.ord),
            rn.nspname||'.'||rc.relname,
            ARRAY(SELECT a.attname FROM unnest(k.confkey) WITH ORDINALITY x(id,ord) JOIN pg_attribute a ON a.attrelid=k.confrelid AND a.attnum=x.id ORDER BY x.ord),pg_get_constraintdef(k.oid)
            FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace
            LEFT JOIN pg_class rc ON rc.oid=k.confrelid LEFT JOIN pg_namespace rn ON rn.oid=rc.relnamespace
            WHERE n.nspname IN ('staging','dw','analytics')""")
        constraints = cur.fetchall()
        for table, spec in inventory.items():
            items = [r for r in constraints if r[0] == table]
            pk = [r[3] for r in items if r[1] == "p"]
            uq = sorted(r[3] for r in items if r[1] == "u")
            fk = sorted((r[3], r[4], r[5]) for r in items if r[1] == "f")
            wanted_fk = sorted((f["columns"], f["target"], f["target_columns"]) for f in spec["foreign_keys"])
            if pk != [spec["primary_key"]] or uq != sorted(spec["unique_keys"]) or fk != wanted_fk:
                raise SafeError("CATALOG_KEY_MISMATCH", file=table)
        if not all(r[2] for r in constraints):
            raise SafeError("UNVALIDATED_CONSTRAINT")
        checks = sum(r[1] == "c" for r in constraints)
        if checks != len(re.findall(r"\bCHECK\s*\(", (ROOT / "database/schema.sql").read_text(encoding="utf-8"))):
            raise SafeError("CATALOG_CHECK_COUNT_MISMATCH")
        cur.execute("SELECT n.nspname||'.'||t.relname,i.relname,pg_get_indexdef(i.oid),pg_get_expr(x.indpred,x.indrelid) FROM pg_index x JOIN pg_class i ON i.oid=x.indexrelid JOIN pg_class t ON t.oid=x.indrelid JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname IN ('staging','dw','analytics')")
        indexes = cur.fetchall()
        for spec in expected["index_inventory"]:
            match = [r for r in indexes if r[0] == spec["table"] and r[1] == spec["name"]]
            if len(match) != 1 or ("UNIQUE INDEX" in match[0][2]) != spec["unique"]:
                raise SafeError("CATALOG_INDEX_MISMATCH")
            if not all(c in match[0][2] for c in spec["columns"]):
                raise SafeError("CATALOG_INDEX_COLUMN_MISMATCH")
        if not any(r[1] == "uq_model_registry_one_active" and r[3] == "is_active" for r in indexes):
            raise SafeError("CATALOG_ACTIVE_INDEX_MISMATCH")
        contract = json.loads((ROOT / "docs/shared/data_contract.json").read_text(encoding="utf-8"))
        cur.execute("SELECT schemaname||'.'||viewname FROM pg_views WHERE schemaname IN ('staging','dw','analytics')")
        views = {r[0] for r in cur.fetchall()}
        if views != set(contract["dw_views"].values()) | {"analytics.v_active_user_cluster", "analytics.v_active_cluster_genre_profile"}:
            raise SafeError("CATALOG_VIEW_SET_MISMATCH")
        view_columns = {}
        for logical, view in contract["dw_views"].items():
            cur.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position", view.split("."))
            cols = cur.fetchall()
            types = expected["contract_view_types_inferred"][view]
            if [r[0] for r in cols] != [r[0] for r in contract["tables"][logical]["columns"]] or [r[1] for r in cols] != types:
                raise SafeError("CATALOG_VIEW_MISMATCH", file=view)
            view_columns[view] = cols
        cur.execute("SELECT viewname,definition FROM pg_views WHERE schemaname='dw' AND viewname='v_ml_ratings'")
        definition = cur.fetchone()[1]
        if any(x in definition for x in ("bridge_movie_genre", "dim_genre")):
            raise SafeError("RATINGS_VIEW_MULTIPLICATION")
        return {"tables": len(columns), "columns": sum(map(len, columns.values())), "views": len(views), "foreign_keys": sum(r[1] == "f" for r in constraints),
                "check_constraints": checks, "explicit_indexes": len(expected["index_inventory"]), "columns_match": True, "keys_match": True,
                "constraints_validated": True, "view_columns_and_types": view_columns,
                "constraint_definitions": [{"table": r[0], "type": r[1], "definition": r[6]} for r in constraints]}


def bootstrap(c):
    marker = origin_marker()
    maintenance = connect(c, maintenance=True)
    maintenance.autocommit = True
    created = False
    try:
        with maintenance.cursor() as cur:
            cur.execute("SELECT shobj_description(oid,'pg_database') FROM pg_database WHERE datname=%s", (TARGET_DB,))
            existing = cur.fetchone()
            if existing is None:
                cur.execute("SELECT rolcreatedb OR rolsuper FROM pg_roles WHERE rolname=current_user")
                if not cur.fetchone()[0]:
                    raise SafeError("CREATE_DATABASE_PERMISSION_REQUIRED")
                cur.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'").format(sql.Identifier(TARGET_DB)))
                created = True
                cur.execute(sql.SQL("COMMENT ON DATABASE {} IS %s").format(sql.Identifier(TARGET_DB)), (marker,))
            elif existing[0] != marker:
                raise SafeError("EXISTING_DATABASE_ORIGIN_UNKNOWN_KEEP_UNCHANGED")
    finally:
        maintenance.close()
    conn = connect(c)
    conn.autocommit = True
    try:
        assert_project(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema' AND c.relkind IN ('r','v','m','S','f')")
            objects = cur.fetchone()[0]
            if objects:
                return {"database_created": created, "ddl": "EXISTING_VERIFIED_NO_DDL", "catalog": catalog(conn), "non_staging_counts": target_counts(conn)}
            cur.execute("SELECT set_config('btl.target_database',%s,false)", (TARGET_DB,))
            approved = (ROOT / "database/schema.sql").read_text(encoding="utf-8")
            if not approved.rstrip().endswith("COMMIT;"):
                raise SafeError("DDL_TRANSACTION_WRAPPER_CHANGED")
            # Keep approved statements; defer its final COMMIT until catalog matches.
            cur.execute(approved.rsplit("COMMIT;", 1)[0])
            verified = catalog(conn)
            counts = target_counts(conn)
            if any(counts.values()):
                raise SafeError("TARGET_NOT_EMPTY")
            cur.execute("COMMIT")
            return {"database_created": created, "ddl": "EXECUTED_CATALOG_VERIFIED_COMMITTED", "schema_sha256": sha256(ROOT / "database/schema.sql"), "catalog": verified, "non_staging_counts": counts}
    except Exception:
        with conn.cursor() as cur:
            cur.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def target_counts(conn):
    inventory = json.loads((ROOT / "docs/P1/s04_design_checks_v2.json").read_text(encoding="utf-8"))["sql_inventory"]
    result = {}
    with conn.cursor() as cur:
        for name in inventory:
            if name.startswith("staging."):
                continue
            cur.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(*map(sql.Identifier, name.split("."))))
            result[name] = cur.fetchone()[0]
    return result


class DigestSink:
    def __init__(self):
        self.h = hashlib.sha256()

    def write(self, text):
        self.h.update(text.encode("utf-8"))
        return len(text)


def verify_staging(conn, raw_dir, schema="staging"):
    result = {}
    for table in SPECS:
        sink = DigestSink()
        writer = csv.writer(sink, lineterminator="\n")
        non_ascii = quotes = commas = 0
        count = 0
        with conn.cursor(name="s05_verify_" + uuid.uuid4().hex) as cur:
            cur.itersize = 10000
            cur.execute(sql.SQL("SELECT * FROM {}.{} ORDER BY source_line").format(sql.Identifier(schema), sql.Identifier(table)))
            for source, actual in zip_longest(raw_rows(raw_dir, table), cur):
                if source != actual:
                    raise SafeError("SOURCE_STAGING_FIELD_OR_ORDER_MISMATCH", file=SPECS[table][0])
                writer.writerow(actual)
                count += 1
                if table == "movies_raw":
                    title = source[2]
                    non_ascii += any(ord(c) > 127 for c in title)
                    quotes += '"' in title
                    commas += ',' in title
        result[table] = {"rows": count, "min_source_line": 1 if count else None, "max_source_line": count or None,
                         "source_staging_all_fields_exact": True, "retained_row_csv_sha256": sink.h.hexdigest()}
        if table == "movies_raw":
            result[table]["special_title_counts"] = {"non_ascii": non_ascii, "quote": quotes, "comma": commas}
    return result


def refresh_body(conn, raw_dir, expected_counts, schema="staging", stats=None):
    if schema != "staging" and not re.fullmatch(r"s05_test_[0-9a-f]{12}", schema):
        raise SafeError("INVALID_STAGING_NAMESPACE")
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(20261027,1)")
        cur.execute(sql.SQL("TRUNCATE {} ").format(sql.SQL(", ").join(sql.Identifier(schema, table) for table in SPECS)))
    return copy_staging(conn, raw_dir, expected_counts, schema, stats)


def copy_staging(conn, raw_dir, expected_counts, schema="staging", stats=None):
    """COPY/verify only; transaction and clearing belong to the caller (S05/6D)."""
    if schema != "staging" and not re.fullmatch(r"(?:s05|s06d)_test_[0-9a-f]{12}", schema):
        raise SafeError("INVALID_STAGING_NAMESPACE")
    stats = stats if stats is not None else {}
    with conn.cursor() as cur:
        for table, (filename, _, columns) in SPECS.items():
            stats[table] = {"read": 0, "loaded": 0, "errors": 0}
            # Disk spill is local/temporary, never a repository artifact.
            with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream, lineterminator="\n")
                try:
                    for row in raw_rows(raw_dir, table):
                        stats[table]["read"] += 1
                        writer.writerow(row)
                except SafeError:
                    stats[table]["errors"] += 1
                    raise
                if stats[table]["read"] != expected_counts[table]:
                    stats[table]["errors"] += 1
                    raise SafeError("STAGING_SOURCE_COUNT_MISMATCH", file=filename)
                stream.seek(0)
                command = sql.SQL("COPY {}.{} ({}) FROM STDIN WITH (FORMAT CSV)").format(
                    sql.Identifier(schema), sql.Identifier(table), sql.SQL(",").join(map(sql.Identifier, ("source_line", *columns))))
                try:
                    cur.copy_expert(command.as_string(conn), stream)
                except psycopg2.Error:
                    stats[table]["errors"] += 1
                    raise
                cur.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table)))
                stats[table]["loaded"] = cur.fetchone()[0]
                if stats[table]["loaded"] != expected_counts[table]:
                    stats[table]["errors"] += 1
                    raise SafeError("STAGING_LOADED_COUNT_MISMATCH", file=filename)
    return verify_staging(conn, raw_dir, schema)


def load_staging(c, raw_dir):
    source = json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8"))
    verified_source = verify_sources(raw_dir, source)
    counts = {table: source["files"][spec[0]]["line_count"] for table, spec in SPECS.items()}
    conn = connect(c)
    stats = {}
    try:
        with conn:
            assert_project(conn)
            catalog(conn)  # Refuse catalog drift before any TRUNCATE.
            if any(target_counts(conn).values()):
                raise SafeError("S05_REQUIRES_EMPTY_DW_ANALYTICS")
            verified = refresh_body(conn, raw_dir, counts, stats=stats)
            verify_sources(raw_dir, source)  # Detect source changes during the load.
            empty = target_counts(conn)
            if any(empty.values()):
                raise SafeError("NON_STAGING_TARGET_CHANGED")
        return {"transaction": "COMMITTED", "source": verified_source, "staging": verified, "counters": stats, "non_staging_counts": empty}
    except SafeError as exc:
        exc.details = {"transaction": "ROLLED_BACK", "attempted_counters": stats}
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["inputs", "bootstrap", "load", "catalog"])
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/p1_s05/ml-1m")
    args = parser.parse_args()
    run_id = uuid.uuid4().hex
    start = time.monotonic()
    report = {"step": "S05", "action": args.action, "run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "target_database": TARGET_DB, "code_base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "code_sha256": sha256(Path(__file__)), "data_rows_in_report": False}
    code = 0
    try:
        if args.action == "inputs":
            report["result"] = verify_inputs(args.raw_dir)
        else:
            c = config(args.env_file)
            report["endpoint"] = {"host": c["POSTGRES_HOST"], "port": int(c["POSTGRES_PORT"])}
            if args.action == "bootstrap":
                report["result"] = bootstrap(c)
            elif args.action == "load":
                report["result"] = load_staging(c, args.raw_dir)
            else:
                conn = connect(c)
                try:
                    conn.set_session(readonly=True)
                    with conn:
                        assert_project(conn)
                        report["result"] = {"catalog": catalog(conn), "non_staging_counts": target_counts(conn)}
                finally:
                    conn.close()
        report["status"] = "PASS"
    except SafeError as exc:
        report.update(status="FAIL", error_category=exc.code, file=exc.file, source_line=exc.line)
        report.update(exc.details)
        code = 2
    except Exception as exc:
        report.update(status="FAIL", error_category="SQL_ERROR" if isinstance(exc, psycopg2.Error) else "LOCAL_OPERATION_ERROR",
                      sqlstate=getattr(exc, "pgcode", None))
        code = 3
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    report["exit_code"] = code
    output = ROOT / "results/warehouse" / ("s05_" + args.action + "_" + run_id + ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "action": args.action, "run_id": run_id,
                      "duration_seconds": report["duration_seconds"], "report": str(output.relative_to(ROOT)),
                      **({"error_category": report["error_category"], "sqlstate": report.get("sqlstate")} if code else {})}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
