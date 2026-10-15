"""Check the existing project instance without logging secrets or creating DW objects."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = "btl-movielens-superset-web-1"

# The subprocess receives credentials only via stdin, never argv or printed output.
CONTAINER_CHECK = r'''
import json, sys, socket, importlib.metadata as m
import psycopg2
c = json.load(sys.stdin)
r = {"superset_version": m.version("apache-superset"),
     "postgresql_driver": m.version("psycopg2-binary")}
try:
    with socket.create_connection(("host.docker.internal", 5432), 5):
        r["windows_postgresql_tcp"] = "PASS"
except Exception:
    r["windows_postgresql_tcp"] = "FAIL"
r["host_sql"] = "WAITING_LOCAL_CONFIG"
r["dw_views"] = "NOT_VERIFIED"
if c:
    try:
        host = c["POSTGRES_HOST"]
        if host in ("localhost", "127.0.0.1", "::1"):
            host = "host.docker.internal"
        with psycopg2.connect(host=host, port=int(c["POSTGRES_PORT"]),
            dbname=c["POSTGRES_DB"], user=c["POSTGRES_USER"],
            password=c["POSTGRES_PASSWORD"], connect_timeout=5,
            application_name="btl_p1_container_check",
            options="-c default_transaction_read_only=on -c statement_timeout=5000") as conn:
            conn.set_session(readonly=True)
            with conn.cursor() as cur:
                cur.execute("SELECT 1, current_setting('server_version')")
                value, version = cur.fetchone()
                r["host_sql"] = "SELECT_1_PASS" if value == 1 else "FAIL"
                r["host_server_version"] = version
                views = ["dw.v_ml_users", "dw.v_ml_movies", "dw.v_ml_movie_genres", "dw.v_ml_ratings"]
                states = {}
                for view in views:
                    cur.execute("SELECT to_regclass(%s)", (view,))
                    relation = cur.fetchone()[0]
                    if relation is None:
                        states[view] = "NOT_CREATED"
                    else:
                        cur.execute("SELECT has_table_privilege(current_user, %s, 'SELECT')", (view,))
                        states[view] = "SELECT_PRIVILEGE" if cur.fetchone()[0] else "NO_SELECT_PRIVILEGE"
                r["dw_views"] = states
        # This is a connection probe, not proof that a dedicated read-only BI role exists.
        r["dedicated_dw_read_role_verified"] = False
    except Exception as exc:
        r["host_sql"] = "CONNECTION_FAILED"
        r["sqlstate"] = getattr(exc, "pgcode", None)
        message = str(exc).lower()
        categories = [("password authentication failed", "AUTHENTICATION_FAILED"),
                      ("does not exist", "DATABASE_OR_ROLE_NOT_FOUND"),
                      ("no pg_hba.conf entry", "ACCESS_RULE_REJECTED"),
                      ("connection refused", "CONNECTION_REFUSED"),
                      ("timeout", "CONNECTION_TIMEOUT")]
        r["error_category"] = next((label for pattern, label in categories if pattern in message), "CONNECTION_ERROR")
print(json.dumps(r))
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, help="Explicit local host SQL configuration")
    args = parser.parse_args()
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat()}
    for path in ("health", "login/"):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8089/" + path, timeout=10) as response:
                report[path] = response.status
        except Exception:
            report[path] = "HTTP_FAILED"
    config = {}
    if args.env_file:
        from dotenv import dotenv_values

        values = dotenv_values(args.env_file, interpolate=False)
        required = ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
        if all(values.get(key) for key in required):
            config = {key: values[key] for key in required}
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", CONTAINER, "python", "-c", CONTAINER_CHECK],
            input=json.dumps(config), text=True, capture_output=True, timeout=30,
        )
        report["container"] = json.loads(result.stdout) if result.returncode == 0 else {"status": "CHECK_FAILED"}
    except Exception:
        report["container"] = {"status": "CHECK_FAILED"}
    report["user_ui_login_verified"] = False
    report["dashboard_created"] = False
    report["service_exit_code"] = 0 if report.get("health") == 200 and report.get("login/") == 200 and report["container"].get("superset_version") == "6.1.0" else 1
    sql = report["container"].get("host_sql")
    report["exit_code"] = report["service_exit_code"] or (0 if sql == "SELECT_1_PASS" else 2 if sql == "WAITING_LOCAL_CONFIG" else 3)
    target = ROOT / "results" / "warehouse" / "superset_environment_check.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
