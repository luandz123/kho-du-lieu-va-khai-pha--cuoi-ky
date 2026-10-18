"""Atomic refresh control and publication failures, no real connection."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from etl.s05_staging import SafeError
from etl.run_etl import TARGETS, atomic_json, atomic_refresh, full_refresh, publish, safe_config, scope


class RefreshTests(unittest.TestCase):
    def test_exact_refresh_scope_excludes_registry(self):
        registry, tables = scope()
        self.assertEqual(registry, "analytics.model_registry")
        self.assertEqual(len(tables), 11)
        self.assertNotIn(registry, tables)
        self.assertEqual(set(tables), set(TARGETS))

    def test_fixture_scope_cannot_escape_namespace(self):
        registry, tables = scope("s06d_test_123456789abc")
        self.assertTrue(all(p.startswith("s06d_test_123456789abc.") for p in (*tables, registry)))
        for bad in ["public", "dw", "s06d_test_123456789abc;DROP"]:
            with self.assertRaises(SafeError):
                scope(bad)

    def test_atomic_json_replaces_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            atomic_json(path, {"version": 1})
            atomic_json(path, {"version": 2})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"version": 2})
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_failed_rename_preserves_old_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            atomic_json(path, {"version": 1})
            with patch("etl.run_etl.os.replace", side_effect=OSError("fixture")):
                with self.assertRaises(OSError):
                    atomic_json(path, {"version": 2})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"version": 1})
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_publication_failure_never_claims_db_rollback(self):
        report = {"database_committed": True, "status": "PASS"}
        with patch("etl.run_etl.atomic_json", side_effect=OSError("fixture")):
            self.assertFalse(publish(report, Path("unused.json")))
        self.assertIs(report["database_committed"], True)
        self.assertEqual(report["status"], "DB_COMMITTED_G2_PUBLICATION_FAILED")
        self.assertFalse(report["g2_metadata_published"])

    def test_commit_exception_remains_unverified(self):
        conn = MagicMock()
        conn.closed = False
        conn.__exit__.side_effect = OSError("fixture commit connection loss")
        model = {"active": 0, "valid": 0, "registry_rows": 1, "metadata_except_flags_sha256": "fixture"}
        with patch("etl.run_etl.model_state", return_value=model):
            with self.assertRaises(SafeError) as caught:
                atomic_refresh(conn, lambda c: {}, lambda c: {}, fixture_schema="s06d_test_123456789abc")
        self.assertEqual(caught.exception.details["database_outcome"], "COMMIT_OUTCOME_UNVERIFIED")

    def test_same_connection_and_one_truncate(self):
        conn = MagicMock()
        conn.closed = False
        seen = []
        model = {"active": 0, "valid": 0, "registry_rows": 0, "metadata_except_flags_sha256": "fixture"}
        with patch("etl.run_etl.model_state", return_value=model):
            result = atomic_refresh(conn, lambda c: seen.append(c), lambda c: seen.append(c), fixture_schema="s06d_test_123456789abc")
        self.assertEqual(seen, [conn, conn])
        self.assertEqual(result["truncate_statements"], 1)
        commands = conn.cursor.return_value.__enter__.return_value.execute.call_args_list
        self.assertEqual(sum("TRUNCATE" in str(call) for call in commands), 1)
        self.assertFalse(any("CASCADE" in str(call) or "DROP" in str(call) for call in commands))

    def test_precommit_failure_is_not_commit_success(self):
        conn = MagicMock()
        conn.closed = False
        model = {"active": 0, "valid": 0, "registry_rows": 0, "metadata_except_flags_sha256": "fixture"}
        def reject(c):
            raise SafeError("FIXTURE_CHECKSUM_MISMATCH")
        with patch("etl.run_etl.model_state", return_value=model):
            with self.assertRaises(SafeError) as caught:
                atomic_refresh(conn, lambda c: {}, reject, fixture_schema="s06d_test_123456789abc")
        self.assertEqual(caught.exception.details["database_outcome"], "ROLLED_BACK")

    def test_unknown_commit_reconnects_without_claiming_attribution(self):
        conn = MagicMock()
        err = SafeError("FIXTURE_COMMIT_LOSS")
        err.details = {"database_outcome": "COMMIT_OUTCOME_UNVERIFIED"}
        checked = {"checks": {"canonical_hashes": {"ratings": "fixture"}, "models": {"active": 0}}}
        with patch("etl.run_etl.connect", return_value=conn), patch("etl.run_etl.verify_sources"), patch("etl.run_etl.assert_project"), patch("etl.run_etl.catalog"), patch("etl.run_etl.atomic_refresh", side_effect=err), patch("etl.run_etl.readonly_check", return_value=checked) as reconnect:
            with self.assertRaises(SafeError) as caught:
                full_refresh({}, Path("unused_fixture"))
        reconnect.assert_called_once()
        self.assertEqual(caught.exception.details["database_outcome"], "COMMIT_OUTCOME_UNVERIFIED")
        self.assertTrue(caught.exception.details["reconciliation"]["commit_attribution_still_unverified"])

    def test_safe_config_excludes_credentials(self):
        value = safe_config({"POSTGRES_HOST": "localhost", "POSTGRES_PORT": "5432", "POSTGRES_USER": "invented_user", "POSTGRES_PASSWORD": "invented_secret"})
        text = json.dumps(value)
        self.assertNotIn("invented_secret", text)
        self.assertNotIn("invented_user", text)
        self.assertTrue(value["credentials_excluded"])

    def test_manifest_write_failure_keeps_committed_db_state(self):
        report = {"database_committed": True, "status": "PASS"}
        def write(path, value):
            if str(path) == "manifest.json":
                raise OSError("fixture manifest write failure")
        with patch("etl.run_etl.atomic_json", side_effect=write), patch("etl.run_etl.manifest_for", return_value={}):
            self.assertFalse(publish(report, Path("report.json"), Path("manifest.json")))
        self.assertTrue(report["database_committed"])
        self.assertEqual(report["status"], "DB_COMMITTED_G2_PUBLICATION_FAILED")


if __name__ == "__main__":
    unittest.main()
