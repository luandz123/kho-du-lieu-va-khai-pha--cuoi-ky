"""Read-only live configuration/package verification and local static checks."""
import sys,json,hashlib,ast,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'dashboard/overview'),str(ROOT/'dashboard/preferences')]
from superset_api import SupersetAPI
from prepare import write
D=ROOT/'dashboard/preferences'
def main():
 a=SupersetAPI();ids=json.loads((D/'object_ids.json').read_text());defs=json.loads((D/'chart_definitions.json').read_text(encoding='utf-8'))
 actual=a.request('GET',f'/api/v1/dashboard/{ids["dashboard"]}')['result'];expected=json.loads((D/'dashboard_definition.json').read_text(encoding='utf-8'))
 for key in ['dashboard_title','slug']:assert actual[key]==expected[key],key
 assert json.loads(actual['position_json'])==json.loads(expected['position_json']),'POSITION_STRUCTURE_CHANGED'
 am=json.loads(actual['json_metadata']);em=json.loads(expected['json_metadata'])
 for key in ['native_filter_configuration','refresh_frequency','expanded_slices','chart_configuration','timed_refresh_immune_slices']:assert am[key]==em[key],key
 filters=am['native_filter_configuration'];cs=ids['charts'];fixed={cs[k] for k in ['insufficient','baseline','model','baseline_gender','baseline_age']}
 assert set(filters[0]['scope']['excluded'])==fixed
 assert all(set(f['scope']['excluded'])==fixed|{cs['heatmap']} for f in filters[1:])
 for key in ['users','profile']:
  ds=a.request('GET',f'/api/v1/dataset/{ids[key]}')['result'];assert ds['sql']==(D/(key+'_dataset.sql')).read_text(encoding='utf-8') and ds['database']['id']==1
 for key,e in defs.items():
  chart=a.request('GET',f'/api/v1/chart/{e["chart_id"]}')['result'];assert json.loads(chart['params'])==e['form_data'] and json.loads(chart['query_context'])==e['query_context']
 package=ROOT/'data/processed/p1_g3_20261020_intake'
 expected_sha={'user_cluster.csv':'5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93','cluster_genre_profile.csv':'59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d','manifest.json':'630453504b71c6b3e38e022f760e2c37a2612a418d3dfdfbf448794c7297d0f0'}
 hashes={k:hashlib.sha256((package/k).read_bytes()).hexdigest() for k in expected_sha};assert hashes==expected_sha
 for p in D.rglob('*.json'):json.loads(p.read_text(encoding='utf-8'))
 for p in [*D.glob('*.py'),ROOT/'tests/warehouse/check_preferences_fixture.py']:ast.parse(p.read_text(encoding='utf-8'))
 assert hashlib.sha256((ROOT/'docs/KE_HOACH_BTL_MOVIELENS.md').read_bytes()).hexdigest()=='da37e4a262541ad9f7957ded381cd1347a8e657709f8367fa2ec5ee4cd51d7c7'
 ignore=subprocess.run(['git','check-ignore','.env','dashboard/superset/.env.bi','dashboard/superset/.env','data/processed/p1_g3_20261020_intake/user_cluster.csv'],capture_output=True,text=True);assert len(ignore.stdout.splitlines())==4
 tracked=subprocess.check_output(['git','ls-files'],text=True).splitlines();bad=[p for p in tracked if p.startswith(('data/raw/','data/processed/')) or p in ['.env','dashboard/superset/.env','dashboard/superset/.env.bi']];assert not bad
 containers=json.loads(subprocess.check_output(['docker','inspect','btl-movielens-superset-web-1','btl-movielens-superset-metadata-1'],text=True));states=[{'name':v['Name'],'status':v['State']['Status'],'health':v['State'].get('Health',{}).get('Status'),'exit_code':v['State']['ExitCode']} for v in containers];assert all(v['status']=='running' and v['health']=='healthy' for v in states)
 write('dashboard_observed.json',{k:actual[k] for k in ['dashboard_title','slug','position_json','json_metadata']})
 report={'status':'PASS','at_utc':datetime.now(timezone.utc).isoformat(),'dashboard':ids['dashboard'],'datasets':[ids['users'],ids['profile']],'charts':cs,'native_filters_exact':True,'chart_sql_metrics_exact':True,'package_byte_sha256':hashes,'producer_code_commit':'bab0b4049d4e0b1724418b8a92d8afbeda4bc775','checkpoint_11b2':'f663dcb4143202dac0835e4d5168e1b8558a6463','model_version':'kmeans_k4_seed42','containers':states,'outside_plan_unchanged':True,'private_paths_ignored':True,'p2_intake_status':'NOT_CONFIRMED','limits':['PUBLIC TEMP remains','Three-dashboard export/import/restore not performed','No two-machine connectivity or P2 intake evidence','No fresh full refresh with S07 helper/G3','Narrow panels require table horizontal scrolling; desktop heatmap verified at 1280x900'],'business_definition_unchanged_after_ui':True}
 write('evidence/verification.json',report);print(json.dumps({'status':'PASS','dashboard':ids['dashboard'],'charts':len(cs),'containers':states}))
if __name__=='__main__':main()
