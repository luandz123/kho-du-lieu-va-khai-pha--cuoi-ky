"""Production dispatch guards and CLI policy without database writes."""
import unittest,tempfile,json,sys,io,os
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
from etl import g3_transaction as tx
from etl import load_g3 as cli
from etl.g3_intake import VERSION,PINNED,SafeError,read_package,validate_snapshot
from tests.warehouse.test_g3_intake import sample

class DispatcherTests(unittest.TestCase):
    def test_unknown_connection_state_never_claims_rollback(self):
        from unittest.mock import Mock
        c=Mock(closed=False);c.get_transaction_status.return_value=4
        self.assertEqual(tx.database_outcome('PRECOMMIT',c),'UNKNOWN')
        c.get_transaction_status.return_value=0
        self.assertEqual(tx.database_outcome('PRECOMMIT',c),'ROLLED_BACK')
        self.assertEqual(tx.database_outcome('COMMIT_REQUESTED',c),'UNKNOWN')
    def test_production_requires_byte_snapshot(self):
        with self.assertRaises(SafeError) as e:tx.production_transaction(None,sample())
        self.assertEqual(e.exception.code,'PRODUCTION_REQUIRES_VERIFIED_BYTE_SNAPSHOT')
    def test_production_dispatches_shared_core_with_all_checks(self):
        p=sample();p.snapshot={'memory':b'fixture'};p.manifest['model_version']=VERSION;p.payload_sha256=dict(PINNED)
        with patch.object(tx,'validate_snapshot',return_value=p) as v,patch.object(tx,'_transaction',return_value={'fixture':'dispatch-spy'}) as engine:
            result=tx.production_transaction('same-connection',p,expect_empty=True)
        self.assertEqual(result,{'fixture':'dispatch-spy'});v.assert_called_once_with(p.snapshot)
        engine.assert_called_once_with('same-connection',p,schema='analytics',source_schema='dw',production=True,expect_empty=True)
    def test_production_rejects_other_frozen_payload(self):
        p=sample();p.snapshot={};p.manifest['model_version']=VERSION
        with patch.object(tx,'validate_snapshot',return_value=p),patch.object(tx,'_transaction') as engine:
            with self.assertRaises(SafeError):tx.production_transaction(None,p)
        engine.assert_not_called()
    def test_fixture_cannot_target_production(self):
        with self.assertRaises(SafeError):tx.fixture_transaction(None,sample(),schema='analytics')
    def test_cli_default_is_dry_run(self):
        p=sample()
        with tempfile.TemporaryDirectory() as d:
            report=Path(d)/'r.json'
            with patch.object(sys,'argv',['load_g3','--package','synthetic','--report',str(report)]),patch.object(cli,'read_package',return_value=p),patch.object(cli,'config',return_value={}),patch.object(cli,'observe',return_value={'synthetic':True}),patch.object(cli,'dashboard_state',return_value={'same':1}),patch.object(cli,'production_transaction') as write,redirect_stdout(io.StringIO()):self.assertEqual(cli.main(),0)
            self.assertEqual(json.loads(report.read_text())['mode'],'DRY_RUN');write.assert_not_called()
    def test_unknown_reconciles_without_write_retry(self):
        p=sample();err=SafeError('SYNTHETIC_LOST_ACK');err.details={'database_outcome':'UNKNOWN'}
        with tempfile.TemporaryDirectory() as d:
            report=Path(d)/'r.json'
            with patch.object(sys,'argv',['load_g3','--package','synthetic','--apply','--report',str(report)]),patch.object(cli,'read_package',return_value=p),patch.object(cli,'config',return_value={}),patch.object(cli,'connect'),patch.object(cli,'observe',return_value={'synthetic':True}) as read,patch.object(cli,'dashboard_state',return_value={'same':1}),patch.object(cli,'production_transaction',side_effect=err) as write,redirect_stdout(io.StringIO()):self.assertEqual(cli.main(),2)
            r=json.loads(report.read_text());self.assertEqual(r['status'],'UNKNOWN');self.assertFalse(r['write_retry']);self.assertEqual(write.call_count,1);self.assertEqual(read.call_count,2)
    def test_snapshot_does_not_reread_package_directory(self):
        # Actual package is read once, then all file paths can disappear without changing snapshot validation.
        from etl.s05_staging import ROOT
        # An isolated checkout may use the already accepted ignored package
        # via an explicit test-only path; never regenerate or copy it into Git.
        p=read_package(Path(os.environ.get('BTL_G3_TEST_PACKAGE',ROOT/'data/processed/p1_g3_20261020_intake')))
        with patch('pathlib.Path.is_file',side_effect=AssertionError('package reread')):
            q=validate_snapshot(p.snapshot)
        self.assertEqual(q.users,p.users);self.assertEqual(q.profiles,p.profiles)

if __name__=='__main__':unittest.main()
