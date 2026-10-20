"""S11C scoped grants and fresh environment observation; never print credentials."""
import json,sys,subprocess,uuid
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'dashboard/overview'))
from etl.s05_staging import config,connect,sha256
from superset_api import SupersetAPI
D=ROOT/'dashboard/trends'
def main():
 c=connect(config(ROOT/'.env'))
 with c:
  with c.cursor() as q:
   q.execute("SELECT current_database(),shobj_description(oid,'pg_authid') FROM pg_roles WHERE rolname='movielens_bi_reader'")
   role=q.fetchone();assert role and role[0]=='movielens_btl' and role[1] and 'P1' in role[1]
   q.execute((D/'bi_grants.sql').read_text())
 c.close()
 # Reuse container-side privilege inspection but preserve the immutable 11A tool/report.
 from check_bi_reader import PAYLOAD
 old="r['selectable']==['dw.v_ml_movies','dw.v_ml_ratings']"
 new="r['selectable']==['analytics.v_olap_genre_quarter','analytics.v_olap_time_rollup','dw.v_ml_movies','dw.v_ml_ratings']"
 assert old in PAYLOAD
 from dotenv import dotenv_values
 payload=PAYLOAD.replace(old,new).replace('btl_s11a_reader_check','btl_s11c_reader_check')
 p=subprocess.run(['docker','exec','-i','btl-movielens-superset-web-1','python','-c',payload],input=json.dumps(dict(dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False))),text=True,capture_output=True,timeout=90)
 if p.returncode:raise RuntimeError('BI_CONTAINER_AUDIT_FAILED')
 r=json.loads(p.stdout)
 r.update(at_utc=datetime.now(timezone.utc).isoformat(),run_id=uuid.uuid4().hex,grant_sql=(D/'bi_grants.sql').read_text(),grant_sha256=sha256(D/'bi_grants.sql'),p2_intake_status='NOT_CONFIRMED',limits=['PUBLIC TEMP remains','No two-machine connectivity assertion'])
 (D/'evidence/bi_reader.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'status':r['status'],'selectable':r['selectable'],'writeable':r['writeable'],'session_read_only':r['session_read_only']}))
if __name__=='__main__':main()
