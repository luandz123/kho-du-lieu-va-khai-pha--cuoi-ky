"""DW-only reconstruction for a second checkout; no Superset/backup required.

Default plan-only. --apply creates a NEW guarded target, never demo or a clone.
"""
import argparse,json,uuid,sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from etl.s05_staging import config,verify_sources
from etl.integration_target import IntegrationPermit,integration_connect
from etl.run_etl import atomic_refresh,populate,verify_warehouse,atomic_json
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--raw-dir',type=Path);p.add_argument('--env-file',type=Path,default=ROOT/'.env');p.add_argument('--date',default='20261023');p.add_argument('--report',type=Path);a=p.parse_args()
 if not a.apply:print(json.dumps({'mode':'PLAN_ONLY','creates_database':False,'superset_required':False}));return
 assert a.raw_dir and a.report and not a.report.exists(),'RAW_AND_NEW_REPORT_REQUIRED'
 c=config(a.env_file);source=json.loads((ROOT/'data/source_manifest.json').read_text(encoding='utf-8'));verify_sources(a.raw_dir,source)
 rid=uuid.uuid4().hex;permit=IntegrationPermit('movielens_btl_int_'+a.date+'_'+rid[:8],rid,c['POSTGRES_USER'])
 m=psycopg2.connect(host=c['POSTGRES_HOST'],port=c['POSTGRES_PORT'],dbname='postgres',user=c['POSTGRES_USER'],password=c['POSTGRES_PASSWORD']);m.autocommit=True
 with m.cursor() as q:
  q.execute('SELECT 1 FROM pg_database WHERE datname=%s',(permit.database,));assert q.fetchone() is None,'TARGET_EXISTS'
  q.execute(sql.SQL('CREATE DATABASE {} OWNER {} TEMPLATE template0 ENCODING %s').format(sql.Identifier(permit.database),sql.Identifier(permit.owner)),('UTF8',))
  q.execute(sql.SQL('COMMENT ON DATABASE {} IS %s').format(sql.Identifier(permit.database)),(permit.marker,))
 m.close();x=integration_connect(c,permit);x.autocommit=True
 with x.cursor() as q:q.execute('SELECT set_config(%s,%s,false)',('btl.target_database',permit.database));q.execute((ROOT/'database/schema.sql').read_text(encoding='utf-8'))
 x.close();x=integration_connect(c,permit);progress={}
 result=atomic_refresh(x,lambda z:populate(z,a.raw_dir,source,progress),lambda z:verify_warehouse(z,a.raw_dir),progress=progress);x.close()
 x=integration_connect(c,permit)
 with x:
  with x.cursor() as q:q.execute((ROOT/'database/views.sql').read_text(encoding='utf-8'))
 x.close();atomic_json(a.report,{'run_id':rid,'database':permit.database,'owner':permit.owner,'transaction':result['transaction'],'canonical_hashes':result['checks']['canonical_hashes'],'row_counts':result['checks']['row_counts'],'superset_required':False,'p2_intake_g2':'NOT_CONFIRMED','g3_loaded':False})
 print(json.dumps({'status':'DW_RECREATED','target':permit.database,'p2_intake_confirmation_required':True}))
if __name__=='__main__':main()
