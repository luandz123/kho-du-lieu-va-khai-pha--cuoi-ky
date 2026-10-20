"""Independent base-table aggregate SQL vs actual Superset engine, no user export."""
import sys,json,copy,uuid,time,subprocess,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'dashboard/overview'),str(ROOT/'dashboard/preferences')]
from etl.s05_staging import connect,config,sha256
from superset_api import SupersetAPI
from prepare import objects,model_snapshot,write
D=ROOT/'dashboard/preferences'
def close(a,b):return abs(float(a)-float(b))<1e-8
def main():
 start=time.monotonic();api=SupersetAPI();rid=uuid.uuid4().hex
 report={'run_id':rid,'at_utc':datetime.now(timezone.utc).isoformat(),'status':'FAIL','base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'cases':[],'code_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha256(p) for p in D.glob('*') if p.suffix in ['.py','.sql']}}
 try:
  c=connect(config(ROOT/'.env'));c.set_session(readonly=True,isolation_level='REPEATABLE READ')
  with c:
   with c.cursor() as q:
    # Independent aggregate tables, NOT the virtual datasets or active-view SQL.
    q.execute('''SELECT c.cluster_id,u.gender,u.age_group,count(*) FROM analytics.user_cluster c JOIN analytics.model_registry r USING(model_version) JOIN dw.dim_user u USING(user_id) WHERE r.is_active AND r.is_valid_for_dw AND c.status='assigned' GROUP BY 1,2,3 ORDER BY 1,2,3''');cube=q.fetchall()
    q.execute('''SELECT p.cluster_id,p.genre_name,p.mean_preference,p.n_users FROM analytics.cluster_genre_profile p JOIN analytics.model_registry r USING(model_version) WHERE r.is_active AND r.is_valid_for_dw ORDER BY 1,2''');profile=q.fetchall()
    q.execute("SELECT count(*) FROM analytics.user_cluster c JOIN analytics.model_registry r USING(model_version) WHERE r.is_active AND r.is_valid_for_dw AND c.status='insufficient_evidence' AND c.cluster_id IS NULL");assert q.fetchone()[0]==2
  c.close();assert sum(r[3] for r in cube)==6038 and len(profile)==72
  counts={k:sum(n for cid,g,a,n in cube if cid==k) for k in range(4)};assert list(counts.values())==[2478,1393,760,1407]
  bg={g:sum(n for cid,gg,a,n in cube if gg==g) for g in ['F','M']};ba={a:sum(n for cid,g,aa,n in cube if aa==a) for a in sorted({r[2] for r in cube})}
  defs=json.loads((D/'chart_definitions.json').read_text(encoding='utf-8'));ids=json.loads((D/'object_ids.json').read_text())
  # Actual engine identity, not a READ ONLY session assertion.
  ctx=copy.deepcopy(defs['baseline']['query_context']);ctx['queries'][0]['metrics']=[{'expressionType':'SQL','sqlExpression':"MAX(current_user::text)",'label':'engine_role','hasCustomLabel':True,'optionName':'engine_role'},{'expressionType':'SQL','sqlExpression':"MAX(current_setting('TimeZone')::text)",'label':'engine_timezone','hasCustomLabel':True,'optionName':'engine_timezone'}]
  r=api.request('POST','/api/v1/chart/data',ctx)['result'][0];assert r['status']=='success';assert r['data']==[{'engine_role':'movielens_bi_reader','engine_timezone':'UTC'}];report['engine']=r['data'][0]
  for name,clusters,ages,genders in [('all',None,None,None),('cluster_3',[3],None,None),('cluster_1_age25_34_female',[1],['25-34'],['F'])]:
   actual={};queries={}
   for key,e in defs.items():
    saved=api.request('GET',f'/api/v1/chart/{e["chart_id"]}')['result'];assert json.loads(saved['params'])==e['form_data'] and json.loads(saved['query_context'])==e['query_context']
    ctx=copy.deepcopy(e['query_context']);ctx['force']=True;filters=[]
    if key not in ['insufficient','baseline','model','baseline_gender','baseline_age']:
     if clusters:filters.append({'col':'cluster_id','op':'IN','val':clusters})
     if key!='heatmap':
      if ages:filters.append({'col':'age_group','op':'IN','val':ages})
      if genders:filters.append({'col':'gender','op':'IN','val':genders})
    ctx['queries'][0]['filters']=filters;r=api.request('POST','/api/v1/chart/data',ctx)['result'][0]
    assert r['status']=='success',(key,r.get('error'));actual[key]=r['data'];queries[key]=r['query']
   selected=[r for r in cube if (not clusters or r[0] in clusters) and (not ages or r[2] in ages) and (not genders or r[1] in genders)]
   total=sum(r[3] for r in selected)
   assert actual['assigned'][0]['assigned_users']==total and actual['insufficient'][0]['insufficient_users']==2 and actual['baseline'][0]['fixed_assigned_baseline']==6038
   assert actual['model']==[{'model_version':'kmeans_k4_seed42','assigned_users':6038,'insufficient_users':2}]
   assert len(actual['size'])==len({r[0] for r in selected})
   for r in actual['size']:
    cid=int(r['cluster_label'][0]);n=sum(n for cc,g,a,n in selected if cc==cid);assert r['assigned_users']==n and close(r['pct_of_fixed_6038'],100*n/6038)
   for key,dimension,baseline_counts,index in [('gender','gender',bg,1),('age','age_group',ba,2)]:
    assert len(actual[key])==len({(r[0],r[index]) for r in selected})
    for r in actual[key]:
     cid=int(r['cluster_label'][0]);v=r[dimension];n=sum(t[3] for t in selected if t[0]==cid and t[index]==v)
     assert r['assigned_users']==n and r['original_cluster_users']==counts[cid] and close(r['pct_of_original_cluster'],100*n/counts[cid])
     assert r['baseline_'+key+'_users']==baseline_counts[v] and close(r['baseline_'+key+'_pct'],100*baseline_counts[v]/6038)
   for key,dim,expected in [('baseline_gender','gender',bg),('baseline_age','age_group',ba)]:assert {r[dim]:r['assigned_users'] for r in actual[key]}==expected
   expected={(cid,g):float(m) for cid,g,m,n in profile if not clusters or cid in clusters};assert len(actual['heatmap'])==len(expected)
   assert all(close(r['mean_preference'],expected[(int(r['cluster_label'][0]),r['genre_name'])]) for r in actual['heatmap'])
   report['cases'].append({'case':name,'status':'PASS','cluster':clusters,'age_group':ages,'gender':genders,'assigned':total,'insufficient_fixed':2,'baseline_fixed':6038,'heatmap_cells':len(expected),'actual_aggregates':actual,'generated_queries':queries})
  before=json.loads((D/'evidence/before.json').read_text(encoding='utf-8'));after=objects(api);assert before['objects']==after,'EXISTING_BUSINESS_CONFIG_CHANGED';assert before['database']==model_snapshot(),'SOURCE_OR_MODEL_CHANGED'
  report['existing_dashboards_live']={}
  for cid,label,filters,expected in [(1,'11A_all',[],1000209),(1,'11A_Q3_2000',None,324864),(9,'11C_all',[],None),(9,'11C_Q1_2001',[{'col':'quarter_label','op':'IN','val':['2001 Q1']}],32223),(13,'11C_Animation_Q1_2001',[{'col':'quarter_label','op':'IN','val':['2001 Q1']},{'col':'genre_name','op':'IN','val':['Animation']}],None)]:
   ctx=json.loads(api.request('GET',f'/api/v1/chart/{cid}')['result']['query_context']);ctx['force']=True
   if filters is None:ctx['queries'][0]['time_range']='2000-07-01 : 2000-10-01'
   else:ctx['queries'][0]['filters']=filters
   r=api.request('POST','/api/v1/chart/data',ctx)['result'][0];assert r['status']=='success'
   if expected is not None:assert r['data'][0]['rating_count']==expected,(label,r['data'])
   if label=='11C_Animation_Q1_2001':assert close(r['data'][0]['qoq_pct'],100*(1715-20068)/20068)
   report['existing_dashboards_live'][label]=r['data']
  write('evidence/existing_after.json',after);report.update(status='PASS',duration_seconds=round(time.monotonic()-start,3),all_19_existing_objects_unchanged=True,staging_dw_model_unchanged=True,cluster_sizes=counts,fixed_gender_baseline=bg,fixed_age_baseline=ba,p2_intake_status='NOT_CONFIRMED',package_unchanged=True)
 except Exception as e:
  report['error_category']=str(e)[:180] if isinstance(e,AssertionError) else type(e).__name__
  write(f'evidence/reconciliation_FAIL_{rid}.json',report);raise
 write('evidence/reconciliation.json',report);print(json.dumps({'status':'PASS','run_id':rid,'cases':[{k:r[k] for k in ['case','assigned','heatmap_cells']} for r in report['cases']],'seconds':report['duration_seconds']}))
if __name__=='__main__':main()
