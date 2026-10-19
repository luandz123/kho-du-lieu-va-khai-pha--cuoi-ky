"""Independent fact SQL versus saved Superset chart query contexts; aggregate evidence only."""
import copy,json,time,uuid,re
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from etl.s05_staging import ROOT,config,connect,sha256
from superset_api import SupersetAPI
D=ROOT/'dashboard/overview'
def main():
 start=time.monotonic();api=SupersetAPI();ids=json.loads((D/'object_ids.json').read_text(encoding='utf-8'));defs=json.loads((D/'chart_definitions.json').read_text(encoding='utf-8'))
 conn=connect(config(ROOT/'.env'));conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
 report={'run_id':uuid.uuid4().hex,'at_utc':datetime.now(timezone.utc).isoformat(),'status':'FAIL','source':'Independent fact SQL vs Superset chart/data API using actual BI database','chart_contexts_source':'saved chart definitions','cases':[],'code_sha256':{p:sha256(ROOT/p) for p in ['dashboard/overview/reconcile.py','dashboard/overview/ratings_dataset.sql','dashboard/overview/catalog_dataset.sql','dashboard/overview/metrics.json']}}
 cases=[('all_history','No filter',None,None),('2000_q3','2000-07-01 : 2000-10-01','2000-07-01T00:00:00Z','2000-10-01T00:00:00Z'),('2001_q1','2001-01-01 : 2001-04-01','2001-01-01T00:00:00Z','2001-04-01T00:00:00Z')]
 with conn:
  for name,timerange,lo,hi in cases:
   where='' if lo is None else ' WHERE f.rated_at >= %s::timestamptz AND f.rated_at < %s::timestamptz';args=() if lo is None else (lo,hi)
   with conn.cursor() as c:
    c.execute('SELECT count(*),sum(f.rating),count(DISTINCT f.user_key),count(DISTINCT f.movie_key),sum(f.rating)::numeric/count(*) FROM dw.fact_rating f'+where,args);n,total,users,movies,mean=c.fetchone()
    c.execute('SELECT f.rating,count(*) FROM dw.fact_rating f'+where+' GROUP BY f.rating ORDER BY f.rating',args);stars=[{'rating':r,'rating_count':count} for r,count in c.fetchall()]
    c.execute('SELECT m.movie_id,m.title,count(*),sum(f.rating)::numeric/count(*) FROM dw.fact_rating f JOIN dw.dim_movie m ON m.movie_key=f.movie_key'+where+' GROUP BY m.movie_id,m.title ORDER BY count(*) DESC,sum(f.rating)::numeric/count(*) DESC,m.movie_id ASC LIMIT 10',args);top=[{'movie_id':i,'title':title,'rating_count':n,'weighted_mean':str(avg)} for i,title,n,avg in c.fetchall()]
   expected={'ratings':n,'sum':total,'users':users,'movies':movies,'catalog':3883,'mean':str(mean),'stars':stars,'top10':top};actual={};queries={}
   for key,d in defs.items():
    ctx=copy.deepcopy(d['query_context']);ctx['force']=True
    ctx['queries'][0]['time_range']='No filter' if key=='catalog' else timerange
    r=api.request('POST','/api/v1/chart/data',ctx)['result'][0];assert r['status']=='success',key
    data=r['data'];queries[key]=r['query']
    if key in ['stars','top10']:actual[key]=data
    else:actual[key]=data[0][d['form_data']['metric']['label']]
   for key in ['ratings','sum','users','movies','catalog']:assert actual[key]==expected[key],(name,key)
   assert abs(Decimal(str(actual['mean']))-Decimal(expected['mean']))<Decimal('1e-12')
   assert sorted(actual['stars'],key=lambda x:x['rating'])==expected['stars']
   assert len(actual['top10'])==10
   for a,e in zip(actual['top10'],expected['top10']):
    assert all(a[k]==e[k] for k in ['movie_id','title','rating_count']) and abs(Decimal(str(a['weighted_mean']))-Decimal(e['weighted_mean']))<Decimal('1e-12')
   if lo:
    topquery=re.sub(r'--[^\n]*','',queries['top10']);assert topquery.index('WHERE rated_at_utc')<topquery.index('GROUP BY')<topquery.index('ORDER BY')<topquery.index('LIMIT 10')
   report['cases'].append({'case':name,'time_range':timerange,'status':'PASS','expected':expected,'superset_actual':actual,'generated_queries':queries})
  with conn.cursor() as c:
   c.execute("WITH x(id,n,s) AS (VALUES (9,2,8),(3,2,8),(1,2,7),(2,3,6)) SELECT id FROM x ORDER BY ROW(n,s::numeric/n,-id) DESC");assert [x[0] for x in c.fetchall()]==[2,3,9,1]
 conn.close();assert [x['expected']['ratings'] for x in report['cases']]==[1000209,324864,32223]
 report.update(status='PASS',tie_fixture='count desc / mean desc / original movie_id asc; synthetic VALUES passed',duration_seconds=round(time.monotonic()-start,3),p2_intake_status='NOT_CONFIRMED',dedicated_bi_reader_verified_separately=True)
 (D/'evidence/reconciliation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','run_id':report['run_id'],'cases':[{'case':r['case'],'ratings':r['expected']['ratings'],'sum':r['expected']['sum'],'users':r['expected']['users'],'movies':r['expected']['movies']} for r in report['cases']],'duration_seconds':report['duration_seconds']}))
if __name__=='__main__':main()
