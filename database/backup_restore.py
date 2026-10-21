"""S12A preparation only: consistent pg_dump, guarded new clone, read-only checks.

Never changes production data or production guards. Raw logs/dumps/secrets stay
under ignored backups/. Metadata backup is NOT restored in this step.
"""
from __future__ import annotations
import argparse,gc,hashlib,json,os,re,shutil,subprocess,sys,time,uuid,warnings
from datetime import datetime,timezone
from pathlib import Path
from dataclasses import dataclass
import psycopg2
from psycopg2 import sql
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from etl.s05_staging import config,assert_project,catalog,SafeError
SOURCE='movielens_btl'
BIN=Path('C:/Program Files/PostgreSQL/17/bin')
TABLES={'staging.users_raw':'source_line','staging.movies_raw':'source_line','staging.ratings_raw':'source_line',
 'dw.dim_user':'user_key','dw.dim_movie':'movie_key','dw.dim_date':'date_key','dw.dim_genre':'genre_key',
 'dw.bridge_movie_genre':'movie_key,genre_key','dw.fact_rating':'rating_key',
 'analytics.model_registry':'model_version','analytics.user_cluster':'model_version,user_id',
 'analytics.cluster_genre_profile':'model_version,cluster_id,genre_name'}
def require(ok,code):
 if not ok:raise SafeError(code)
def digest_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump_json(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def validate_target_name(name):
 require(isinstance(name,str) and re.fullmatch(r'movielens_btl_restore_[0-9]{8}_[0-9a-f]{8}',name) is not None,'RESTORE_TARGET_NAME_REJECTED')
 require(name!=SOURCE,'PRODUCTION_RESTORE_FORBIDDEN')
 return name
@dataclass(frozen=True)
class Permit:
 target:str
 run_id:str
 dump_sha256:str
 @property
 def marker(self):return f'BTL P1 S12A-PREP RESTORE TEST; source={SOURCE}; run_id={self.run_id}; dump_sha256={self.dump_sha256}'
def require_clone_identity(name,marker,permit):
 validate_target_name(permit.target)
 require(name==permit.target and marker==permit.marker,'RESTORE_CLONE_IDENTITY_MISMATCH')
def pg_connect(c,name,*,readonly=False):
 conn=psycopg2.connect(host=c['POSTGRES_HOST'],port=int(c['POSTGRES_PORT']),dbname=name,user=c['POSTGRES_USER'],password=c['POSTGRES_PASSWORD'],connect_timeout=10,application_name='btl_p1_s12a_prep',options='-c timezone=UTC -c lock_timeout=10000 -c statement_timeout=300000')
 if readonly:conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
 return conn
def check_clone(conn,permit):
 with conn.cursor() as q:
  q.execute("SELECT current_database(),shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database()")
  require_clone_identity(*q.fetchone(),permit)
def official_restore_args(c,permit,path):
 validate_target_name(permit.target)
 require(digest_file(path)==permit.dump_sha256,'DUMP_BYTES_CHANGED')
 return [str(BIN/'pg_restore.exe'),'--host',c['POSTGRES_HOST'],'--port',str(c['POSTGRES_PORT']),'--username',c['POSTGRES_USER'],'--no-password','--dbname',permit.target,'--exit-on-error','--single-transaction','--verbose',str(path)]
def validate_toc(text):
 entries=[line for line in text.splitlines() if line and not line.startswith(';')]
 require(bool(entries),'EMPTY_ARCHIVE_TOC')
 # No archive may issue database creation/properties/ACL/comment against source.
 require(not any(re.search(r'\bDATABASE(?: PROPERTIES)?\b',line) for line in entries),'ARCHIVE_DATABASE_COMMAND_REJECTED')
 return len(entries)
def db_info(conn):
 with conn.cursor() as q:
  q.execute("SELECT current_database(),current_user,current_setting('server_version'),pg_database_size(current_database()),pg_get_userbyid(datdba),pg_encoding_to_char(encoding),datcollate,datctype,datlocprovider,to_jsonb(d)->>'datlocale',shobj_description(oid,'pg_database'),datacl FROM pg_database d WHERE datname=current_database()")
  names=['database','role','server_version','bytes','owner','encoding','lc_collate','lc_ctype','locale_provider','locale','marker','database_acl'];return dict(zip(names,q.fetchone()))
def fingerprint(conn):
 out={}
 with conn.cursor() as q:
  for table,order in TABLES.items():
   # Only fixed identifiers above; no user-level rows leave the DB.
   q.execute(f'SELECT count(*),md5(string_agg(row_to_json(t)::text,chr(10) ORDER BY {order})) FROM {table} t')
   n,h=q.fetchone();out[table]={'rows':n,'ordered_row_md5':h}
  q.execute("SELECT schemaname||'.'||viewname,definition FROM pg_views WHERE schemaname IN ('staging','dw','analytics') ORDER BY 1");out['view_definitions_sha256']=hashlib.sha256(json.dumps(q.fetchall()).encode()).hexdigest()
  q.execute("SELECT sequencename FROM pg_sequences WHERE schemaname='dw' ORDER BY sequencename")
  seqs=[r[0] for r in q.fetchall()];out['sequences']={}
  for name in seqs:
   q.execute(sql.SQL('SELECT last_value,is_called FROM dw.{}').format(sql.Identifier(name)));out['sequences'][name]=list(q.fetchone())
 return out
def acl_ownership(conn):
 with conn.cursor() as q:
  q.execute("SELECT n.nspname||'.'||c.relname,c.relkind,pg_get_userbyid(c.relowner),c.relacl FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('staging','dw','analytics') AND c.relkind IN ('r','v','S') ORDER BY 1");relations=q.fetchall()
  q.execute("SELECT nspname,pg_get_userbyid(nspowner),nspacl FROM pg_namespace WHERE nspname IN ('staging','dw','analytics') ORDER BY 1");schemas=q.fetchall()
  q.execute("SELECT r.rolname,s.setconfig FROM pg_db_role_setting s LEFT JOIN pg_roles r ON r.oid=s.setrole JOIN pg_database d ON d.oid=s.setdatabase WHERE d.datname=current_database() ORDER BY 1 NULLS FIRST");settings=q.fetchall()
 return {'relations':relations,'schemas':schemas,'database_role_settings':settings}
def canonical(conn):
 from mining.data_io import load_dw_data,compute_canonical_hash
 with warnings.catch_warnings(record=True) as captured:
  warnings.simplefilter('always');frames=load_dw_data(connection_or_engine=conn)
 out={'hashes':{k:compute_canonical_hash(k,f) for k,f in frames.items()},'row_counts':{k:len(f) for k,f in frames.items()},'warning_categories':sorted({type(w.message).__name__ for w in captured})}
 del frames;gc.collect();return out
def aggregate_checks(conn):
 out={}
 with conn.cursor() as q:
  q.execute('SELECT * FROM analytics.v_olap_kpi');out['kpi']=dict(zip([d.name for d in q.description],q.fetchone()))
  require(out['kpi']['rating_count']==1000209 and out['kpi']['rating_sum']==3582313 and out['kpi']['rated_users']==6040 and out['kpi']['rated_movies']==3706,'KPI_MISMATCH')
  q.execute('SELECT model_version,is_active,is_valid_for_dw,registered_at,model_created_at FROM analytics.model_registry ORDER BY model_version');out['registry']=[dict(zip([d.name for d in q.description],row)) for row in q.fetchall()]
  require(len(out['registry'])==1 and out['registry'][0]['model_version']=='kmeans_k4_seed42' and out['registry'][0]['is_active'] and out['registry'][0]['is_valid_for_dw'],'REGISTRY_MISMATCH')
  q.execute('SELECT status,cluster_id,count(*) FROM analytics.v_active_user_cluster GROUP BY 1,2 ORDER BY 1,2');out['clusters']=[{'status':s,'cluster_id':cid,'users':n} for s,cid,n in q.fetchall()]
  require([(r['cluster_id'],r['users']) for r in out['clusters'] if r['status']=='assigned']==[(0,2478),(1,1393),(2,760),(3,1407)],'CLUSTER_COUNTS')
  require(sum(r['users'] for r in out['clusters'])==6040 and [(r['cluster_id'],r['users']) for r in out['clusters'] if r['status']=='insufficient_evidence']==[(None,2)],'INSUFFICIENT_MISMATCH')
  q.execute('SELECT cluster_id,count(*),sum(mean_preference),min(n_users),max(n_users) FROM analytics.v_active_cluster_genre_profile GROUP BY 1 ORDER BY 1');out['profiles']=[{'cluster_id':cid,'genres':n,'sum_mean':float(total),'min_n_users':lo,'max_n_users':hi} for cid,n,total,lo,hi in q.fetchall()]
  require(len(out['profiles'])==4 and all(x['genres']==18 and abs(x['sum_mean']-1)<1e-8 and x['min_n_users']==x['max_n_users']==[2478,1393,760,1407][x['cluster_id']] for x in out['profiles']),'PROFILE_MISMATCH')
  q.execute('SELECT movie_id,rating_count FROM analytics.v_olap_movie_metrics ORDER BY rating_count DESC,mean_rating DESC,movie_id LIMIT 1');out['top_movie']=list(q.fetchone());require(out['top_movie']==[2858,3428],'TOP_MOVIE_MISMATCH')
  q.execute("SELECT time_level,count(*),sum(rating_count),sum(rating_sum) FROM analytics.v_olap_time_rollup GROUP BY 1 ORDER BY 1");out['rollup']=[list(x) for x in q.fetchall()];require(all(x[2]==1000209 and x[3]==3582313 for x in out['rollup']),'ROLLUP_MISMATCH')
  q.execute("SELECT count(*) FROM dw.fact_rating WHERE rated_at>='2000-07-01T00:00:00Z'::timestamptz AND rated_at<'2000-10-01T00:00:00Z'::timestamptz");out['q3_2000']=q.fetchone()[0];require(out['q3_2000']==324864,'Q3_MISMATCH')
  q.execute("SELECT rating_count,previous_rating_count,qoq_pct,genre_assignment_total,genre_share_pct,eligible_for_ranking FROM analytics.v_olap_genre_quarter WHERE genre_name='Animation' AND quarter_start='2001-01-01'");out['animation_2001q1']=dict(zip([d.name for d in q.description],q.fetchone()));require(out['animation_2001q1']['rating_count']==1715 and out['animation_2001q1']['previous_rating_count']==20068 and abs(float(out['animation_2001q1']['qoq_pct'])+91.45405620888978)<1e-8 and out['animation_2001q1']['genre_assignment_total']==63335,'O5_MISMATCH')
 return out
def run_private(args,local,label,*,env=None,stdout_file=None):
 raw_out=stdout_file or local/(label+'.stdout.log');raw_err=local/(label+'.stderr.log')
 with Path(raw_out).open('wb') as a,raw_err.open('wb') as b:p=subprocess.run(args,stdout=a,stderr=b,env=env,timeout=600)
 require(p.returncode==0,'OFFICIAL_TOOL_FAILED_'+label.upper())
 return {'exit_code':p.returncode,'raw_stdout_local':str(Path(raw_out).relative_to(ROOT)),'raw_stderr_local':str(raw_err.relative_to(ROOT))}
def backup_metadata(local):
 container='btl-movielens-superset-metadata-1';path=local/'superset_metadata.dump'
 report=run_private(['docker','exec',container,'pg_dump','-U','superset_meta','-d','superset_metadata','--format=custom','--no-password','--verbose'],local,'metadata_dump',stdout_file=path)
 report.update(sha256=digest_file(path),bytes=path.stat().st_size,scope='Production Superset metadata only; encrypted connection metadata may exist, local only',metadata_restore_tested=False)
 report['toc']=run_private([str(BIN/'pg_restore.exe'),'--list',str(path)],local,'metadata_toc')
 report['archive_readability']=run_private([str(BIN/'pg_restore.exe'),'--file',os.devnull,'--exit-on-error',str(path)],local,'metadata_archive_read')
 # Preserve the exact secret/config locally. Never publish their values or hashes.
 dest=local/'superset_private_config';dest.mkdir()
 names=['.env','.env.bi','superset_config.py','compose.yaml','Dockerfile','init_metadata.py']
 for name in names:shutil.copyfile(ROOT/'dashboard/superset'/name,dest/name)
 report['private_config_files_preserved']=names
 report['config_secret_hashes_published']=False
 return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--date',default='20261021');p.add_argument('--target');args=p.parse_args()
 require(re.fullmatch(r'[0-9]{8}',args.date) is not None,'DATE_REJECTED')
 rid=uuid.uuid4().hex;target=validate_target_name(args.target or f'movielens_btl_restore_{args.date}_{rid[:8]}');local=ROOT/'backups'/f'p1_s12a_{args.date}_{rid}'
 report_path=ROOT/'results/warehouse/s12a_prep'/f'backup_restore_{rid}.json';start=time.monotonic();source=None;maintenance=None;report={'run_id':rid,'at_utc':datetime.now(timezone.utc).isoformat(),'step':'PRE_12A_BACKUP_RESTORE_ONLY','status':'IN_PROGRESS','target':target,'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'code_sha256':digest_file(__file__),'metadata_restore_tested':False,'p2_intake_status':'NOT_CONFIRMED','cf_step10':'WAITING_FOR_P2_FINALIZATION','integration_candidate_selected':False}
 try:
  c=config(ROOT/'.env');source=pg_connect(c,SOURCE,readonly=True);assert_project(source);info=db_info(source);report['source']=info
  free=shutil.disk_usage(ROOT).free;require(free>info['bytes']*3+1024**3,'INSUFFICIENT_BACKUP_DISK_SPACE');report['disk']={'free_before':free,'source_database_bytes':info['bytes'],'minimum_policy_bytes':info['bytes']*3+1024**3}
  versions={tool:subprocess.check_output([str(BIN/(tool+'.exe')),'--version'],text=True).strip() for tool in ['pg_dump','pg_restore']};require(all('17.' in v for v in versions.values()) and info['server_version'].startswith('17.'),'TOOL_SERVER_MAJOR_MISMATCH');report['versions']=versions
  maintenance=pg_connect(c,'postgres');maintenance.autocommit=True
  with maintenance.cursor() as q:
   q.execute('SELECT 1 FROM pg_database WHERE datname=%s',(target,));require(q.fetchone() is None,'RESTORE_TARGET_ALREADY_EXISTS')
   q.execute('SELECT rolsuper,rolcreatedb FROM pg_roles WHERE rolname=current_user');require(any(q.fetchone()),'CREATE_DATABASE_PRIVILEGE_MISSING')
  if not args.apply:
   report['status']='PLAN_ONLY';dump_json(report_path,report);print(json.dumps({'status':'PLAN_ONLY','target':target,'report':str(report_path.relative_to(ROOT))}));return 0
  require(not local.exists(),'BACKUP_DIRECTORY_EXISTS');local.mkdir(parents=True)
  require(subprocess.run(['git','check-ignore',str(local/'dw.dump')],cwd=ROOT,capture_output=True).returncode==0,'PRIVATE_BACKUP_NOT_IGNORED')
  with source.cursor() as q:q.execute('SELECT pg_advisory_xact_lock_shared(20261027,1)');q.execute('SELECT pg_export_snapshot()');snapshot=q.fetchone()[0]
  report['consistent_snapshot']='Explicit exported PostgreSQL MVCC snapshot; source READ ONLY repeatable-read transaction and project shared advisory lock held through dump/verification'
  report['source_catalog']=catalog(source);report['source_before']=fingerprint(source);report['source_acl_ownership']=acl_ownership(source)
  expected=json.loads((ROOT/'results/warehouse/dw_manifest.json').read_text(encoding='utf-8'));report['source_canonical']=canonical(source);require(report['source_canonical']['hashes']==expected['canonical_hashes'] and report['source_canonical']['row_counts']==expected['row_counts'],'SOURCE_CANONICAL_MISMATCH')
  report['source_aggregates']=aggregate_checks(source);print(json.dumps({'phase':'SOURCE_VERIFIED','run_id':rid,'target':target}),flush=True)
  env=os.environ.copy();env['PGPASSWORD']=c['POSTGRES_PASSWORD'];env['PGOPTIONS']='-c timezone=UTC'
  dump=local/'dw.dump';cmd=[str(BIN/'pg_dump.exe'),'--host',c['POSTGRES_HOST'],'--port',str(c['POSTGRES_PORT']),'--username',c['POSTGRES_USER'],'--dbname',SOURCE,'--no-password','--format=custom','--snapshot',snapshot,'--verbose','--file',str(dump)]
  report['dw_dump']=run_private(cmd,local,'dw_dump',env=env);h=digest_file(dump);report['dw_dump'].update(sha256=h,bytes=dump.stat().st_size,scope='All movielens_btl database objects/data; owners and object ACL retained, no globals/role passwords, no CREATE DATABASE',completed_at_utc=datetime.now(timezone.utc).isoformat())
  report['dw_toc']=run_private([str(BIN/'pg_restore.exe'),'--list',str(dump)],local,'dw_toc');toc=(local/'dw_toc.stdout.log').read_text(encoding='utf-8');report['dw_toc']['entries']=validate_toc(toc)
  permit=Permit(target,rid,h)
  with maintenance.cursor() as q:
   q.execute('SELECT 1 FROM pg_database WHERE datname=%s',(target,));require(q.fetchone() is None,'RESTORE_TARGET_APPEARED')
   require(info['locale_provider']=='c','NON_LIBC_LOCALE_REQUIRES_EXPLICIT_PREPARATION')
   q.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE template0 ENCODING %s LC_COLLATE %s LC_CTYPE %s').format(sql.Identifier(target)),(info['encoding'],info['lc_collate'],info['lc_ctype']))
   q.execute(sql.SQL('COMMENT ON DATABASE {} IS %s').format(sql.Identifier(target)),(permit.marker,))
  guard=pg_connect(c,target,readonly=True)
  with guard:check_clone(guard,permit)
  guard.close();report['target_created']=True;report['target_marker']=permit.marker
  report['restore']=run_private(official_restore_args(c,permit,dump),local,'dw_restore',env=env);print(json.dumps({'phase':'RESTORE_COMPLETED','target':target,'dump_sha256':h}),flush=True)
  clone=pg_connect(c,target,readonly=True)
  try:
   with clone:
    check_clone(clone,permit)
    try:assert_project(clone);raise SafeError('PRODUCTION_GUARD_UNEXPECTEDLY_ACCEPTED_CLONE')
    except SafeError as e:require(e.code=='UNVERIFIED_PROJECT_DATABASE','PRODUCTION_GUARD_CHANGED')
    report['production_guard_still_rejects_clone']=True
    report['clone_catalog']=catalog(clone);report['clone_fingerprints']=fingerprint(clone);require(report['clone_fingerprints']==report['source_before'],'CLONE_DATA_OR_VIEW_MISMATCH')
    report['clone_canonical']=canonical(clone);require(report['clone_canonical']['hashes']==expected['canonical_hashes'] and report['clone_canonical']['row_counts']==expected['row_counts'],'CLONE_CANONICAL_MISMATCH')
    report['clone_aggregates']=aggregate_checks(clone);require(report['clone_aggregates']==report['source_aggregates'],'CLONE_AGGREGATE_MISMATCH')
    report['clone_acl_ownership']=acl_ownership(clone);require(report['clone_acl_ownership']['relations']==report['source_acl_ownership']['relations'] and report['clone_acl_ownership']['schemas']==report['source_acl_ownership']['schemas'],'CLONE_OBJECT_ACL_OR_OWNER_MISMATCH')
    report['clone_database']=db_info(clone)
    with clone.cursor() as q:q.execute("SELECT current_setting('transaction_read_only')");require(q.fetchone()[0]=='on','CLONE_CHECK_NOT_READ_ONLY')
  finally:clone.close()
  # Fresh source connection, independently observing preservation after restore.
  after=pg_connect(c,SOURCE,readonly=True)
  try:
   with after:assert_project(after);report['source_after']=fingerprint(after);require(report['source_after']==report['source_before'],'PRODUCTION_SOURCE_CHANGED');require(acl_ownership(after)==report['source_acl_ownership'],'SOURCE_ACL_CHANGED')
  finally:after.close()
  print(json.dumps({'phase':'CLONE_AND_SOURCE_CHECKS_PASS','target':target}),flush=True)
  report['superset_metadata_backup']=backup_metadata(local)
  report.update(status='PASS_WAITING_REVIEW',duration_seconds=round(time.monotonic()-start,3),private_backup_directory=str(local.relative_to(ROOT)),source_data_model_preserved=True,object_owners_and_acl_preserved=True,global_roles_in_dump=False,database_level_acl_reapplied=False,database_comment_policy='Clone uses unique safety marker; source marker unchanged',full_refresh_executed=False,requirements_merged=False,step12a_completed=False)
  print(json.dumps({'status':report['status'],'run_id':rid,'target':target,'report':str(report_path.relative_to(ROOT)),'dw_sha256':h,'metadata_sha256':report['superset_metadata_backup']['sha256']}),flush=True)
  return 0
 except Exception as e:
  report.update(status='FAIL',error_code=e.code if isinstance(e,SafeError) else type(e).__name__,pgcode=getattr(e,'pgcode',None),duration_seconds=round(time.monotonic()-start,3))
  print(json.dumps({'status':'FAIL','error_code':report['error_code'],'target':target,'report':str(report_path.relative_to(ROOT))}),flush=True);return 2
 finally:
  for conn in [source,maintenance]:
   if conn is not None:conn.close()
  dump_json(report_path,report)
if __name__=='__main__':raise SystemExit(main())
