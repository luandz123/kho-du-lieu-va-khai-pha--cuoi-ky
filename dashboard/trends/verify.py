"""Final read-only SQL/API/config/privilege checks, never rebuild the dashboard."""
import json,sys,subprocess,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'dashboard/overview'))
from etl.s05_staging import connect,config,sha256
from superset_api import SupersetAPI
D=ROOT/'dashboard/trends'
def main():
 api=SupersetAPI();ids=json.loads((D/'object_ids.json').read_text());r={'status':'FAIL','at_utc':datetime.now(timezone.utc).isoformat(),'objects':ids}
 for key in ['quarter','genre']:
  a=api.request('GET',f'/api/v1/dataset/{ids[key]}')['result'];assert a['sql'].strip()==(D/(key+'_dataset.sql')).read_text(encoding='utf-8').strip()
 a=api.request('GET',f'/api/v1/dashboard/{ids["dashboard"]}')['result'];expected=json.loads((D/'dashboard_definition.json').read_text(encoding='utf-8'))
 assert json.loads(a['position_json'])==json.loads(expected['position_json'])
 em=json.loads(expected['json_metadata']);am=json.loads(a['json_metadata'])
 auto_color_keys={'color_scheme_domain','shared_label_colors','map_label_colors','label_colors'}
 assert {k:v for k,v in am.items() if k not in auto_color_keys}=={k:v for k,v in em.items() if k not in auto_color_keys}
 r['superset_generated_color_metadata']={k:am.get(k) for k in auto_color_keys}
 (D/'dashboard_observed.json').write_text(json.dumps({k:a.get(k) for k in expected},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 meta=json.loads(a['json_metadata']);filters=meta['native_filter_configuration'];assert len(filters)==2 and all(f['filterType']=='filter_select' for f in filters)
 assert filters[0]['targets'][0]['column']['name']=='quarter_label' and filters[0]['scope']['excluded']==[]
 assert filters[1]['scope']['excluded']==[ids['charts']['system']]
 r['native_filters']=filters
 metrics=[{'expressionType':'SQL','sqlExpression':expr,'label':label,'hasCustomLabel':True,'optionName':'verify_'+label} for expr,label in [('MAX(current_user::text)','executing_role'),("MAX(current_setting('TimeZone')::text)",'engine_timezone')]]
 engine=api.request('POST','/api/v1/chart/data',{'datasource':{'id':ids['quarter'],'type':'table'},'force':True,'queries':[{'columns':[],'metrics':metrics,'row_limit':1,'is_timeseries':False}],'result_format':'json','result_type':'full'})['result'][0]['data'][0]
 assert engine=={'executing_role':'movielens_bi_reader','engine_timezone':'UTC'};r['actual_superset_engine']=engine
 c=connect(config(ROOT/'.env'));c.set_session(readonly=True)
 with c:
  with c.cursor() as q:
   q.execute("SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname='movielens_bi_reader')");r['reader_owned_relations']=q.fetchone()[0];assert r['reader_owned_relations']==0
   q.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE CASE WHEN c.relkind='S' AND n.nspname IN ('dw','staging','analytics') THEN has_sequence_privilege('movielens_bi_reader',c.oid,'USAGE,UPDATE') ELSE false END");r['mutable_project_sequences']=q.fetchone()[0];assert r['mutable_project_sequences']==0
   q.execute("SELECT schema_name,has_schema_privilege('movielens_bi_reader',schema_name,'USAGE') FROM information_schema.schemata WHERE schema_name IN ('dw','analytics') ORDER BY 1");r['schema_usage']=dict(q.fetchall());assert all(r['schema_usage'].values())
   q.execute("SELECT count(*) FROM analytics.v_olap_genre_quarter WHERE is_boundary_partial AND eligible_for_ranking");assert q.fetchone()[0]==0
   q.execute("SELECT sum(rating_count),sum(rating_sum) FROM analytics.v_olap_time_rollup WHERE time_level='quarter'");assert q.fetchone()==(1000209,3582313)
 c.close();r['containers']=[]
 for name in ['btl-movielens-superset-web-1','btl-movielens-superset-metadata-1']:
  state=subprocess.check_output(['docker','inspect','--format','{{.Name}}|{{.State.Status}}|{{.State.Health.Status}}|{{.State.ExitCode}}',name],text=True).strip();assert state.endswith('|running|healthy|0');r['containers'].append(state)
 protected=['database/schema.sql','database/views.sql','docs/shared/data_contract.md','docs/shared/data_contract.json']
 r['protected_files']={}
 for p in protected:
  blob=subprocess.check_output(['git','show','origin/main:'+p]);local=(ROOT/p).read_bytes();assert blob.replace(b'\r\n',b'\n')==local.replace(b'\r\n',b'\n');r['protected_files'][p]=sha256(ROOT/p)
 assert sha256(ROOT/'docs/KE_HOACH_BTL_MOVIELENS.md')=='da37e4a262541ad9f7957ded381cd1347a8e657709f8367fa2ec5ee4cd51d7c7'
 r.update(status='PASS',dedicated_bi_reader_verified=True,p2_intake_status='NOT_CONFIRMED',public_temp_remains=True,full_refresh_with_s07_helper_verified=False,import_restore_verified=False,code_sha256=sha256(Path(__file__)))
 (D/'evidence/final_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','engine':engine,'protected_files_unchanged':len(protected),'containers':r['containers']}))
if __name__=='__main__':main()
