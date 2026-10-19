"""Final read-only S11A object, grain, baseline and BI-role verification."""
import json,subprocess,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from etl.s05_staging import ROOT,connect,config
from superset_api import SupersetAPI
D=ROOT/'dashboard/overview'
def main():
 s=SupersetAPI();ids=json.loads((D/'object_ids.json').read_text(encoding='utf-8'));r={'at_utc':datetime.now(timezone.utc).isoformat(),'status':'FAIL','objects':{},'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 for key,path in [('database','database/1'),('ratings_dataset','dataset/1'),('catalog_dataset','dataset/2')]:
  d=s.request('GET','/api/v1/'+path)['result']
  if key=='database':r['objects'][key]={k:d.get(k) for k in ['id','database_name','allow_dml','allow_ctas','allow_cvas','allow_file_upload','expose_in_sqllab']}
  else:r['objects'][key]={'id':d['id'],'name':d['table_name'],'main_dttm_col':d.get('main_dttm_col'),'columns':[{k:c.get(k) for k in ['column_name','type','is_dttm']} for c in d['columns']]}
 r['objects']['charts']=[]
 for key,cid in ids['charts'].items():
  d=s.request('GET','/api/v1/chart/'+str(cid))['result'];r['objects']['charts'].append({'key':key,'id':cid,'name':d['slice_name'],'viz_type':d['viz_type'],'datasource_id':d['datasource_id']})
 d=s.request('GET','/api/v1/dashboard/1')['result'];meta=json.loads(d['json_metadata']);r['objects']['dashboard']={'id':d['id'],'title':d['dashboard_title'],'slug':d['slug'],'published':d['published'],'native_filters':meta['native_filter_configuration']}
 metrics=[{'expressionType':'SQL','sqlExpression':expr,'label':label,'hasCustomLabel':True,'optionName':'verify_'+label} for expr,label in [('MAX(current_user::text)','executing_role'),("MAX(current_setting('TimeZone')::text)",'engine_timezone')]]
 actual=s.request('POST','/api/v1/chart/data',{'datasource':{'id':ids['catalog'],'type':'table'},'force':True,'queries':[{'columns':[],'metrics':metrics,'row_limit':1,'is_timeseries':False}],'result_format':'json','result_type':'full'})['result'][0]['data'][0]
 assert actual=={'executing_role':'movielens_bi_reader','engine_timezone':'UTC'};r['actual_superset_engine']=actual
 conn=connect(config(ROOT/'.env'));conn.set_session(readonly=True)
 with conn:
  with conn.cursor() as c:
   c.execute('SELECT count(*) FROM dw.dim_movie');r['independent_dim_movie_count']=c.fetchone()[0];assert r['independent_dim_movie_count']==3883
   c.execute('SELECT rating,count(*) FROM dw.fact_rating GROUP BY rating ORDER BY rating');r['independent_stars']=c.fetchall();assert [n for _,n in r['independent_stars']]==[56174,107557,261197,348971,226310]
   c.execute('SELECT count(*) FROM (SELECT user_id,movie_id,count(*) n FROM dw.v_ml_ratings GROUP BY user_id,movie_id HAVING count(*)<>1) t');r['duplicate_rating_pairs']=c.fetchone()[0];assert r['duplicate_rating_pairs']==0
   c.execute("SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname='movielens_bi_reader')");r['reader_owned_relations']=c.fetchone()[0];assert r['reader_owned_relations']==0
   c.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE CASE WHEN c.relkind='S' AND n.nspname IN ('dw','staging','analytics') THEN has_sequence_privilege('movielens_bi_reader',c.oid,'USAGE,UPDATE') ELSE false END");r['reader_mutable_project_sequences']=c.fetchone()[0];assert r['reader_mutable_project_sequences']==0
   c.execute('SELECT count(*) FROM analytics.model_registry UNION ALL SELECT count(*) FROM analytics.user_cluster UNION ALL SELECT count(*) FROM analytics.cluster_genre_profile');r['analytics_row_counts']=[x[0] for x in c.fetchall()];assert r['analytics_row_counts']==[0,0,0]
 conn.close();r['project_containers']=[]
 for name in ['btl-movielens-superset-web-1','btl-movielens-superset-metadata-1']:
  out=subprocess.check_output(['docker','inspect','--format','{{.Name}}|{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}',name],text=True).strip();r['project_containers'].append(out);assert out.endswith('|running|healthy')
 r.update(status='PASS',readonly_bi_role_verified=True,p2_intake_status='NOT_CONFIRMED',other_instances_modified=False,native_filter_excludes_only_catalog=meta['native_filter_configuration'][0]['scope']['excluded']==[5]);assert r['native_filter_excludes_only_catalog']
 (D/'evidence/final_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':r['status'],'charts':len(r['objects']['charts']),'superset_engine':actual,'catalog':r['independent_dim_movie_count'],'duplicates':r['duplicate_rating_pairs'],'mutable_sequences':r['reader_mutable_project_sequences'],'analytics':r['analytics_row_counts']}))
if __name__=='__main__':main()
