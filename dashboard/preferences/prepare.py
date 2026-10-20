"""Preserve existing business objects and model; narrowly extend BI view SELECT."""
import json,sys,subprocess,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'dashboard/overview')]
from superset_api import SupersetAPI
from etl.s05_staging import connect,config
D=ROOT/'dashboard/preferences'
def write(name,obj):
 (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def objects(api):
 result={}
 for kind,ids,fields in [('dashboard',[1,2],['dashboard_title','position_json','json_metadata','css','slug']),('dataset',range(1,5),['sql','metrics','columns','main_dttm_col']),('chart',range(1,14),['params','query_context','dashboards','slice_name','viz_type'])]:
  for i in ids:
   r=api.request('GET',f'/api/v1/{kind}/{i}')['result'];result[f'{kind}/{i}']={k:r.get(k) for k in fields}
 return result
def model_snapshot():
 c=connect(config(ROOT/'.env'));c.set_session(readonly=True,isolation_level='REPEATABLE READ');out={}
 with c:
  with c.cursor() as q:
   q.execute('SELECT row_to_json(r) FROM analytics.model_registry r ORDER BY model_version');out['registry']=[r[0] for r in q.fetchall()]
   for table,order in [('analytics.user_cluster','model_version,user_id'),('analytics.cluster_genre_profile','model_version,cluster_id,genre_name')]:
    q.execute(f'SELECT count(*),md5(string_agg(row_to_json(t)::text,chr(10) ORDER BY {order})) FROM {table} t');out[table]=list(q.fetchone())
   for table,order in [('staging.users_raw','source_line'),('staging.movies_raw','source_line'),('staging.ratings_raw','source_line'),('dw.dim_user','user_key'),('dw.dim_movie','movie_key'),('dw.dim_date','date_key'),('dw.dim_genre','genre_key'),('dw.bridge_movie_genre','movie_key,genre_key'),('dw.fact_rating','rating_key')]:
    q.execute(f'SELECT count(*),md5(string_agg(row_to_json(t)::text,chr(10) ORDER BY {order})) FROM {table} t');out[table]=list(q.fetchone())
 c.close();return out
def main():
 (D/'evidence').mkdir(parents=True,exist_ok=True)
 assert not (D/'evidence/before.json').exists(),'DO_NOT_OVERWRITE_BASELINE'
 a=SupersetAPI();before={'objects':objects(a),'database':model_snapshot(),'at_utc':datetime.now(timezone.utc).isoformat()};write('evidence/before.json',before)
 c=connect(config(ROOT/'.env'))
 with c:
  with c.cursor() as q:
   q.execute("SELECT current_database(),shobj_description(oid,'pg_authid') FROM pg_roles WHERE rolname='movielens_bi_reader'");r=q.fetchone();assert r[0]=='movielens_btl' and 'P1 S11A managed' in r[1]
   q.execute((D/'bi_grants.sql').read_text())
 c.close()
 from check_bi_reader import PAYLOAD
 from dotenv import dotenv_values
 expected=['analytics.v_active_cluster_genre_profile','analytics.v_active_user_cluster','analytics.v_olap_genre_quarter','analytics.v_olap_time_rollup','dw.v_ml_movies','dw.v_ml_ratings','dw.v_ml_users']
 payload=PAYLOAD.replace("r['selectable']==['dw.v_ml_movies','dw.v_ml_ratings']",f"r['selectable']=={expected!r}").replace('btl_s11a_reader_check','btl_s11b3_reader_check')
 p=subprocess.run(['docker','exec','-i','btl-movielens-superset-web-1','python','-c',payload],input=json.dumps(dict(dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False))),capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError('BI_CONTAINER_AUDIT_FAILED')
 result=json.loads(p.stdout);result.update(grant_sql=(D/'bi_grants.sql').read_text(),at_utc=datetime.now(timezone.utc).isoformat(),p2_intake_status='NOT_CONFIRMED');write('evidence/bi_reader.json',result)
 print(json.dumps({'status':'PASS','selectable':result['selectable'],'writeable':result['writeable']}))
if __name__=='__main__':main()
