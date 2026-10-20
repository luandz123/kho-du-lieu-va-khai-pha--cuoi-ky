"""Read-only independent fact aggregates vs saved live Superset charts, three cases.

Python independently constructs the complete grid, share, lag and global rank.
Native-filter UI verification is separate; this runner verifies API semantics.
"""
import sys,json,copy,uuid,time,subprocess,hashlib
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'dashboard/overview'))
from etl.s05_staging import connect,config,sha256
from superset_api import SupersetAPI
D=ROOT/'dashboard/trends'
def snapshot(s):
 before=json.loads((D/'evidence/overview_before.json').read_text(encoding='utf-8'));after={}
 for key,fields in before.items():
  r=s.request('GET','/api/v1/'+key)['result'];after[key]={k:r.get(k) for k in fields}
 assert before==after,'OVERVIEW_CONFIG_CHANGED'
 return after
def close(a,b):
 if a is None or b is None:return a is None and b is None
 return abs(Decimal(str(a))-Decimal(str(b)))<Decimal('0.000000001')
def main():
 start=time.monotonic();s=SupersetAPI();report={'run_id':uuid.uuid4().hex,'at_utc':datetime.now(timezone.utc).isoformat(),'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':'FAIL','cases':[],'expected_source':'independent fact/bridge aggregates then Python Decimal full-grid/lag/share/rank','code_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha256(p) for p in D.glob('*') if p.suffix in ['.py','.sql']}}
 c=connect(config(ROOT/'.env'));c.set_session(readonly=True,isolation_level='REPEATABLE READ')
 with c:
  with c.cursor() as q:
   sql=(D/'reconciliation.sql').read_text().split(';');q.execute(sql[0]);system={f'{d.year} Q{(d.month-1)//3+1}':{'rating_count':n,'rating_sum':total} for d,n,total in q.fetchall()}
   q.execute(sql[1]);counts={(f'{d.year} Q{(d.month-1)//3+1}',g):n for d,g,n in q.fetchall()}
   q.execute('SELECT genre_name FROM dw.dim_genre ORDER BY genre_name');genres=[r[0] for r in q.fetchall()]
   q.execute("SELECT count(*) FROM (SELECT b.movie_key FROM dw.bridge_movie_genre b JOIN dw.dim_genre g USING(genre_key) GROUP BY b.movie_key HAVING bool_or(g.genre_name='Comedy') AND count(*)>1) x");multi=q.fetchone()[0];assert multi>0
   q.execute("SELECT (SELECT count(*) FROM analytics.model_registry),(SELECT count(*) FROM analytics.user_cluster),(SELECT count(*) FROM analytics.cluster_genre_profile)");analytics=list(q.fetchone());assert analytics==[0,0,0]
 quarters=sorted(system);assert len(quarters)==12 and sum(x['rating_count'] for x in system.values())==1000209 and sum(x['rating_sum'] for x in system.values())==3582313
 expected={}
 for i,qt in enumerate(quarters):
  total=sum(counts.get((qt,g),0) for g in genres);rankable=[]
  for g in genres:
   n=counts.get((qt,g),0);prev=counts.get((quarters[i-1],g),0) if i else None;edge=i in [0,len(quarters)-1];eligible=i>1 and not edge and prev>=100
   row={'quarter_label':qt,'genre_name':g,'rating_count':n,'previous_rating_count':prev,'genre_assignment_total':total,'genre_share_pct':Decimal(100)*n/total,'qoq_pct':None if not prev else Decimal(100)*(n-prev)/prev,'growth_rank':None,'is_boundary_partial':edge,'eligible_for_ranking':eligible}
   expected[(qt,g)]=row
   if eligible:rankable.append(row)
  for rank,row in enumerate(sorted(rankable,key=lambda r:(-r['qoq_pct'],-r['rating_count'],r['genre_name'])),1):row['growth_rank']=rank
 assert sum(r['growth_rank'] is not None for r in expected.values())==156
 defs={}
 for key,entry in json.loads((D/'chart_definitions.json').read_text(encoding='utf-8')).items():
  actual=s.request('GET',f'/api/v1/chart/{entry["chart_id"]}')['result'];assert json.loads(actual['params'])==entry['form_data'];assert json.loads(actual['query_context'])==entry['query_context'];defs[key]=json.loads(actual['query_context'])
 cases=[('all_quarters_all_genres',quarters,genres),('comedy_2000q4_2001q1',['2000 Q4','2001 Q1'],['Comedy']),('three_genres_2001q1_2002q2',[q for q in quarters if '2001 Q1'<=q<='2002 Q2'],['Animation','Horror','Western'])]
 for name,qs,gs in cases:
  results={};queries={}
  for key,ctx in defs.items():
   ctx=copy.deepcopy(ctx);ctx['force']=True;query=ctx['queries'][0];query['filters']=[{'col':'quarter_label','op':'IN','val':qs}]
   if key!='system':query['filters'].append({'col':'genre_name','op':'IN','val':gs})
   response=s.request('POST','/api/v1/chart/data',ctx)['result'][0];assert response['status']=='success';results[key]=response['data'];queries[key]=response['query']
  assert len(results['system'])==len(qs)
  for a in results['system']:assert a['rating_count']==system[a['quarter_label']]['rating_count']
  for key in ['genre_count','qoq','share','detail']:
   rows=results[key];assert len(rows)==len(qs)*len(gs),(name,key)
   fields={'genre_count':['rating_count'],'qoq':['qoq_pct'],'share':['genre_share_pct'],'detail':['rating_count','previous_rating_count','genre_assignment_total','genre_share_pct','qoq_pct','growth_rank']}[key]
   for a in rows:
    e=expected[(a['quarter_label'],a['genre_name'])]
    assert all(close(a[k],e[k]) for k in fields),(name,key,a['quarter_label'],a['genre_name'])
    if key=='detail':
     assert ('Quý biên' in a['ranking_status'])==e['is_boundary_partial']
     if e['growth_rank']==1 and e['qoq_pct']<0:assert a['rank_interpretation']=='Hạng 1: giảm ít nhất'
  report['cases'].append({'case':name,'status':'PASS','selected_quarters':qs,'selected_genres':gs,'system_unique_ratings':sum(system[q]['rating_count'] for q in qs),'genre_rows':len(results['detail']),'superset_actual':results,'generated_queries':queries,'first_visible_rows':[r for r in results['detail'] if r['quarter_label']==qs[0]]})
 # Synthetic missing-quarter/previous-zero proof, entirely in memory; no source edits.
 def lag(rows):
  out=[];prev=None
  for x in rows:
   out.append(None if not prev else Decimal(100)*(x-prev)/prev);prev=x
  return out
 fixture=[10,0,5];assert lag(fixture)==[None,Decimal(-100),None]
 # Preserve 11A config AND execute its saved KPI/Top10 through the live BI engine.
 after=snapshot(s);overview={}
 for cid,key in [(1,'ratings'),(7,'top10')]:
  ctx=json.loads(s.request('GET',f'/api/v1/chart/{cid}')['result']['query_context']);ctx['force']=True;r=s.request('POST','/api/v1/chart/data',ctx)['result'][0];assert r['status']=='success';overview[key]=r['data']
 assert overview['ratings'][0]['rating_count']==1000209 and overview['top10'][0]['movie_id']==2858 and overview['top10'][0]['rating_count']==3428
 (D/'evidence/overview_after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 report.update(status='PASS',duration_seconds=round(time.monotonic()-start,3),overview_unchanged=True,overview_live_api=overview,comedy_movies_with_multiple_genres=multi,analytics_counts=analytics,zero_fill_previous_zero_fixture={'input':fixture,'qoq':[None,-100,None],'status':'PASS'},boundary_quarters=[quarters[0],quarters[-1]],ranked_cells=156,p2_intake_status='NOT_CONFIRMED',full_refresh_rerun=False)
 (D/'evidence/reconciliation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','run_id':report['run_id'],'seconds':report['duration_seconds'],'cases':[{k:r[k] for k in ['case','system_unique_ratings','genre_rows']} for r in report['cases']]}))
if __name__=='__main__':main()
