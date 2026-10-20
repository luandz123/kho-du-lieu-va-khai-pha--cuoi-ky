"""Final read-only isolation, BI privileges, production preservation and UI evidence."""
import subprocess,json,hashlib,sys,copy
from datetime import datetime,timezone
from dotenv import dotenv_values
from common import ROOT,D,SupersetAPI,RestoreAPI,production_objects,write
from publication_policy import zip_state
sys.path.insert(0,str(ROOT/'dashboard/preferences'))
from prepare import model_snapshot
PAYLOAD=r'''import json,sys,psycopg2
c=json.load(sys.stdin);conn=psycopg2.connect(host=c['POSTGRES_HOST'],port=c['POSTGRES_PORT'],dbname=c['POSTGRES_DB'],user=c['POSTGRES_USER'],password=c['POSTGRES_PASSWORD'],connect_timeout=10)
conn.set_session(readonly=True)
with conn:
 with conn.cursor() as q:
  q.execute("SELECT current_user,current_database()");role,db=q.fetchone()
  q.execute("SELECT n.nspname||'.'||c.relname,has_table_privilege(current_user,c.oid,'SELECT'),has_table_privilege(current_user,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('staging','dw','analytics') AND c.relkind IN ('r','v','m','p') ORDER BY 1");rows=q.fetchall()
  q.execute('SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolinherit FROM pg_roles WHERE rolname=current_user');attrs=list(q.fetchone())
  q.execute("SELECT count(*) FROM pg_roles WHERE rolname<>current_user AND pg_has_role(current_user,oid,'MEMBER')");memberships=q.fetchone()[0]
  q.execute("SELECT nspname,has_schema_privilege(current_user,oid,'CREATE') FROM pg_namespace WHERE nspname IN ('staging','dw','analytics','public')");schema_create=dict(q.fetchall())
  q.execute("SELECT has_database_privilege(current_user,current_database(),'CREATE'),has_database_privilege(current_user,current_database(),'TEMP')");create,temp=q.fetchone()
r={'role':role,'database':db,'selectable':[n for n,s,w in rows if s],'writeable':[n for n,s,w in rows if w],'attributes_all_false':not any(attrs),'memberships':memberships,'schema_create':schema_create,'database_create':create,'public_temp':temp,'session_read_only_for_observation':True}
assert role=='movielens_bi_reader' and db=='movielens_btl' and not r['writeable'] and not any(attrs) and memberships==0 and not any(schema_create.values()) and not create
print(json.dumps(r));conn.close()'''
def main():
 names=['btl-movielens-s11b4-restore-web-1','btl-movielens-s11b4-restore-metadata-1','btl-movielens-s11b4-restore-init-1','btl-movielens-superset-web-1','btl-movielens-superset-metadata-1']
 all_inspect=json.loads(subprocess.check_output(['docker','inspect',*names],text=True));raw={v['Name'].lstrip('/'):v for v in all_inspect};records=[]
 for name in names:
  v=raw[name];mounts=[{'type':m['Type'],'name':m.get('Name'),'destination':m['Destination'],'writable':m['RW']} for m in v['Mounts']]
  records.append({'name':name,'image_id':v['Image'],'status':v['State']['Status'],'health':v['State'].get('Health',{}).get('Status'),'exit_code':v['State']['ExitCode'],'mounts':mounts,'networks':list(v['NetworkSettings']['Networks']),'ports':v['NetworkSettings']['Ports'],'memory_limit_bytes':v['HostConfig']['Memory'],'nano_cpus':v['HostConfig']['NanoCpus']})
 test_vol={m.get('Name') for name,v in raw.items() if 's11b4-restore' in name for m in v['Mounts'] if m['Type']=='volume'}
 prod_vol={m.get('Name') for name,v in raw.items() if 's11b4-restore' not in name for m in v['Mounts'] if m['Type']=='volume'}
 assert not (test_vol & prod_vol) and len(test_vol)==2
 assert raw[names[0]]['Image']==raw[names[3]]['Image']
 for name in [names[0],names[1],names[3],names[4]]:assert raw[name]['State']['Status']=='running' and raw[name]['State']['Health']['Status']=='healthy'
 assert raw[names[2]]['State']['Status']=='exited' and raw[names[2]]['State']['ExitCode']==0
 p=subprocess.run(['docker','exec','-i',names[0],'python','-c',PAYLOAD],input=json.dumps(dict(dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False))),text=True,capture_output=True,timeout=60)
 assert p.returncode==0,'RESTORE_BI_PRIVILEGE_AUDIT_FAILED';bi=json.loads(p.stdout)
 approved=json.loads((ROOT/'dashboard/preferences/evidence/bi_reader.json').read_text());assert bi['selectable']==approved['selectable'],'BI_SELECT_CHANGED'
 before=json.loads((D/'evidence/production_before.json').read_text(encoding='utf-8'));assert before['objects']==production_objects(SupersetAPI()) and before['database']==model_snapshot(),'PRODUCTION_CHANGED'
 restore=RestoreAPI();mapping=json.loads((D/'evidence/uuid_mapping.json').read_text())['old_id_to_new_id']
 for old,new in mapping['dashboard'].items():
  source=before['objects'][f'dashboard/{old}'];actual=restore.request('GET',f'/api/v1/dashboard/{new}')['result'];filters=copy.deepcopy(json.loads(source['json_metadata'])['native_filter_configuration']);layout=json.loads(source['position_json'])
  for f in filters:
   f['scope']['excluded']=[mapping['chart'][str(x)] for x in f['scope']['excluded']]
   for t in f.get('targets',[]):
    if t.get('datasetId') is not None:t['datasetId']=mapping['dataset'][str(t['datasetId'])]
  for node in layout.values():
   if isinstance(node,dict) and node.get('type')=='CHART':
    old_chart=node['meta']['chartId'];node['meta'].update(chartId=mapping['chart'][str(old_chart)],uuid=before['objects'][f'chart/{old_chart}']['uuid'])
  assert filters==json.loads(actual['json_metadata'])['native_filter_configuration'] and layout==json.loads(actual['position_json']),'RESTORE_FILTER_OR_LAYOUT_CHANGED_AFTER_UI'
 version=subprocess.check_output(['docker','exec',names[0],'python','-c',"import importlib.metadata;print(importlib.metadata.version('apache-superset'))"],text=True).strip();assert version=='6.1.0'
 stats=subprocess.check_output(['docker','stats','--no-stream','--format','{{json .}}',names[0],names[1]],text=True);stats=[{k:v for k,v in json.loads(line).items() if k in ['Name','MemUsage','CPUPerc','PIDs','BlockIO','NetIO']} for line in stats.splitlines()]
 disk={}
 for label,name,path in [('test_metadata',names[1],'/var/lib/postgresql/data'),('test_home',names[0],'/app/superset_home')]:
  disk[label+'_KiB']=int(subprocess.check_output(['docker','exec',name,'du','-sk',path],text=True).split()[0])
 ui_checks={}
 for file,needles in [('ui_overview_all.json',['1,000,209','3,883']),('ui_overview_q3.json',['324,864','2000-07-01','3,883']),('ui_trends_animation.json',['1,715','20,068','63335','-91.45405620888978','Hạng 1: giảm ít nhất']),('ui_preferences_all.json',['6,038 User','2 Không có','kmeans_k4_seed42']),('ui_preferences_filtered.json',['170 User','6,038 Mẫu','2 Không có','Applied filters (3)','Applied filters (1)'])]:
  v=json.loads((D/'evidence'/file).read_text(encoding='utf-8'));assert v['url'].startswith('http://127.0.0.1:8091/');assert all(s in v['ax'] for s in needles),(file,'UI_EXPECTATION_NOT_FOUND');ui_checks[file]='PASS'
 for p in [ROOT/'.env',ROOT/'dashboard/superset/.env.bi',D/'.env']:assert subprocess.run(['git','check-ignore',str(p)],capture_output=True).returncode==0
 policy=zip_state(ROOT)
 report={'status':'PASS','at_utc':datetime.now(timezone.utc).isoformat(),'superset_version':version,'containers':records,'test_volumes':sorted(test_vol),'production_volumes':sorted(prod_vol),'metadata_home_volumes_disjoint':True,'bi_effective_privileges_from_test_container':bi,'bi_same_seven_views_as_approved_11b3':True,'production_32_business_objects_and_staging_dw_model_unchanged':True,'restored_filter_scopes_and_uuid_layout_exact_after_ui':True,'ui_checks':ui_checks,'resource_snapshot':stats,'volume_disk':disk,'ongoing_cost':'Local Docker resources only; no paid cloud service created. Test web/metadata and two volumes retained for review.','production_metadata_not_imported_into':True,'zip_still_ignored':True,'p2_intake_status':'NOT_CONFIRMED','runtime_hash':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'observe.py',D/'common.py']}}
 report['zip_still_ignored']=policy['ignored'];report['zip_publication_policy']=policy
 write('evidence/publication_observation.json' if policy['phase']=='AUTHORIZED_GIT_PUBLICATION' else 'evidence/final_observation.json',report);print(json.dumps({'status':'PASS','version':version,'ui_cases':len(ui_checks),'disjoint_volumes':True,'disk':disk,'production_unchanged':True,'zip_publication_phase':policy['phase']}))
if __name__=='__main__':main()
