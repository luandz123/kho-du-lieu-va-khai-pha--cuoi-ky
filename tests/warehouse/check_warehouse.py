"""Read-only integrated warehouse check; never load or refresh any table.

Usage: python tests/warehouse/check_warehouse.py --env-file .env
The action is fixed to verify; user-supplied load/preflight actions are rejected.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from etl.run_etl import RAW, ROOT, main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    args = parser.parse_args()
    sys.argv = [sys.argv[0], "verify", "--env-file", str(args.env_file), "--raw-dir", str(args.raw_dir)]
    raise SystemExit(main())
