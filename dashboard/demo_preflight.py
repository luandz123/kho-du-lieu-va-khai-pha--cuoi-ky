"""Read-only 8089 demo preflight. No grants, ETL, reload, or metadata edits.

Official login/chart query APIs may populate Superset query caches only.
All persisted output is aggregate and contains no credentials/user history.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import copy, hashlib, json, subprocess, sys, time, uuid, urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'dashboard/overview')]
from superset_api import SupersetAPI
from etl.s05_staging import config,connect

DEST=ROOT/'results/warehouse/demo_preflight_20261025'
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
def state():
    names=['btl-movielens-superset-metadata-1','btl-movielens-superset-web-1']
    rows=json.loads(subprocess.check_output(['docker','inspect',*names],encoding='utf-8'))
    return [{k:v for k,v in {'name':r['Name'],'id':r['Id'],'status':r['State']['Status'],'health':r['State'].get('Health',{}).get('Status'),'exit_code':r['State']['ExitCode'],'oom_killed':r['State']['OOMKilled'],'image':r['Config']['Image'],'started_at':r['State']['StartedAt'],'finished_at':r['State']['FinishedAt']}.items()} for r in rows]
def objects(api):
    r={}
    for cid in range(1,24):
        x=api.request('GET',f'/api/v1/chart/{cid}')['result']
        r['chart/'+str(cid)]={k:x.get(k) for k in ['uuid','params','query_context','datasource_id','datasource_type','viz_type']}
    for did in range(1,4):
        x=api.request('GET',f'/api/v1/dashboard/{did}')['result']
        r['dashboard/'+str(did)]={k:x.get(k) for k in ['uuid','position_json','json_metadata','dashboard_title','published']}
    return r
def chart(api,cid,filters=None,time_range=None,metrics=None):
    ctx=json.loads(api.request('GET',f'/api/v1/chart/{cid}')['result']['query_context'])
    ctx=copy.deepcopy(ctx);ctx['force']=True
    if filters is not None:ctx['queries'][0]['filters']=filters
    if time_range is not None:ctx['queries'][0]['time_range']=time_range
    if metrics is not None:ctx['queries'][0]['metrics']=metrics
    result=api.request('POST','/api/v1/chart/data',ctx)['result'][0]
    assert result['status']=='success','CHART_QUERY_FAILED_'+str(cid)
    return result['data']
def near(a,b):return abs(Decimal(str(a))-Decimal(str(b)))<Decimal('1e-8')
def main():
    DEST.mkdir(parents=True,exist_ok=True);rid=uuid.uuid4().hex;started=time.monotonic()
    report={'run_id':rid,'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'client_date':'2026-10-25','status':'FAIL','HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'READ_ONLY_SQL_AND_OFFICIAL_SUPERSET_QUERY_API','runtime_pipeline_rerun':False}
    conn=None
    try:
        report['containers']=state();assert all(x['status']=='running' and x['health']=='healthy' for x in report['containers'])
        with urllib.request.urlopen('http://127.0.0.1:8089/health',timeout=20) as r:assert r.status==200;report['health_http']=r.status
        api=SupersetAPI();report['api_login']='PASS';before=objects(api);report['business_config_sha256_before']=digest(before)
        conn=connect(config(ROOT/'.env'));conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
        with conn:
            with conn.cursor() as q:
                q.execute("SELECT current_database(),current_setting('transaction_read_only')");db,ro=q.fetchone();assert db=='movielens_btl' and ro=='on';report['database']=db;report['sql_transaction_read_only']=True
                q.execute('SELECT count(*),sum(rating),count(DISTINCT user_key),count(DISTINCT movie_key) FROM dw.fact_rating');all_values=list(q.fetchone());assert all_values==[1000209,3582313,6040,3706]
                q.execute('SELECT count(*) FROM dw.dim_movie');assert q.fetchone()[0]==3883
                cases=[]
                for label,tr,lo,hi in [('all','No filter',None,None),('2000Q3','2000-07-01 : 2000-10-01','2000-07-01','2000-10-01')]:
                    where='' if lo is None else ' WHERE rated_at >= %s::timestamptz AND rated_at < %s::timestamptz'
                    params=() if lo is None else (lo,hi)
                    q.execute('SELECT count(*),sum(rating),count(DISTINCT user_key),count(DISTINCT movie_key) FROM dw.fact_rating'+where,params);n,total,users,movies=q.fetchone()
                    observed={key:chart(api,cid,time_range=tr)[0][metric] for key,cid,metric in [('ratings',1,'rating_count'),('mean',2,'weighted_mean'),('users',3,'rated_users'),('movies',4,'rated_movies'),('sum',6,'rating_sum')]}
                    assert [observed[k] for k in ['ratings','sum','users','movies']]==[n,total,users,movies]
                    assert near(observed['mean'],Decimal(total)/n)
                    cases.append({'case':label,'sql':{'ratings':n,'sum':total,'users':users,'movies':movies},'api':observed,'status':'PASS'})
                report['overview']=cases
                # Genre count and denominator independently from base fact/bridge.
                sql="""SELECT count(*) FROM dw.fact_rating f JOIN dw.bridge_movie_genre b USING(movie_key) JOIN dw.dim_genre g USING(genre_key) WHERE f.rated_at >= %s::timestamptz AND f.rated_at < %s::timestamptz AND g.genre_name='Animation'"""
                q.execute(sql,('2001-01-01','2001-04-01'));n=q.fetchone()[0]
                q.execute(sql,('2000-10-01','2001-01-01'));prev=q.fetchone()[0]
                q.execute("SELECT count(*) FROM dw.fact_rating f JOIN dw.bridge_movie_genre b USING(movie_key) WHERE f.rated_at >= '2001-01-01'::timestamptz AND f.rated_at < '2001-04-01'::timestamptz");den=q.fetchone()[0]
                assert [n,prev,den]==[1715,20068,63335]
                row=chart(api,13,[{'col':'quarter_label','op':'IN','val':['2001 Q1']},{'col':'genre_name','op':'IN','val':['Animation']}])[0]
                assert row['rating_count']==n and row['previous_rating_count']==prev and row['genre_assignment_total']==den and near(row['qoq_pct'],Decimal(100)*(n-prev)/prev) and near(row['genre_share_pct'],Decimal(100)*n/den) and row['growth_rank']==1
                report['trends']={'case':'Animation 2001 Q1','sql':{'count':n,'prev':prev,'denominator':den},'api':row,'status':'PASS'}
                q.execute("SELECT count(*) FILTER(WHERE c.status='assigned'),count(*) FILTER(WHERE c.status='insufficient_evidence') FROM analytics.user_cluster c JOIN analytics.model_registry r USING(model_version) WHERE r.is_active AND r.is_valid_for_dw");assigned,insufficient=q.fetchone();assert [assigned,insufficient]==[6038,2]
                q.execute("SELECT count(*) FROM analytics.user_cluster c JOIN analytics.model_registry r USING(model_version) JOIN dw.dim_user u USING(user_id) WHERE r.is_active AND r.is_valid_for_dw AND c.status='assigned' AND c.cluster_id=1 AND u.gender='F' AND u.age_group='25-34'");selected=q.fetchone()[0];assert selected==170
                q.execute("SELECT c.cluster_id,count(*) FROM analytics.user_cluster c JOIN analytics.model_registry r USING(model_version) WHERE r.is_active AND r.is_valid_for_dw AND c.status='assigned' GROUP BY 1 ORDER BY 1");sizes=dict(q.fetchall());assert list(sizes.values())==[2478,1393,760,1407]
                q.execute("SELECT p.cluster_id,p.genre_name,p.mean_preference FROM analytics.cluster_genre_profile p JOIN analytics.model_registry r USING(model_version) WHERE r.is_active AND r.is_valid_for_dw ORDER BY 1,2");profile=q.fetchall();assert len(profile)==72
                report['preferences']=[]
                for name,flt in [('all',[]),('cluster1_F_25-34',[{'col':'cluster_id','op':'IN','val':[1]},{'col':'age_group','op':'IN','val':['25-34']},{'col':'gender','op':'IN','val':['F']}])]:
                    count=chart(api,14,flt)[0]['assigned_users'];assert count==(6038 if name=='all' else 170)
                    assert chart(api,15,[])[0]['insufficient_users']==2 and chart(api,16,[])[0]['fixed_assigned_baseline']==6038
                    heat=chart(api,19,[] if name=='all' else [flt[0]])
                    expected={(cid,g):m for cid,g,m in profile if name=='all' or cid==1}
                    assert len(heat)==len(expected) and all(near(r['mean_preference'],expected[(int(r['cluster_label'][0]),r['genre_name'])]) for r in heat)
                    report['preferences'].append({'case':name,'assigned':count,'fixed_baseline':6038,'insufficient':2,'heatmap_cells':len(heat),'status':'PASS'})
                # BI identity as executed by the Superset SQL engine.
                metrics=[{'expressionType':'SQL','sqlExpression':"MAX(current_user::text)",'label':'engine_role','hasCustomLabel':True,'optionName':'engine_role'}]
                report['engine_role']=chart(api,16,[],metrics=metrics)[0]['engine_role'];assert report['engine_role']=='movielens_bi_reader'
                q.execute('SELECT count(*),sum(rating),count(DISTINCT user_key),count(DISTINCT movie_key) FROM dw.fact_rating');assert list(q.fetchone())==all_values
        conn.close();conn=None
        after=objects(api);assert before==after;report['business_config_sha256_after']=digest(after)
        report.update(status='PASS',duration_seconds=round(time.monotonic()-started,3),business_config_unchanged=True,cluster_sizes=sizes,p2_intake_G2='CONFIRMED',G4='PASS_I01_I15',G5_complete=False)
    except Exception as e:
        report['error_category']=str(e) if isinstance(e,AssertionError) and re_safe(str(e)) else type(e).__name__
    finally:
        if conn is not None:conn.close()
    name=('preflight_' if report['status']=='PASS' else 'preflight_FAIL_')+rid+'.json'
    (DEST/name).write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'run_id':rid,'report':str((DEST/name).relative_to(ROOT)),'error_category':report.get('error_category')},ensure_ascii=False))
    if report['status']!='PASS':sys.exit(1)
def re_safe(s):return bool(s) and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789' for c in s)
if __name__=='__main__':main()
