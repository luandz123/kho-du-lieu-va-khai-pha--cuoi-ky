"""Read-only final source/clone/BI/Superset preservation after backup preparation."""
import argparse,json,sys,subprocess,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'dashboard/restore')]
from database.backup_restore import (Permit,check_clone,pg_connect,config,SOURCE,assert_project,
 fingerprint,digest_file,require)
from common import SupersetAPI,production_objects
from dotenv import dotenv_values
PAYLOAD=r'''import json,sys,psycopg2
c=json.load(sys.stdin);name=c.pop('CLONE_TARGET');marker=c.pop('CLONE_MARKER')
conn=psycopg2.connect(host=c['POSTGRES_HOST'],port=c['POSTGRES_PORT'],dbname=name,user=c['POSTGRES_USER'],password=c['POSTGRES_PASSWORD'],connect_timeout=10,options='-c timezone=UTC')
conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
with conn:
 with conn.cursor() as q:
  q.execute("SELECT current_database(),current_user,shobj_description(oid,'pg_database'),current_setting('transaction_read_only') FROM pg_database WHERE datname=current_database()");db,role,actual,ro=q.fetchone();assert db==name and actual==marker and role=='movielens_bi_reader' and ro=='on'
  q.execute("SELECT n.nspname||'.'||t.relname,has_table_privilege(current_user,t.oid,'SELECT'),has_table_privilege(current_user,t.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') FROM pg_class t JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname IN ('staging','dw','analytics') AND t.relkind IN ('r','v','p') ORDER BY 1");rows=q.fetchall()
  q.execute("SELECT has_database_privilege(current_user,current_database(),'CONNECT'),has_database_privilege(current_user,current_database(),'CREATE'),has_database_privilege(current_user,current_database(),'TEMP')");dbpriv=list(q.fetchone())
  q.execute('SELECT count(*),sum(rating) FROM dw.v_ml_ratings');ratings=list(q.fetchone());assert ratings==[1000209,3582313]
  q.execute('SELECT count(*) FROM analytics.v_active_user_cluster');users=q.fetchone()[0];assert users==6040
  q.execute('SELECT count(*) FROM analytics.v_active_cluster_genre_profile');profiles=q.fetchone()[0];assert profiles==72
out={'database':db,'role':role,'session_read_only':ro,'selectable':[n for n,s,w in rows if s],'writeable':[n for n,s,w in rows if w],'database_privileges_connect_create_temp':dbpriv,'ratings_count_sum':ratings,'active_users':users,'active_profiles':profiles}
assert not out['writeable'] and dbpriv==[True,False,True]
print(json.dumps(out));conn.close()'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();r=json.loads(a.receipt.read_text(encoding='utf-8'));require(r['status']=='PASS_WAITING_REVIEW','BACKUP_NOT_VERIFIED')
 permit=Permit(r['target'],r['run_id'],r['dw_dump']['sha256']);c=config(ROOT/'.env');endpoints={}
 for label,name in [('production',SOURCE),('clone',permit.target)]:
  conn=pg_connect(c,name,readonly=True)
  with conn:
   if label=='production':assert_project(conn);require(fingerprint(conn)==r['source_before'],'SOURCE_CHANGED_AFTER_METADATA_BACKUP')
   else:check_clone(conn,permit)
   with conn.cursor() as q:q.execute("SELECT current_database(),inet_server_addr()::text,inet_server_port(),current_setting('transaction_read_only')");endpoints[label]=list(q.fetchone())
  conn.close()
 bi=dict(dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False));bi.update(CLONE_TARGET=permit.target,CLONE_MARKER=permit.marker)
 b=subprocess.run(['docker','exec','-i','btl-movielens-superset-web-1','python','-c',PAYLOAD],input=json.dumps(bi),capture_output=True,text=True,timeout=60);require(b.returncode==0,'CLONE_BI_READER_FAILED');priv=json.loads(b.stdout)
 approved=json.loads((ROOT/'dashboard/preferences/evidence/bi_reader.json').read_text());require(priv['selectable']==approved['selectable'],'CLONE_BI_ACL_MISMATCH')
 before=json.loads((ROOT/'results/warehouse/s12a_prep/superset_before.json').read_text(encoding='utf-8'))['objects'];after=production_objects(SupersetAPI());require(before==after,'SUPERSET_PRODUCTION_CONFIG_CHANGED')
 local=ROOT/r['private_backup_directory'];require(digest_file(local/'dw.dump')==r['dw_dump']['sha256'] and digest_file(local/'superset_metadata.dump')==r['superset_metadata_backup']['sha256'],'BACKUP_HASH_CHANGED')
 config_copy=all((ROOT/'dashboard/superset'/f).read_bytes()==(local/'superset_private_config'/f).read_bytes() for f in r['superset_metadata_backup']['private_config_files_preserved']);require(config_copy,'PRIVATE_CONFIG_COPY_DIFFERS')
 metadata_version=subprocess.check_output(['docker','exec','btl-movielens-superset-metadata-1','pg_dump','--version'],text=True).strip()
 protected=json.loads((ROOT/'results/warehouse/s12a_prep/protected_files_before.json').read_text())['files'];require(all(digest_file(ROOT/p)==h for p,h in protected.items()),'PROTECTED_FILE_CHANGED')
 inspect=json.loads(subprocess.check_output(['docker','inspect','btl-movielens-superset-web-1','btl-movielens-superset-metadata-1','btl-movielens-s11b4-restore-web-1','btl-movielens-s11b4-restore-metadata-1'],text=True));services=[{'name':v['Name'],'status':v['State']['Status'],'health':v['State'].get('Health',{}).get('Status'),'exit_code':v['State']['ExitCode'],'volumes':[m.get('Name') for m in v['Mounts'] if m['Type']=='volume']} for v in inspect]
 out={'status':'PASS','at_utc':datetime.now(timezone.utc).isoformat(),'backup_run_id':r['run_id'],'endpoints':endpoints,'bi_clone_read_only':priv,'production_32_business_objects_unchanged':True,'source_fingerprints_preserved_after_metadata_backup':True,'private_secret_config_exact_copy':config_copy,'secret_config_values_or_hashes_published':False,'metadata_pg_dump_version':metadata_version,'metadata_restore_tested':False,'protected_files_unchanged':len(protected),'services':services,'services_before_observed':'8089 and 8091 project web/metadata Exited255 at turn start; cause unverified. Started only existing 8089 metadata/web for backup/API; no recreate/init/volume reset. 8091 left stopped.','dump_completed_utc_from_file_mtime':{name:datetime.fromtimestamp((local/name).stat().st_mtime,timezone.utc).isoformat() for name in ['dw.dump','superset_metadata.dump']},'code_sha256':digest_file(__file__),'step12a_completed':False,'integration_candidate':None,'p2_intake_status':'NOT_CONFIRMED'}
 path=ROOT/'results/warehouse/s12a_prep/postflight.json';path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','target':permit.target,'production_unchanged':True,'bi_select_views':len(priv['selectable']),'metadata_restore_tested':False}))
if __name__=='__main__':main()
