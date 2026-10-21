"""Read-only post-UI proof of isolation, config/ACL preservation and BI identity."""
import json,sys,subprocess,hashlib
from datetime import datetime,timezone
from common import ROOT,D,RestoreAPI,SupersetAPI,production_objects,write
from restore_metadata import PROJECT,META,WEB,BACKUP,EXPECTED,sha,guard_resource,marker,sql_exec
from database.backup_restore import config,pg_connect,assert_project,fingerprint,acl_ownership
from dotenv import dotenv_values
sys.path.insert(0,str(ROOT/'tests/warehouse'))
from check_backup_postflight import PAYLOAD
def normalize(v):return json.loads(json.dumps(v,default=str))
def main():
 r=json.loads((D/'evidence/restore_receipt.json').read_text(encoding='utf-8'));before=json.loads((D/'evidence/production_before.json').read_text(encoding='utf-8'))
 verify=json.loads((D/'evidence/restore_verification.json').read_text(encoding='utf-8'));assert verify['status']=='PASS'
 api=RestoreAPI();prod=SupersetAPI();restored=production_objects(api)
 assert restored==before['objects'],'METADATA_BUSINESS_FIELDS_OR_LAYOUT_CHANGED'
 assert production_objects(prod)==before['objects'],'PRODUCTION_BUSINESS_FIELDS_CHANGED'
 c=pg_connect(config(ROOT/'.env'),'movielens_btl',readonly=True)
 with c:
  assert_project(c);assert fingerprint(c)==before['dw_fingerprint'];assert normalize(acl_ownership(c))==before['acl']
  with c.cursor() as q:q.execute("SELECT shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database()");source_marker=q.fetchone()[0]
 c.close()
 bi=dict(dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False));bi.update(CLONE_TARGET='movielens_btl',CLONE_MARKER=source_marker)
 p=subprocess.run(['docker','exec','-i',WEB,'python','-c',PAYLOAD],input=json.dumps(bi),capture_output=True,text=True,timeout=90);assert p.returncode==0,'BI_RO_CHECK_FAILED';priv=json.loads(p.stdout)
 assert priv['selectable']==json.loads((ROOT/'dashboard/preferences/evidence/bi_reader.json').read_text(encoding='utf-8'))['selectable']
 names=[META,WEB,'btl-movielens-superset-web-1','btl-movielens-superset-metadata-1','btl-movielens-s11b4-restore-web-1','btl-movielens-s11b4-restore-metadata-1']
 info=json.loads(subprocess.check_output(['docker','inspect',*names],text=True));byname={v['Name'].lstrip('/'):v for v in info};guard_resource(byname[META],r['run_id'])
 assert sql_exec("SELECT shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database();")==marker(r['run_id'])
 testvol={m['Name'] for v in info[:2] for m in v['Mounts'] if m['Type']=='volume'};othervol={m['Name'] for v in info[2:] for m in v['Mounts'] if m['Type']=='volume'}
 assert not testvol&othervol and len(testvol)==2
 assert all(byname[n]['State']['Health']['Status']=='healthy' for n in names[:4])
 assert all(byname[n]['State']['Status']=='exited' and byname[n]['State']['ExitCode']==255 for n in names[4:])
 assert sha(BACKUP/'superset_metadata.dump')==EXPECTED
 assert all((ROOT/'dashboard/superset'/p).read_bytes()==(BACKUP/'superset_private_config'/p).read_bytes() for p in ['.env','.env.bi','superset_config.py','compose.yaml','Dockerfile','init_metadata.py'])
 ui={}
 for file,need in [('ui_overview_all',['1,000,209','3,883']),('ui_overview_q3',['324,864','2000-07-01','3,883']),('ui_trends_animation',['1,715','20,068','63335','Hạng 1: giảm ít nhất']),('ui_preferences_all',['6,038 User','2 Không có','kmeans_k4_seed42']),('ui_preferences_filtered',['170 User','6,038 Mẫu','2 Không có','Applied filters (3)','Applied filters (1)'])]:
  data=json.loads((D/'evidence'/f'{file}.json').read_text(encoding='utf-8'));assert data['url'].startswith('http://127.0.0.1:8092/');assert all(s in data['ax'] for s in need),file;assert (D/'evidence'/f'{file}.png').stat().st_size>10000;ui[file]='PASS'
 stats=[json.loads(line) for line in subprocess.check_output(['docker','stats','--no-stream','--format','{{json .}}',WEB,META],text=True).splitlines()]
 out={'status':'PASS_WAITING_REVIEW','at_utc':datetime.now(timezone.utc).isoformat(),'run_id':r['run_id'],'metadata_restore_tested':True,'login_succeeded_with_restored_account':True,'restored_encrypted_database_connection_works_as_bi_role':verify['engine'],'all_32_business_objects_layout_filter_metric_sql_exact':True,'identity_ids_and_uuids_preserved':True,'layout_repair_applied':False,'zip_import_performed':False,'source_dw_model_acl_preserved':True,'production_32_business_objects_preserved':True,'private_backed_up_config_matches_production':True,'bi_effective_read_only_privileges':priv,'ui_checks':ui,'test_volumes':sorted(testvol),'volume_isolation':True,'containers':[{'name':v['Name'],'image':v['Image'],'status':v['State']['Status'],'health':v['State'].get('Health',{}).get('Status'),'exit_code':v['State']['ExitCode']} for v in info],'resources':[{k:v for k,v in s.items() if k in ['Name','MemUsage','CPUPerc','PIDs']} for s in stats],'scope':'same host/version, existing production DW; not new-machine whole-stack disaster recovery','p2_intake_status':'NOT_CONFIRMED','step12a_completed':False,'integration_candidate':None,'code_sha256':sha(D/'observe.py')}
 write('evidence/final_observation.json',out);print(json.dumps({'status':out['status'],'ui_cases':len(ui),'layout_exact':True,'production_unchanged':True,'bi_read_only':True}))
if __name__=='__main__':main()
