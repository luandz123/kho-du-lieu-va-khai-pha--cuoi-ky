"""Read-only VALUES fixture: native filters must not renormalize fixed baseline.

No schema, table, registry, G3 payload or production analytics writes.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from etl.s05_staging import connect,config
def main():
 c=connect(config(ROOT/'.env'));c.set_session(readonly=True)
 sql="""WITH user_fixture(cluster_id,status,gender,age_group) AS
 (VALUES (0,'assigned','F','25-34'),(0,'assigned','M','25-34'),
         (0,'assigned','M','18-24'),(1,'assigned','F','25-34'),
         (NULL,'insufficient_evidence','F','25-34')),
 windows AS (SELECT *,count(*) FILTER(WHERE status='assigned') OVER() total,
 count(*) FILTER(WHERE status='assigned') OVER(PARTITION BY cluster_id) cluster_n,
 count(*) FILTER(WHERE status='assigned') OVER(PARTITION BY gender) gender_n
 FROM user_fixture)
 SELECT count(*),max(total),max(cluster_n),max(gender_n),
 100.0*count(*)/max(total),100.0*count(*)/max(cluster_n)
 FROM windows WHERE status='assigned' AND cluster_id=0 AND gender='F'"""
 with c:
  with c.cursor() as q:
   q.execute("SELECT current_setting('transaction_read_only')");assert q.fetchone()[0]=='on'
   q.execute(sql);r=q.fetchone();assert r[:4]==(1,4,3,2) and float(r[4])==25 and abs(float(r[5])-100/3)<1e-10
   # Positive-preference fixture has 2 genres but must not fan out user counts.
   q.execute("WITH u(id) AS(VALUES(1),(2),(3)), p(genre,preference,n_users) AS(VALUES('A',0.7,3),('B',0.3,3)) SELECT (SELECT count(*) FROM u),sum(preference),max(n_users),sum(n_users) FROM p")
   a=q.fetchone();assert a[0]==3 and float(a[1])==1 and a[2]==3 and a[3]==6
 c.close()
 report={'status':'PASS','checks':{'session_read_only':True,'filtered_count':r[0],'fixed_assigned_denominator':r[1],'original_cluster_denominator':r[2],'fixed_gender_baseline':r[3],'selected_share_pct':float(r[4]),'cluster_share_pct':float(r[5]),'profile_genres':2,'true_users':a[0],'sum_repeated_n_users_is_wrong':a[3]},'production_writes':False}
 (ROOT/'dashboard/preferences/evidence/fixture.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
