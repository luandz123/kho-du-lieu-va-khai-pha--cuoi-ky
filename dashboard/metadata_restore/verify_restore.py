"""Metadata-restored objects + independent SQL; identity mapping, no layout edits."""
import json,copy,time,uuid,hashlib,sys,subprocess
from datetime import datetime,timezone
from common import ROOT,D,RestoreAPI,SupersetAPI,production_objects,write
from etl.s05_staging import connect,config
sys.path.insert(0,str(ROOT/'dashboard/preferences'))
from prepare import model_snapshot
def near(a,b):return (a is None and b is None) or (a is not None and b is not None and abs(float(a)-float(b))<1e-8)
def main():
 start=time.monotonic();rid=uuid.uuid4().hex;api=RestoreAPI();prod=SupersetAPI()
 report={'run_id':rid,'at_utc':datetime.now(timezone.utc).isoformat(),'status':'FAIL','target':api.base,'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'code_state':'WORKING_TREE_NOT_COMMITTED','code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'verify_restore.py',D/'common.py']}}
 try:
  mapping=json.loads((D/'evidence/uuid_mapping.json').read_text())['old_id_to_new_id'];before=json.loads((D/'evidence/production_before.json').read_text(encoding='utf-8'));source=before['objects'];contexts={};baseline={}
  for old,new in mapping['dataset'].items():
   r=api.request('GET',f'/api/v1/dataset/{new}')['result'];s=source[f'dataset/{old}'];assert r['sql']==s['sql'] and r['main_dttm_col']==s['main_dttm_col']
  for old,new in mapping['chart'].items():
   r=api.request('GET',f'/api/v1/chart/{new}')['result'];p=json.loads(source[f'chart/{old}']['params']);p['datasource']=str(mapping['dataset'][p['datasource'].split('__')[0]])+'__table';actual=json.loads(r['params'])
   assert p==actual,('CHART_PARAMS_CHANGED',old)
   ctx=json.loads(r['query_context']);expected=json.loads(source[f'chart/{old}']['query_context']);expected['datasource']['id']=mapping['dataset'][str(expected['datasource']['id'])];expected['form_data']['datasource']=str(expected['datasource']['id'])+'__table';assert ctx==expected,('QUERY_CONTEXT_CHANGED',old)
   contexts[int(old)]=ctx
  def query(old,filters=None,time_range=None,override_metrics=None):
   ctx=copy.deepcopy(contexts[old]);ctx['force']=True
   if filters is not None:ctx['queries'][0]['filters']=filters
   if time_range is not None:ctx['queries'][0]['time_range']=time_range
   if override_metrics is not None:ctx['queries'][0]['metrics']=override_metrics
   res=api.request('POST','/api/v1/chart/data',ctx)['result'][0];assert res['status']=='success',('RESTORED_CHART_QUERY_FAILED',old);return res
  # Every restored chart queried, not just successful HTTP import.
  for old in sorted(contexts):baseline[old]=query(old)['data']
  report['all_23_charts_query_success']=True
  metrics=[{'expressionType':'SQL','sqlExpression':"MAX(current_user::text)",'label':'role','hasCustomLabel':True,'optionName':'role'},{'expressionType':'SQL','sqlExpression':"MAX(current_setting('TimeZone')::text)",'label':'timezone','hasCustomLabel':True,'optionName':'timezone'}]
  identity=query(16,override_metrics=metrics)['data'][0];assert identity=={'role':'movielens_bi_reader','timezone':'UTC'};report['engine']=identity
  c=connect(config(ROOT/'.env'));c.set_session(readonly=True,isolation_level='REPEATABLE READ');overview=[]
  with c:
   with c.cursor() as q:
    for label,tr,lo,hi in [('all','No filter',None,None),('Q3_2000','2000-07-01 : 2000-10-01','2000-07-01T00:00:00Z','2000-10-01T00:00:00Z')]:
     where='' if lo is None else ' WHERE f.rated_at >= %s::timestamptz AND f.rated_at < %s::timestamptz';args=() if lo is None else (lo,hi)
     q.execute('SELECT count(*),sum(rating),count(DISTINCT user_key),count(DISTINCT movie_key),sum(rating)::numeric/count(*) FROM dw.fact_rating f'+where,args);n,total,users,movies,mean=q.fetchone()
     q.execute('SELECT rating,count(*) FROM dw.fact_rating f'+where+' GROUP BY rating ORDER BY rating',args);stars=dict(q.fetchall())
     q.execute('SELECT m.movie_id,count(*),sum(rating)::numeric/count(*) FROM dw.fact_rating f JOIN dw.dim_movie m USING(movie_key)'+where+' GROUP BY m.movie_id ORDER BY count(*) DESC,sum(rating)::numeric/count(*) DESC,m.movie_id LIMIT 10',args);top=q.fetchall()
     actual={old:query(old,time_range='No filter' if old==5 else tr)['data'] for old in range(1,9)}
     for old,key,value in [(1,'rating_count',n),(3,'rated_users',users),(4,'rated_movies',movies),(5,'catalog_movies',3883),(6,'rating_sum',total)]:
      # Historical metric aliases are read from original config, not assumed.
      alias=json.loads(source[f'chart/{old}']['params'])['metric']['label'];assert actual[old][0][alias]==value,(label,old)
     mean_key=json.loads(source['chart/2']['params'])['metric']['label'];assert near(actual[2][0][mean_key],mean)
     assert {r['rating']:r['rating_count'] for r in actual[8]}==stars
     assert all(a['movie_id']==e[0] and a['rating_count']==e[1] and near(a['weighted_mean'],e[2]) for a,e in zip(actual[7],top))
     overview.append({'case':label,'status':'PASS','rating_count':n,'rating_sum':total,'rated_users':users,'rated_movies':movies,'actual':actual})
    assert [r['rating_count'] for r in overview]==[1000209,324864]
    q.execute("SELECT date_trunc('quarter',f.rated_at AT TIME ZONE 'UTC')::date,g.genre_name,count(*) FROM dw.fact_rating f JOIN dw.bridge_movie_genre b USING(movie_key) JOIN dw.dim_genre g USING(genre_key) GROUP BY 1,2 ORDER BY 1,2");series=q.fetchall()
    quarters=sorted({r[0] for r in series});genres=sorted({r[1] for r in series});counts={(qt,g):n for qt,g,n in series};computed={}
    for i,qt in enumerate(quarters):
     denom=sum(counts.get((qt,g),0) for g in genres);rankable=[]
     for g in genres:
      n=counts.get((qt,g),0);prev=counts.get((quarters[i-1],g),0) if i else None;eligible=i>1 and i<len(quarters)-1 and prev>=100
      row={'rating_count':n,'previous_rating_count':prev,'genre_assignment_total':denom,'genre_share_pct':100*n/denom,'qoq_pct':None if not prev else 100*(n-prev)/prev,'growth_rank':None};computed[(qt,g)]=row
      if eligible:rankable.append((g,row))
     for rank,(g,row) in enumerate(sorted(rankable,key=lambda t:(-t[1]['qoq_pct'],-t[1]['rating_count'],t[0])),1):row['growth_rank']=rank
    filters=[{'col':'quarter_label','op':'IN','val':['2001 Q1']},{'col':'genre_name','op':'IN','val':['Animation']}]
    trend=query(13,filters=filters)['data'];assert len(trend)==1;expected=computed[(next(qt for qt in quarters if str(qt)=='2001-01-01'),'Animation')]
    assert all(near(trend[0][k],v) for k,v in expected.items());assert trend[0]['rating_count']==1715 and trend[0]['previous_rating_count']==20068
    all_trend=baseline[13];same=next(r for r in all_trend if r['quarter_label']=='2001 Q1' and r['genre_name']=='Animation');assert all(near(trend[0][k],same[k]) for k in expected)
    # All four trend charts also query with categorical quarter/genre filters.
    trend_charts={old:query(old,filters=filters if old!=9 else filters[:1])['data'] for old in range(9,14)}
    q.execute("SELECT c.cluster_id,u.gender,u.age_group,count(*) FROM analytics.user_cluster c JOIN analytics.model_registry r USING(model_version) JOIN dw.dim_user u USING(user_id) WHERE r.is_active AND r.is_valid_for_dw AND c.status='assigned' GROUP BY 1,2,3");cube=q.fetchall()
    q.execute('SELECT p.cluster_id,p.genre_name,p.mean_preference FROM analytics.cluster_genre_profile p JOIN analytics.model_registry r USING(model_version) WHERE r.is_active AND r.is_valid_for_dw');profiles=q.fetchall()
  c.close();preferences=[]
  for label,cs,ages,gs in [('all',None,None,None),('cluster1_F_25_34',[1],['25-34'],['F'])]:
   actual={}
   for old in range(14,24):
    filters=[]
    if old in [14,17,19,20,22]:
     if cs:filters.append({'col':'cluster_id','op':'IN','val':cs})
     if old!=19:
      if ages:filters.append({'col':'age_group','op':'IN','val':ages})
      if gs:filters.append({'col':'gender','op':'IN','val':gs})
    actual[old]=query(old,filters=filters)['data']
   selected=[t for t in cube if (not cs or t[0] in cs) and (not ages or t[2] in ages) and (not gs or t[1] in gs)];n=sum(t[3] for t in selected)
   assert actual[14][0]['assigned_users']==n and actual[15][0]['insufficient_users']==2 and actual[16][0]['fixed_assigned_baseline']==6038
   expected_profile={(cid,g):float(v) for cid,g,v in profiles if not cs or cid in cs};assert len(actual[19])==len(expected_profile)
   assert all(near(r['mean_preference'],expected_profile[(int(r['cluster_label'][0]),r['genre_name'])]) for r in actual[19])
   for old,idx,field,bfield in [(20,1,'gender','gender'),(22,2,'age_group','age')]:
    for row in actual[old]:
     cid=int(row['cluster_label'][0]);value=row[field];expected_n=sum(t[3] for t in selected if t[0]==cid and t[idx]==value);original=sum(t[3] for t in cube if t[0]==cid);bn=sum(t[3] for t in cube if t[idx]==value)
     assert row['assigned_users']==expected_n and row['original_cluster_users']==original and near(row['pct_of_original_cluster'],100*expected_n/original) and row['baseline_'+bfield+'_users']==bn and near(row['baseline_'+bfield+'_pct'],100*bn/6038)
   preferences.append({'case':label,'status':'PASS','assigned':n,'baseline_fixed':6038,'insufficient_fixed':2,'heatmap_cells':len(expected_profile),'actual':actual})
  assert [r['assigned'] for r in preferences]==[6038,170]
  assert before['objects']==production_objects(prod),'PRODUCTION_BUSINESS_CONFIG_CHANGED';assert before['database']==model_snapshot(),'SOURCE_MODEL_CHANGED'
  # Production still queries after isolated import and checks, including a filter.
  prod_checks={}
  for old,tr,filters in [(1,'No filter',None),(1,'2000-07-01 : 2000-10-01',None),(13,None,[{'col':'quarter_label','op':'IN','val':['2001 Q1']},{'col':'genre_name','op':'IN','val':['Animation']}]),(14,None,[{'col':'cluster_id','op':'IN','val':[1]},{'col':'age_group','op':'IN','val':['25-34']},{'col':'gender','op':'IN','val':['F']}])]:
   ctx=json.loads(source[f'chart/{old}']['query_context']);ctx['force']=True
   if tr is not None:ctx['queries'][0]['time_range']=tr
   if filters is not None:ctx['queries'][0]['filters']=filters
   res=prod.request('POST','/api/v1/chart/data',ctx)['result'][0];assert res['status']=='success';prod_checks[str(old)+'_'+str(tr)]=res['data']
  report.update(status='PASS',duration_seconds=round(time.monotonic()-start,3),dataset_sql_and_time_columns_exact=True,all_chart_metrics_and_contexts_remapped_exact=True,metadata_restore_identity_mapping=True,overview_cases=overview,trend_animation={'status':'PASS','expected_independent_fact_sql_python':expected,'actual':trend,'all_filtered_charts':trend_charts,'share_rank_unchanged_by_display_filter':True},preferences_cases=preferences,all_32_production_business_objects_unchanged=True,source_model_registry_fingerprints_unchanged=True,production_live=prod_checks,p2_intake_status='NOT_CONFIRMED',ui_verification_separate=True)
  write('evidence/restore_verification.json',report);print(json.dumps({'status':'PASS','run_id':rid,'seconds':report['duration_seconds'],'all_charts':23,'overview_counts':[r['rating_count'] for r in overview],'preferences':[r['assigned'] for r in preferences],'production_unchanged':True}))
 except Exception as e:
  report['error_category']=str(e)[:180] if isinstance(e,AssertionError) else type(e).__name__;write(f'evidence/restore_verification_FAIL_{rid}.json',report);raise
if __name__=='__main__':main()
