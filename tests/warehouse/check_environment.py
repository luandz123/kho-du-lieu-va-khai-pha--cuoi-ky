"""Read-only environment/SQL check; never print connection strings or raw exceptions."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "SQLAlchemy": "sqlalchemy",
    "psycopg2-binary": "psycopg2",
    "python-dotenv": "dotenv",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", action="store_true")
    parser.add_argument("--env-file", type=Path, help="Explicit local configuration file")
    parser.add_argument("--report", type=Path, help="Report inside results/warehouse only")
    args = parser.parse_args()
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "base_prefix": sys.base_prefix,
        "venv_correct": Path(sys.prefix).resolve() == (ROOT / ".venv").resolve(),
        "python_312": sys.version_info[:2] == (3, 12),
        "dependencies": {},
        "database": "NOT_REQUESTED",
    }
    ok = report["venv_correct"] and report["python_312"]
    for distribution, module in PACKAGES.items():
        try:
            importlib.import_module(module)
            report["dependencies"][distribution] = {
                "version": importlib.metadata.version(distribution), "import": "PASS"
            }
        except Exception:
            report["dependencies"][distribution] = {"import": "FAIL"}
            ok = False
    code = 0 if ok else 1
    if args.db and ok:
        import psycopg2
        from dotenv import dotenv_values

        # Explicit file values only: do not inherit unrelated PGPASSWORD/.pgpass defaults.
        config = dotenv_values(args.env_file, interpolate=False) if args.env_file else {}
        required = ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
        missing = [key for key in required if not config.get(key)]
        if missing:
            report["database"] = "WAITING_LOCAL_CONFIG"
            report["missing_variable_names"] = missing
            code = 2
        else:
            try:
                port = int(config["POSTGRES_PORT"])
                if not 1 <= port <= 65535:
                    raise ValueError("invalid port")
                with psycopg2.connect(
                    host=config["POSTGRES_HOST"], port=port,
                    dbname=config["POSTGRES_DB"], user=config["POSTGRES_USER"],
                    password=config["POSTGRES_PASSWORD"], connect_timeout=5,
                    application_name="btl_p1_setup_check",
                    options="-c default_transaction_read_only=on -c statement_timeout=5000",
                ) as conn:
                    conn.set_session(readonly=True)
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1, current_setting('server_version')")
                        value, version = cursor.fetchone()
                        report["database"] = "SELECT_1_PASS" if value == 1 else "FAIL"
                        report["server_version"] = version
                        if value != 1:
                            code = 3
            except Exception as exc:
                report["database"] = "CONNECTION_FAILED"
                report["sqlstate"] = getattr(exc, "pgcode", None)
                message = str(exc).lower()  # Inspect in memory only, never serialize raw text.
                categories = (
                    ("password authentication failed", "AUTHENTICATION_FAILED"),
                    ("does not exist", "DATABASE_OR_ROLE_NOT_FOUND"),
                    ("no pg_hba.conf entry", "ACCESS_RULE_REJECTED"),
                    ("connection refused", "CONNECTION_REFUSED"),
                    ("timeout", "CONNECTION_TIMEOUT"),
                    ("invalid port", "INVALID_PORT"),
                )
                report["error_category"] = next((label for pattern, label in categories if pattern in message), "CONNECTION_ERROR")
                code = 3
    report["exit_code"] = code
    if args.report:
        target = args.report.resolve()
        target.relative_to((ROOT / "results" / "warehouse").resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
