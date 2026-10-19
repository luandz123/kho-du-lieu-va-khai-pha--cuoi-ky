"""Verify effective BI privileges from the existing Superset container, no secrets logged."""
import json,subprocess,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[2]
PAYLOAD=r'''
import json,sys,psycopg2
c=json.load(sys.stdin);r={}
conn=psycopg2.connect(host=c['POSTGRES_HOST'],port=c['POSTGRES_PORT'],dbname=c['POSTGRES_DB'],user=c['POSTGRES_USER'],password=c['POSTGRES_PASSWORD'],connect_timeout=10,application_name='btl_s11a_reader_check')
with conn:
 with conn.cursor() as q:
  q.execute("SELECT current_user,current_database(),current_setting('transaction_read_only')");a=q.fetchone();r.update(role=a[0],database=a[1],session_read_only=a[2])
  q.execute('SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolinherit FROM pg_roles WHERE rolname=current_user');r['attributes']=dict(zip(['superuser','createdb','createrole','replication','bypassrls','inherit'],q.fetchone()))
  q.execute("SELECT rolname FROM pg_roles WHERE rolname<>current_user AND pg_has_role(current_user,oid,'MEMBER')");r['memberships']=[a[0] for a in q.fetchall()]
  q.execute("SELECT n.nspname||'.'||c.relname,has_table_privilege(current_user,c.oid,'SELECT'),has_table_privilege(current_user,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('staging','dw','analytics') AND c.relkind IN ('r','v','m','p') ORDER BY 1");a=q.fetchall();r['relations_checked']=len(a);r['selectable']=[n for n,s,w in a if s];r['writeable']=[n for n,s,w in a if w]
  q.execute("SELECT nspname,has_schema_privilege(current_user,oid,'CREATE') FROM pg_namespace WHERE nspname IN ('staging','dw','analytics','public')");r['schema_create']=dict(q.fetchall())
  q.execute("SELECT has_database_privilege(current_user,current_database(),'CREATE'),has_database_privilege(current_user,current_database(),'TEMP')");r['database_create'],r['public_default_temp']=q.fetchone()
  q.execute('SELECT count(*),sum(rating),count(DISTINCT user_id),count(DISTINCT movie_id) FROM dw.v_ml_ratings');r['kpi']=list(q.fetchone())
  q.execute('SELECT count(*) FROM dw.v_ml_movies');r['catalog_count']=q.fetchone()[0]
try:
 with conn:
  with conn.cursor() as q:q.execute('UPDATE dw.fact_rating SET rating=rating WHERE false')
 r['update_sqlstate']='UNEXPECTED_PERMISSION'
except psycopg2.Error as e:r['update_sqlstate']=e.pgcode
conn.close()
assert not any(r['attributes'].values()) and not r['memberships'] and not r['writeable'] and not any(r['schema_create'].values()) and not r['database_create']
assert r['selectable']==['dw.v_ml_movies','dw.v_ml_ratings'] and r['update_sqlstate']=='42501'
assert r['kpi']==[1000209,3582313,6040,3706] and r['catalog_count']==3883
r['status']='PASS';print(json.dumps(r))
'''
def main():
 c=dict(dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False))
 p=subprocess.run(['docker','exec','-i','btl-movielens-superset-web-1','python','-c',PAYLOAD],input=json.dumps(c),text=True,capture_output=True,timeout=90)
 if p.returncode:print(json.dumps({'status':'FAIL','error_category':'CONTAINER_PRIVILEGE_CHECK_FAILED'}));return 2
 r=json.loads(p.stdout);r.update(at_utc=datetime.now(timezone.utc).isoformat(),run_id=uuid.uuid4().hex,origin='Superset web container',p2_intake_status='NOT_CONFIRMED')
 out=ROOT/'dashboard/overview/evidence/bi_reader_final.json';out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':r['status'],'relations_checked':r['relations_checked'],'writeable':r['writeable'],'session_read_only':r['session_read_only'],'update_sqlstate':r['update_sqlstate']}));return 0
if __name__=='__main__':raise SystemExit(main())
