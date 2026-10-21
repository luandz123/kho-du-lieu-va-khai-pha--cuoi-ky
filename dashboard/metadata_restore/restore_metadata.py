"""Guarded one-shot metadata restore; private dumps/config/logs never published.

No Superset initialization, upgrade, import ZIP, layout repair or metadata edits.
"""
import argparse,json,hashlib,subprocess,socket,time,uuid,sys
from pathlib import Path
from datetime import datetime,timezone
from dotenv import dotenv_values
from common import ROOT,D,SupersetAPI,production_objects,write
sys.path.insert(0,str(ROOT))
from database.backup_restore import config,pg_connect,assert_project,fingerprint,acl_ownership
sys.path.insert(0,str(ROOT/'dashboard/preferences'))
from prepare import model_snapshot
PROJECT='btl-movielens-s12a-metadata'
META=PROJECT+'-metadata-1';WEB=PROJECT+'-web-1'
DB='superset_metadata';PURPOSE='s12a-metadata-restore-test'
EXPECTED='43665b8c70c13d295ad7c6f3f9289a41750ce536ae28c94435213fdda5141236'
BACKUP=ROOT/'backups/p1_s12a_20261021_2856ed49e9ba494090e2acae73b41b9a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def docker_json(*args):return json.loads(subprocess.check_output(['docker',*args],text=True))
def guard_resource(info,rid):
 assert info['Name']=='/'+META and info['Config']['Labels'].get('btl.run_id')==rid and info['Config']['Labels'].get('btl.purpose')==PURPOSE,'TARGET_RESOURCE_REJECTED'
 vols=[m['Name'] for m in info['Mounts'] if m['Type']=='volume']
 assert vols==[PROJECT+'_restore_metadata'],'TARGET_VOLUME_REJECTED'
def marker(rid):return f'BTL S12A METADATA RESTORE TEST; run_id={rid}; dump_sha256={EXPECTED}'
def sql_exec(statement):
 p=subprocess.run(['docker','exec','-i',META,'psql','-X','-U','superset_meta','-d',DB,'-v','ON_ERROR_STOP=1','-tA'],input=statement,text=True,capture_output=True,timeout=30)
 assert p.returncode==0,'TARGET_PSQL_FAILED'
 return p.stdout.strip()
def guard_database(rid):
 guard_resource(docker_json('inspect',META)[0],rid)
 assert sql_exec("SELECT current_database()||'|'||shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database();")==DB+'|'+marker(rid),'TARGET_MARKER_REJECTED'
 assert sql_exec("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")=='0','TARGET_NOT_EMPTY'
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
 assert sha(BACKUP/'superset_metadata.dump')==EXPECTED,'METADATA_DUMP_HASH_CHANGED'
 if not a.apply:print(json.dumps({'mode':'PLAN_ONLY','port':8092,'project':PROJECT,'dump_sha256':EXPECTED}));return
 assert not (D/'.env').exists() and not (D/'evidence/restore_receipt.json').exists(),'RESTORE_ALREADY_PREPARED_DO_NOT_OVERWRITE'
 with socket.socket() as s:s.bind(('127.0.0.1',8092))
 assert not subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project='+PROJECT],text=True).strip(),'PROJECT_EXISTS'
 for vol in ('restore_metadata','restore_home'):
  assert subprocess.run(['docker','volume','inspect',PROJECT+'_'+vol],capture_output=True).returncode!=0,'VOLUME_EXISTS'
 rid=uuid.uuid4().hex;private=ROOT/'backups'/('metadata_restore_'+rid);private.mkdir()
 src=(BACKUP/'superset_private_config/.env').read_text(encoding='utf-8')
 path=(BACKUP/'superset_private_config/superset_config.py').as_posix()
 (D/'.env').write_text(src+'\nRESTORE_RUN_ID='+rid+'\nBACKED_UP_CONFIG='+path+'\n',encoding='utf-8')
 assert subprocess.run(['git','check-ignore','-q',str(D/'.env')]).returncode==0
 base=['docker','compose','--env-file',str(D/'.env'),'-f',str(D/'compose.yaml')]
 before={'objects':production_objects(SupersetAPI()),'database':model_snapshot()}
 c=pg_connect(config(ROOT/'.env'),'movielens_btl',readonly=True)
 with c:assert_project(c);before['dw_fingerprint']=fingerprint(c);before['acl']=acl_ownership(c)
 c.close();write('evidence/production_before.json',before)
 write('evidence/uuid_mapping.json',{'old_id_to_new_id':{kind:{str(i):i for i in range(1,n+1)} for kind,n in [('dashboard',3),('dataset',6),('chart',23)]},'reason':'Metadata database restore preserves original IDs and UUIDs; no remapping or layout repair applied'})
 receipt={'run_id':rid,'at_utc':datetime.now(timezone.utc).isoformat(),'status':'FAIL','target_project':PROJECT,'metadata_database':DB,'port':8092,'dump_sha256':EXPECTED,'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'code_state':'WORKING_TREE_NOT_IN_CHECKPOINT','code_sha256':sha(Path(__file__)),'private_logs':private.relative_to(ROOT).as_posix(),'production_metadata_restored_into':False,'layout_repair_applied':False,'zip_import_performed':False,'p2_intake_status':'NOT_CONFIRMED'}
 def run(args,label,stdin=None):
  with (private/(label+'.stdout.log')).open('wb') as out,(private/(label+'.stderr.log')).open('wb') as err:
   result=subprocess.run(args,stdin=stdin,stdout=out,stderr=err,timeout=180)
  assert result.returncode==0,'PRIVATE_COMMAND_FAILED_'+label
 def wait(name):
  for _ in range(90):
   info=docker_json('inspect',name)[0]
   if info['State'].get('Health',{}).get('Status')=='healthy':return
   time.sleep(2)
  raise AssertionError('HEALTH_TIMEOUT')
 try:
  run(base+['up','-d','metadata'],'start_metadata');wait(META)
  guard_resource(docker_json('inspect',META)[0],rid)
  assert sql_exec("SELECT current_database()||'|'||count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")==DB+'|0','TARGET_NOT_EMPTY'
  sql_exec("COMMENT ON DATABASE superset_metadata IS '"+marker(rid)+"';")
  guard_database(rid)
  toc=subprocess.check_output([r'C:\Program Files\PostgreSQL\17\bin\pg_restore.exe','--list',str(BACKUP/'superset_metadata.dump')],text=True)
  from database.backup_restore import validate_toc
  receipt['toc_entries']=validate_toc(toc)
  assert sha(BACKUP/'superset_metadata.dump')==EXPECTED
  with (BACKUP/'superset_metadata.dump').open('rb') as inp:
   run(['docker','exec','-i',META,'pg_restore','-U','superset_meta','-d',DB,'--single-transaction','--exit-on-error','--verbose'],'pg_restore',stdin=inp)
  assert sql_exec("SELECT shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database();")==marker(rid)
  receipt['metadata_public_table_count']=int(sql_exec("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"))
  run(base+['up','-d','web'],'start_web');wait(WEB)
  receipt['superset_version']=subprocess.check_output(['docker','exec',WEB,'python','-c',"import importlib.metadata;print(importlib.metadata.version('apache-superset'))"],text=True).strip()
  assert receipt['superset_version']=='6.1.0'
  receipt['image_id']=docker_json('inspect',WEB)[0]['Image']
  assert receipt['image_id']==docker_json('inspect','btl-movielens-superset-web-1')[0]['Image']
  receipt.update(status='RESTORED_AWAITING_FUNCTIONAL_CHECK',finished_utc=datetime.now(timezone.utc).isoformat(),target_retained=True)
  write('evidence/restore_receipt.json',receipt);print(json.dumps({'status':receipt['status'],'run_id':rid,'port':8092,'version':receipt['superset_version']}))
 except Exception as e:
  receipt['error_category']=str(e) if isinstance(e,AssertionError) else type(e).__name__;write('evidence/restore_FAIL_'+rid+'.json',receipt);raise RuntimeError(receipt['error_category']) from None
if __name__=='__main__':main()
