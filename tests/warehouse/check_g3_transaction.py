"""Integration fixtures only; owned marked schema, actual analytics never written."""
import unittest,uuid,json,hashlib,sys
from unittest.mock import patch
from pathlib import Path
from datetime import datetime,timezone
from psycopg2 import sql
from etl.s05_staging import ROOT,connect,config,sha256
from etl.g3_intake import SafeError
from etl.g3_transaction import fixture_transaction
from etl import g3_transaction as transaction_module
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_g3_intake import sample

class TransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema='p1_g3_fixture_'+uuid.uuid4().hex;cls.c=connect(config(ROOT/'.env'))
        with cls.c:
            with cls.c.cursor() as q:
                q.execute('SELECT count(*) FROM analytics.model_registry UNION ALL SELECT count(*) FROM analytics.user_cluster UNION ALL SELECT count(*) FROM analytics.cluster_genre_profile');cls.prod_before=[r[0] for r in q.fetchall()];assert cls.prod_before==[0,0,0]
                s=sql.Identifier(cls.schema);q.execute(sql.SQL('CREATE SCHEMA {}').format(s));q.execute(sql.SQL("COMMENT ON SCHEMA {} IS 'BTL P1 G3 disposable synthetic fixture'").format(s))
                q.execute(sql.SQL('CREATE TABLE {}.dim_user(user_id integer PRIMARY KEY); CREATE TABLE {}.dim_genre(genre_name text PRIMARY KEY)').format(s,s))
                q.execute(sql.SQL('INSERT INTO {}.dim_user VALUES(10),(20),(30); INSERT INTO {}.dim_genre VALUES(\'Action\'),(\'Comedy\')').format(s,s))
                for table in ['model_registry','user_cluster','cluster_genre_profile']:
                    q.execute(sql.SQL('CREATE TABLE {} (LIKE {} INCLUDING ALL)').format(sql.Identifier(cls.schema,table),sql.Identifier('analytics',table)))
                q.execute(sql.SQL('ALTER TABLE {}.user_cluster ADD FOREIGN KEY(model_version) REFERENCES {}.model_registry(model_version),ADD FOREIGN KEY(user_id) REFERENCES {}.dim_user(user_id)').format(s,s,s))
                q.execute(sql.SQL('ALTER TABLE {}.cluster_genre_profile ADD FOREIGN KEY(model_version) REFERENCES {}.model_registry(model_version),ADD FOREIGN KEY(genre_name) REFERENCES {}.dim_genre(genre_name)').format(s,s,s))
    def setUp(self):
        with self.c:
            with self.c.cursor() as q:q.execute(sql.SQL('TRUNCATE {},{},{}').format(*(sql.Identifier(self.schema,t) for t in ['user_cluster','cluster_genre_profile','model_registry'])))
        fixture_transaction(self.c,sample('fixture-old'),schema=self.schema)
    def snapshot(self):
        rows=[]
        with self.c:
            with self.c.cursor() as q:
                for table in ['model_registry','user_cluster','cluster_genre_profile']:
                    q.execute(sql.SQL('SELECT to_jsonb(t) FROM {} t ORDER BY to_jsonb(t)::text').format(sql.Identifier(self.schema,table)));rows.append(q.fetchall())
        return hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()
    def test_activate_only_after_complete(self):
        r=fixture_transaction(self.c,sample(),schema=self.schema);self.assertEqual(r['transaction'],'COMMITTED_FIXTURE_ONLY')
        with self.c:
            with self.c.cursor() as q:
                q.execute(sql.SQL('SELECT model_version FROM {} WHERE is_active AND is_valid_for_dw').format(sql.Identifier(self.schema,'model_registry')));self.assertEqual(q.fetchall(),[('fixture-v1',)])
    def test_rerun_is_noop(self):
        pkg=sample();fixture_transaction(self.c,pkg,schema=self.schema);before=self.snapshot();r=fixture_transaction(self.c,pkg,schema=self.schema)
        self.assertEqual(r['transaction'],'COMMITTED_NO_OP');self.assertEqual(before,self.snapshot())
    def test_changed_same_version_rejected(self):
        pkg=sample('fixture-old');pkg.payload_sha256['user_cluster.csv']='0'*64;before=self.snapshot()
        with self.assertRaises(SafeError) as e:fixture_transaction(self.c,pkg,schema=self.schema)
        self.assertEqual(e.exception.code,'VERSION_PAYLOAD_CONFLICT');self.assertEqual(before,self.snapshot())
    def test_rollback_restores_prior_snapshot_and_active_model(self):
        for phase in ['registry','users','profiles','activate']:
            with self.subTest(phase=phase):
                before=self.snapshot()
                with self.assertRaises(SafeError) as e:fixture_transaction(self.c,sample(),schema=self.schema,fail_after=phase)
                self.assertEqual(e.exception.code,'FIXTURE_INJECTED_FAILURE');self.assertEqual(before,self.snapshot())
    def test_invalidated_identical_reload(self):
        pkg=sample('fixture-old')
        with self.c:
            with self.c.cursor() as q:
                for table in ['user_cluster','cluster_genre_profile']:q.execute(sql.SQL('DELETE FROM {}').format(sql.Identifier(self.schema,table)))
                q.execute(sql.SQL('UPDATE {} SET is_active=false,is_valid_for_dw=false').format(sql.Identifier(self.schema,'model_registry')))
        r=fixture_transaction(self.c,pkg,schema=self.schema);self.assertEqual(r['plan'],'RELOAD_IDENTICAL_INVALIDATED_VERSION')
    def test_production_check_runs_before_insert_same_connection(self):
        before=self.snapshot()
        def reject(actual_conn,pkg):
            self.assertIs(actual_conn,self.c)
            with actual_conn.cursor() as q:
                q.execute('SELECT pg_backend_pid()');self.assertIsInstance(q.fetchone()[0],int)
            raise SafeError('FIXTURE_CANONICAL_CHECK_REJECTED')
        with patch.object(transaction_module,'SOURCE_TABLES',{self.schema+'.dim_user':'user_id',self.schema+'.dim_genre':'genre_name'}),patch.object(transaction_module,'check_dw',side_effect=reject) as checked:
            with self.assertRaises(SafeError) as e:transaction_module._transaction(self.c,sample(),schema=self.schema,source_schema=self.schema,production=True)
        self.assertEqual(e.exception.code,'FIXTURE_CANONICAL_CHECK_REJECTED');self.assertEqual(e.exception.details['database_outcome'],'ROLLED_BACK');self.assertEqual(checked.call_count,1);self.assertEqual(before,self.snapshot())
    def test_commit_ack_loss_is_unknown_not_rollback(self):
        with self.assertRaises(SafeError) as e:fixture_transaction(self.c,sample(),schema=self.schema,fail_after='commit_ack')
        self.assertEqual(e.exception.details['database_outcome'],'UNKNOWN')
        # Only a fresh READ ONLY connection observes the committed fixture state.
        c=connect(config(ROOT/'.env'));c.set_session(readonly=True)
        try:
            with c:
                with c.cursor() as q:
                    q.execute(sql.SQL('SELECT model_version FROM {} WHERE is_active AND is_valid_for_dw').format(sql.Identifier(self.schema,'model_registry')));self.assertEqual(q.fetchall(),[('fixture-v1',)])
        finally:c.close()
    def test_unexpected_nonempty_production_precondition_rejected(self):
        before=self.snapshot()
        with patch.object(transaction_module,'SOURCE_TABLES',{self.schema+'.dim_user':'user_id',self.schema+'.dim_genre':'genre_name'}),patch.object(transaction_module,'check_dw',return_value={'analytics_counts':{'model_registry':1}}):
            with self.assertRaises(SafeError) as e:transaction_module._transaction(self.c,sample(),schema=self.schema,source_schema=self.schema,production=True,expect_empty=True)
        self.assertEqual(e.exception.code,'EXPECTED_EMPTY_ANALYTICS_CHANGED');self.assertEqual(before,self.snapshot())
    @classmethod
    def tearDownClass(cls):
        with cls.c:
            with cls.c.cursor() as q:
                q.execute('SELECT count(*) FROM analytics.model_registry UNION ALL SELECT count(*) FROM analytics.user_cluster UNION ALL SELECT count(*) FROM analytics.cluster_genre_profile');assert [r[0] for r in q.fetchall()]==cls.prod_before
                q.execute("SELECT obj_description(oid,'pg_namespace'),nspowner=(SELECT oid FROM pg_roles WHERE rolname=current_user) FROM pg_namespace WHERE nspname=%s",(cls.schema,));assert q.fetchone()==('BTL P1 G3 disposable synthetic fixture',True)
                q.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(cls.schema)))
        cls.c.close()

def main():
    suite=unittest.TestLoader().loadTestsFromTestCase(TransactionTests);result=unittest.TextTestRunner(verbosity=2).run(suite)
    r={'at_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'schema':getattr(TransactionTests,'schema',None),'production_analytics_before':getattr(TransactionTests,'prod_before',None),'synthetic_only':True,'rollback_phases':['registry','users','profiles','activate'],'code_sha256':{n:sha256(ROOT/n) for n in ['etl/g3_transaction.py','tests/warehouse/check_g3_transaction.py']}}
    c=connect(config(ROOT/'.env'));c.set_session(readonly=True)
    with c:
        with c.cursor() as q:
            q.execute('SELECT count(*) FROM analytics.model_registry UNION ALL SELECT count(*) FROM analytics.user_cluster UNION ALL SELECT count(*) FROM analytics.cluster_genre_profile');r['production_analytics_after']=[x[0] for x in q.fetchall()]
            q.execute('SELECT count(*) FROM pg_namespace WHERE nspname=%s',(r['schema'],));r['fixture_removed']=q.fetchone()[0]==0
    c.close();require_ok=result.wasSuccessful() and r['production_analytics_after']==[0,0,0] and r['fixture_removed'];r['status']='PASS' if require_ok else 'FAIL'
    r.update(shared_engine_production_check_exercised=True,commit_ack_loss_unknown_checked=True)
    out=ROOT/('results/warehouse/s11b2/fixture_'+uuid.uuid4().hex+'.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(str(out));return 0 if require_ok else 2
if __name__=='__main__':raise SystemExit(main())
