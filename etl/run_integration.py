"""12A isolated target orchestration. Default dry-run, explicit --apply creates DB.

Reuses guarded ETL/G3 transaction paths; never calls official test evaluator.
"""
import argparse,json,sys,uuid,time,os,subprocess,hashlib,copy
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import quote
import psycopg2
from psycopg2 import sql
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from etl.s05_staging import config,verify_sources,catalog,sha256,SafeError
from etl.integration_target import IntegrationPermit,integration_connect
from etl.run_etl import atomic_refresh,populate,verify_warehouse,model_state
from etl.g3_intake import read_package,check_dw
from etl.g3_transaction import production_transaction,verify_active
from database.backup_restore import fingerprint,acl_ownership
sys.path.insert(0,str(ROOT/'dashboard/restore'))
from common import SupersetAPI,production_objects
sys.path.insert(0,str(ROOT/'dashboard/metadata_restore'))
import importlib.util
spec=importlib.util.spec_from_file_location('metadata_common',ROOT/'dashboard/metadata_restore/common.py');mc=importlib.util.module_from_spec(spec);spec.loader.exec_module(mc)
def save(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(o,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8');os.replace(t,p)
def ordinary(c,dbname,readonly=False):
 x=psycopg2.connect(host=c['POSTGRES_HOST'],port=c['POSTGRES_PORT'],dbname=dbname,user=c['POSTGRES_USER'],password=c['POSTGRES_PASSWORD'],connect_timeout=10,options='-c timezone=UTC')
 if readonly:x.set_session(readonly=True,isolation_level='REPEATABLE READ')
 return x
def protected(c):
 x=ordinary(c,'movielens_btl',True)
 with x:r={'fingerprint':fingerprint(x),'acl':acl_ownership(x)}
 x.close();return r
def engine_checks(api):
 def query(i,filters=None,tr=None):
  ctx=json.loads(api.request('GET',f'/api/v1/chart/{i}')['result']['query_context']);ctx['force']=True
  if filters is not None:ctx['queries'][0]['filters']=filters
  if tr:ctx['queries'][0]['time_range']=tr
  r=api.request('POST','/api/v1/chart/data',ctx)['result'][0];assert r['status']=='success';return r['data']
 overview=[query(1,tr=t)[0]['rating_count'] for t in ['No filter','2000-07-01 : 2000-10-01']];assert overview==[1000209,324864]
 filters=[{'col':'quarter_label','op':'IN','val':['2001 Q1']},{'col':'genre_name','op':'IN','val':['Animation']}];trend=query(13,filters)[0]
 assert trend['rating_count']==1715 and trend['previous_rating_count']==20068 and abs(trend['qoq_pct']+91.45405620888978)<1e-8
 filters=[{'col':'cluster_id','op':'IN','val':[1]},{'col':'age_group','op':'IN','val':['25-34']},{'col':'gender','op':'IN','val':['F']}]
 assigned=query(14,filters)[0]['assigned_users'];baseline=query(16,[])[0]['fixed_assigned_baseline'];insufficient=query(15,[])[0]['insufficient_users'];heat=query(19,filters[:1]);assert assigned==170 and baseline==6038 and insufficient==2 and len(heat)==18
 assert query(14,[])[0]['assigned_users']==6038
 return {'overview':overview,'animation':trend,'assigned_all_filtered':[6038,assigned],'baseline':baseline,'insufficient':insufficient,'heatmap_cluster_only_cells':len(heat),'force_cache_refresh':True}
def cli_checks(c,permit,private,out):
 bi=dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False);env=os.environ.copy();env.update(PGHOST=c['POSTGRES_HOST'],PGPORT=str(c['POSTGRES_PORT']),PGDATABASE=permit.database,PGUSER=bi['POSTGRES_USER'],PGPASSWORD=bi['POSTGRES_PASSWORD'],PGOPTIONS='-c default_transaction_read_only=on -c timezone=UTC')
 result=[]
 for uid,mode in [(4277,'evaluation'),(1,'evaluation'),(398,'demo')]:
  dest=private/f'cli_{mode}_{uid}.json';args=[sys.executable,'-m','mining.recommend','--source','dw','--user-id',str(uid),'--mode',mode,'--top-n','5','--output-json',str(dest)]
  with (private/f'cli_{mode}_{uid}.stdout.log').open('wb') as a,(private/f'cli_{mode}_{uid}.stderr.log').open('wb') as b:p=subprocess.run(args,env=env,stdout=a,stderr=b,cwd=ROOT,timeout=600)
  if p.returncode:raise SafeError('INTEGRATION_CLI_FAILED_'+mode)
  data=json.loads(dest.read_text(encoding='utf-8'));result.append({'mode':mode,'status':'CLI_EXIT_0','private_output_sha256':sha256(dest),'model_version':data.get('model_version'),'official_test_evaluator_called':False})
 return result
def main():
 a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');a.add_argument('--package',type=Path,default=ROOT/'data/processed/p1_g3_20261020_intake');a.add_argument('--date',default='20261023');args=a.parse_args()
 if not args.apply:print(json.dumps({'mode':'DRY_RUN_PLAN','creates_database':False,'source_database_write':False,'required':'--apply after PR24 merge verified'}));return
 rid=uuid.uuid4().hex;c=config(ROOT/'.env');permit=IntegrationPermit('movielens_btl_int_'+args.date+'_'+rid[:8],rid,c['POSTGRES_USER']);out=ROOT/'results/warehouse/s12a'/rid;private=ROOT/'tmp/s12a_private'/rid;private.mkdir(parents=True)
 report={'run_id':rid,'at_utc':datetime.now(timezone.utc).isoformat(),'status':'IN_PROGRESS','target':permit.database,'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'code_state':'WORKING_TREE_NOT_COMMITTED','code_sha256':{p:sha256(ROOT/p) for p in ['etl/run_integration.py','etl/integration_target.py','etl/run_etl.py','etl/g3_intake.py','etl/g3_transaction.py','etl/s06a_dimensions.py','etl/s06b_bridge.py','etl/s06c_fact.py','olap/run_olap.py','database/schema.sql','database/views.sql','mining/data_io.py','mining/recommend.py','mining/cf.py','requirements.txt']},'cycles':[],'p2_intake_g2':'NOT_CONFIRMED','candidate_selected':False}
 save(out/'progress.json',report);start=time.monotonic();source=json.loads((ROOT/'data/source_manifest.json').read_text(encoding='utf-8'));raw=ROOT/'data/raw/ml-1m'
 # Resolve actual local source folder without modifying source or manifests.
 if not (raw/'ratings.dat').exists():
  candidates=list((ROOT/'data/raw').rglob('ratings.dat'));assert len(candidates)==1;raw=candidates[0].parent
 pkg=read_package(args.package);report['package']={'manifest_sha256':pkg.manifest_sha256,'payload_sha256':pkg.payload_sha256,'producer':pkg.manifest['code_provenance'],'model_version':pkg.manifest['model_version']};verify_sources(raw,source)
 original=protected(c);prod=SupersetAPI();prod_objects=production_objects(prod);test=mc.RestoreAPI();save(out/'superset8092_before.json',{'objects':production_objects(test)});save(private/'database_api_before.json',test.request('GET','/api/v1/database/1')['result'])
 maintenance=ordinary(c,'postgres');maintenance.autocommit=True
 try:
  with maintenance.cursor() as q:
   q.execute('SELECT 1 FROM pg_database WHERE datname=%s',(permit.database,));assert q.fetchone() is None,'TARGET_ALREADY_EXISTS'
   q.execute(sql.SQL('CREATE DATABASE {} OWNER {} TEMPLATE template0 ENCODING %s').format(sql.Identifier(permit.database),sql.Identifier(permit.owner)),('UTF8',))
   q.execute(sql.SQL('COMMENT ON DATABASE {} IS %s').format(sql.Identifier(permit.database)),(permit.marker,))
  maintenance.close();save(private/'permit.json',{'database':permit.database,'run_id':rid,'owner':permit.owner})
  x=integration_connect(c,permit);x.autocommit=True
  with x.cursor() as q:q.execute('SELECT set_config(%s,%s,false)',('btl.target_database',permit.database));q.execute((ROOT/'database/schema.sql').read_text(encoding='utf-8'))
  x.close()
  bi=dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False)
  x=integration_connect(c,permit)
  with x:
   with x.cursor() as q:
    q.execute((ROOT/'database/views.sql').read_text(encoding='utf-8'))
    q.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO movielens_bi_reader').format(sql.Identifier(permit.database)))
    q.execute('GRANT USAGE ON SCHEMA dw,analytics TO movielens_bi_reader')
    q.execute('GRANT SELECT ON dw.v_ml_users,dw.v_ml_movies,dw.v_ml_movie_genres,dw.v_ml_ratings,analytics.v_olap_time_rollup,analytics.v_olap_genre_quarter,analytics.v_active_user_cluster,analytics.v_active_cluster_genre_profile TO movielens_bi_reader')
  x.close()
  uri='postgresql+psycopg2://'+quote(bi['POSTGRES_USER'],safe='')+':'+quote(bi['POSTGRES_PASSWORD'],safe='')+'@host.docker.internal:'+str(c['POSTGRES_PORT'])+'/'+permit.database
  test.request('PUT','/api/v1/database/1',{'sqlalchemy_uri':uri})
  for cycle in [1,2]:
   print(json.dumps({'cycle':cycle,'phase':'FULL_REFRESH','target':permit.database}),flush=True);progress={};x=integration_connect(c,permit)
   refreshed=atomic_refresh(x,lambda con:populate(con,raw,source,progress),lambda con:verify_warehouse(con,raw),progress=progress);x.close();save(out/f'cycle{cycle}_etl.json',refreshed)
   x=integration_connect(c,permit,readonly=True)
   with x:checked=check_dw(x,pkg)
   x.close();assert checked['canonical_hashes']==pkg.manifest['canonical_hashes'];save(out/f'cycle{cycle}_dw_before_model.json',checked)
   print(json.dumps({'cycle':cycle,'phase':'ML_DW_CLI'}),flush=True);ml=cli_checks(c,permit,private,out)
   x=integration_connect(c,permit);loaded=production_transaction(x,pkg);x.close();save(out/f'cycle{cycle}_g3.json',loaded)
   x=integration_connect(c,permit,readonly=True)
   with x:
    with x.cursor() as q:verify_active(q,pkg,views=True)
    after=check_dw(x,pkg)
    with x.cursor() as q:q.execute('SELECT registered_at FROM analytics.model_registry WHERE model_version=%s',(pkg.manifest['model_version'],));registered=str(q.fetchone()[0])
   x.close();x=integration_connect(c,permit);noop=production_transaction(x,pkg);x.close();assert noop['transaction']=='COMMITTED_NO_OP'
   print(json.dumps({'cycle':cycle,'phase':'SUPERSET_8092'}),flush=True);bi_result=engine_checks(test)
   record={'cycle':cycle,'etl_transaction':refreshed['transaction'],'etl_model_before':refreshed['model_before'],'etl_model_after':refreshed['model_after'],'g3_plan':loaded['plan'],'g3_transaction':loaded['transaction'],'noop':noop['transaction'],'registered_at':registered,'after_g3':after,'ml_cli':ml,'superset8092':bi_result}
   report['cycles'].append(record);save(out/'progress.json',report)
  assert report['cycles'][0]['registered_at']==report['cycles'][1]['registered_at'];assert protected(c)==original;assert production_objects(prod)==prod_objects
  report.update(status='PASS_WAITING_REVIEW',duration_seconds=round(time.monotonic()-start,3),source_dw_model_acl_preserved=True,production_8089_config_preserved=True,registered_at_preserved_across_refresh_reload=True,official_metric_source='results/mining/cf_test_evaluation_receipt.json',official_metric_receipt_sha256=sha256(ROOT/'results/mining/cf_test_evaluation_receipt.json'),official_test_evaluator_called=False)
  save(out/'summary.json',report);print(json.dumps({'status':report['status'],'run_id':rid,'target':permit.database,'cycles':2}),flush=True)
 except Exception as e:
  report.update(status='FAIL',error_category=e.code if isinstance(e,SafeError) else type(e).__name__,duration_seconds=round(time.monotonic()-start,3));save(out/'FAIL.json',report);raise RuntimeError(report['error_category']) from None
if __name__=='__main__':main()
