"""Fresh READ ONLY integration/production checks; no loader, ETL or evaluator."""
import argparse,json,sys,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from etl.run_integration import ordinary,protected,save,engine_checks,mc
from etl.s05_staging import config,assert_project,SafeError,sha256
from etl.integration_target import IntegrationPermit,integration_connect
from etl.g3_intake import read_package,check_dw
from etl.g3_transaction import verify_active
from database.backup_restore import fingerprint
from dotenv import dotenv_values
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();out=ROOT/'results/warehouse/s12a'/a.run;r=json.loads((out/'summary.json').read_text(encoding='utf-8'));assert r['status']=='PASS_WAITING_REVIEW'
 private=ROOT/'tmp/s12a_private'/a.run;permit=IntegrationPermit(**json.loads((private/'permit.json').read_text()));c=config(ROOT/'.env');pkg=read_package(ROOT/'data/processed/p1_g3_20261020_intake')
 x=integration_connect(c,permit,readonly=True)
 with x:
  checked=check_dw(x,pkg)
  with x.cursor() as q:verify_active(q,pkg,views=True)
 x.close();ordinary_target=ordinary(c,permit.database,True)
 try:
  with ordinary_target:assert_project(ordinary_target)
  raise AssertionError('PRODUCTION_GUARD_ACCEPTED_INTEGRATION_DATABASE')
 except SafeError as e:assert e.code=='UNVERIFIED_PROJECT_DATABASE'
 finally:ordinary_target.close()
 # Source has never been refreshed since the accepted backup snapshot.
 old=json.loads((ROOT/'results/warehouse/s12a_prep/backup_restore_2856ed49e9ba494090e2acae73b41b9a.json').read_text(encoding='utf-8'));src=ordinary(c,'movielens_btl',True)
 with src:assert fingerprint(src)==old['source_before']
 src.close()
 bi=dict(dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False));b=ordinary({**c,'POSTGRES_USER':bi['POSTGRES_USER'],'POSTGRES_PASSWORD':bi['POSTGRES_PASSWORD']},permit.database,True)
 with b:
  with b.cursor() as q:
   q.execute("SELECT current_database(),current_user,current_setting('transaction_read_only')");identity=q.fetchone();assert identity==(permit.database,'movielens_bi_reader','on')
   q.execute("SELECT n.nspname||'.'||t.relname,has_table_privilege(current_user,t.oid,'SELECT'),has_table_privilege(current_user,t.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') FROM pg_class t JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname IN ('staging','dw','analytics') AND t.relkind IN ('r','v') ORDER BY 1");permissions=q.fetchall();assert not any(w for n,s,w in permissions)
   q.execute("SELECT has_database_privilege(current_user,current_database(),'CREATE')");assert q.fetchone()==(False,)
 b.close();cli_audit=[]
 b=ordinary({**c,'POSTGRES_USER':bi['POSTGRES_USER'],'POSTGRES_PASSWORD':bi['POSTGRES_PASSWORD']},permit.database,True)
 with b:
  for cycle,folder in [(1,private/'cycle1_preserved'),(2,private)]:
   for index,(uid,mode) in enumerate([(4277,'evaluation'),(1,'evaluation'),(398,'demo')]):
    f=folder/f'cli_{mode}_{uid}.json';data=json.loads(f.read_text(encoding='utf-8'))
    assert sha256(f)==r['cycles'][cycle-1]['ml_cli'][index]['private_output_sha256']
    assert data['mode']==mode and data['top_n']==5 and len(data['recommendations'])==5
    mids=[v['movie_id'] for v in data['recommendations']];assert len(set(mids))==5
    cutoff=976422051 if mode=='evaluation' else 2**63-1
    assert data['model_version']==('item_based_cf_k40_eval_v1' if mode=='evaluation' else 'item_based_cf_k40_DEMO_full_history_v1')
    with b.cursor() as q:
     q.execute('SELECT count(*),count(*) FILTER(WHERE rating>=4) FROM dw.v_ml_ratings WHERE user_id=%s AND timestamp<=%s',(uid,cutoff));history,seeds=q.fetchone();assert history==data['history_count'] and seeds==data['seeds_count']
     q.execute('SELECT count(*) FROM dw.v_ml_ratings WHERE user_id=%s AND timestamp<=%s AND movie_id=ANY(%s)',(uid,cutoff,mids));assert q.fetchone()==(0,)
     for seed in data['seeds']:
      assert seed['rating']>=4
      q.execute('SELECT count(*) FROM dw.v_ml_ratings WHERE user_id=%s AND movie_id=%s AND rating=%s AND timestamp<=%s',(uid,seed['movie_id'],seed['rating'],cutoff));assert q.fetchone()==(1,)
    cli_audit.append({'cycle':cycle,'mode':mode,'private_output_matches_runtime_hash':True,'history_seed_cutoff_verified_by_dw_sql':True,'recommendations_unique_unseen':True,'recommendation_count':5,'score_types':sorted({v['score_type'] for v in data['recommendations']}),'official_test_metrics_measured':False})
 b.close()
 api=mc.RestoreAPI();ctx=json.loads(api.request('GET','/api/v1/chart/16')['result']['query_context']);ctx['force']=True;ctx['queries'][0]['filters']=[]
 ctx['queries'][0]['metrics']=[{'expressionType':'SQL','sqlExpression':expression,'label':name,'hasCustomLabel':True,'optionName':name} for name,expression in [('database','MAX(current_database()::text)'),('role','MAX(current_user::text)'),('timezone',"MAX(current_setting('TimeZone')::text)")]]
 engine=api.request('POST','/api/v1/chart/data',ctx)['result'][0];assert engine['status']=='success';engine=engine['data'][0]
 assert engine=={'database':permit.database,'role':'movielens_bi_reader','timezone':'UTC'}
 for n,h in r['code_sha256'].items():assert sha256(ROOT/n)==h,'RUNTIME_CODE_CHANGED'
 result={'at_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_READ_ONLY','run_id':a.run,'target':permit.database,'canonical_and_model':checked,'ordinary_production_guard_rejects_integration_db':True,'production_source_fingerprint_matches_accepted_backup':True,'bi_identity':identity,'superset8092_actual_engine':engine,'bi_selectable':[n for n,s,w in permissions if s],'bi_writeable':[],'cli_sql_audit':cli_audit,'runtime_code_bytes_unchanged':True,'p2_intake_g2':'NOT_CONFIRMED','candidate_selected':False}
 save(out/'postflight.json',result);print(json.dumps({'status':'PASS_READ_ONLY','target':permit.database,'production_guard_unchanged':True,'bi_writeable':[]}))
if __name__=='__main__':main()
