"""S11B-2 explicit production CLI. Default READ ONLY; --apply enables one transaction.

No automatic write retry. All INSERT values come from the validated byte snapshot.
"""
import argparse,hashlib,json,subprocess,sys,time,uuid,tempfile,os
from pathlib import Path
from datetime import datetime,timezone
from psycopg2 import sql
from etl.s05_staging import ROOT,SafeError,config,connect,sha256
from etl.g3_intake import require,read_package,check_dw,VERSION
from etl.g3_transaction import production_transaction,verify_active,SOURCE_TABLES

def protected_state(conn):
    """All retained fields, including surrogate IDs; aggregate fingerprints only."""
    state={'sources':{}}
    with conn.cursor() as q:
        for name,keys in SOURCE_TABLES.items():
            q.execute(sql.SQL("SELECT count(*),md5(COALESCE(string_agg(md5(to_jsonb(t)::text),'' ORDER BY {}),'')) FROM {} t").format(
                sql.SQL(',').join(map(sql.Identifier,keys.split(','))),sql.Identifier(*name.split('.'))))
            n,h=q.fetchone();state['sources'][name]={'rows':n,'ordered_row_md5':h}
        q.execute("SELECT n.nspname,c.relname,c.relowner,c.relacl::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('dw','analytics','staging') ORDER BY 1,2")
        state['project_relation_acl_sha256']=hashlib.sha256(json.dumps(q.fetchall(),default=str).encode()).hexdigest()
        q.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolinherit,rolreplication,rolbypassrls FROM pg_roles WHERE rolname='movielens_bi_reader'");state['bi_role_attributes']=list(q.fetchone())
        q.execute("SELECT r.rolname FROM pg_auth_members a JOIN pg_roles r ON r.oid=a.roleid JOIN pg_roles m ON m.oid=a.member WHERE m.rolname='movielens_bi_reader' ORDER BY 1");state['bi_memberships']=[r[0] for r in q.fetchall()]
        q.execute("SELECT nspname,nspacl::text FROM pg_namespace WHERE nspname IN ('dw','staging','analytics','public') ORDER BY 1");state['schema_acl_sha256']=hashlib.sha256(json.dumps(q.fetchall()).encode()).hexdigest()
    return state

def dashboard_state():
    """Read official API only; do not start services, create charts or modify metadata."""
    sys.path.insert(0,str(ROOT/'dashboard/overview'))
    from superset_api import SupersetAPI
    paths=subprocess.check_output(['git','ls-files','dashboard/overview','dashboard/trends','dashboard/superset'],cwd=ROOT,text=True).splitlines()
    artifact_hashes={p:sha256(ROOT/p) for p in paths}
    try:api=SupersetAPI()
    except Exception as e:return {'available':False,'error_category':type(e).__name__,'local_artifact_sha256':artifact_hashes}
    result={}
    fields={'dashboard':['dashboard_title','position_json','json_metadata','css','slug'],
            'dataset':['sql','metrics','columns','main_dttm_col'],
            'chart':['params','query_context','dashboards','slice_name','viz_type']}
    for kind,ids in [('dashboard',[1,2]),('dataset',[1,2,3,4]),('chart',range(1,14))]:
        for i in ids:
            r=api.request('GET',f'/api/v1/{kind}/{i}')['result'];value={k:r.get(k) for k in fields[kind]}
            result[f'{kind}/{i}']=hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()
    return {'available':True,'object_config_sha256':result,'local_artifact_sha256':artifact_hashes}

def observe(c,pkg,*,active_required=False):
    conn=connect(c);conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
    try:
        with conn:
            with conn.cursor() as q:q.execute('SELECT pg_advisory_xact_lock_shared(20261027,1)')
            dw=check_dw(conn,pkg);protected=protected_state(conn)
            with conn.cursor() as q:
                q.execute("SELECT current_database(),current_setting('transaction_read_only')");db,ro=q.fetchone();require(ro=='on','POSTCHECK_NOT_READ_ONLY')
                q.execute('SELECT model_version,contract_version,is_active,is_valid_for_dw,registered_at,model_created_at FROM analytics.model_registry ORDER BY model_version')
                registry=[dict(zip(['model_version','contract_version','is_active','is_valid_for_dw','registered_at','model_created_at'],r)) for r in q.fetchall()]
                q.execute('SELECT cluster_id,count(*) FROM analytics.user_cluster WHERE status=%s GROUP BY cluster_id ORDER BY cluster_id',('assigned',));sizes={r[0]:r[1] for r in q.fetchall()}
                q.execute('SELECT status,count(*) FROM analytics.user_cluster GROUP BY status ORDER BY status');statuses=dict(q.fetchall())
                q.execute('SELECT cluster_id,count(*),sum(mean_preference),min(n_users),max(n_users) FROM analytics.cluster_genre_profile GROUP BY cluster_id ORDER BY cluster_id');profile=[list(r) for r in q.fetchall()]
                if active_required:
                    require(len(registry)==1 and registry[0]['model_version']==VERSION and registry[0]['contract_version']==2 and registry[0]['is_active'] and registry[0]['is_valid_for_dw'],'POSTCHECK_REGISTRY_STATE')
                    require(dw['analytics_counts']=={'model_registry':1,'user_cluster':6040,'cluster_genre_profile':72},'POSTCHECK_COUNTS')
                    verify_active(q,pkg,views=True)
                    require(sizes=={0:2478,1:1393,2:760,3:1407} and statuses=={'assigned':6038,'insufficient_evidence':2},'POSTCHECK_CLUSTER_COUNTS')
                    require(all(n==18 and abs(total-1)<1e-8 and lo==hi==sizes[k] for k,n,total,lo,hi in profile),'POSTCHECK_PROFILE')
    finally:conn.close()
    return {'database':db,'read_only':ro,'dw':dw,'protected_state':protected,'registry':registry,'cluster_sizes':sizes,'status_counts':statuses,'profile_aggregates':profile}

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);m=p.add_mutually_exclusive_group();m.add_argument('--apply',action='store_true');m.add_argument('--dry-run',action='store_true');p.add_argument('--expect-empty',action='store_true');p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    require(not a.report.exists(),'REPORT_EXISTS_KEEP_HISTORY');a.report.parent.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();files=['etl/g3_intake.py','etl/g3_transaction.py','etl/load_g3.py']
    r={'run_id':uuid.uuid4().hex,'at_utc':datetime.now(timezone.utc).isoformat(),'mode':'APPLY' if a.apply else 'DRY_RUN','status':'FAIL',
       'code_state':'WORKING_TREE_SHA256_NOT_IN_BASE_COMMIT','base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
       'code_sha256':{n:sha256(ROOT/n) for n in files},'p2_intake_status':'NOT_CONFIRMED','write_retry':False}
    conn=None;pkg=None;c=None
    try:
        pkg=read_package(a.package);c=config(ROOT/'.env')
        r.update(model_version=VERSION,payload_sha256=pkg.payload_sha256,manifest_sha256=pkg.manifest_sha256)
        r['before']=observe(c,pkg)
        if a.expect_empty:require(not any(r['before']['dw']['analytics_counts'].values()),'EXPECTED_EMPTY_ANALYTICS_CHANGED')
        r['dashboard_before']=dashboard_state()
        if a.apply:
            conn=connect(c)
            r['transaction_result']=production_transaction(conn,pkg,expect_empty=a.expect_empty)
            conn.close();conn=None
            # Fresh connection after COMMIT; no same-session snapshot reused.
            r['after']=observe(c,pkg,active_required=True)
            require(r['before']['protected_state']==r['after']['protected_state'],'STAGING_DW_OR_BI_PRIVILEGES_CHANGED')
            if r['transaction_result']['transaction']=='COMMITTED_NO_OP':require(r['before']['registry']==r['after']['registry'],'NO_OP_CHANGED_REGISTRY')
        else:r['database_outcome']='NO_WRITE_DRY_RUN'
        r['dashboard_after']=dashboard_state()
        if r['dashboard_before'].get('available',True) and r['dashboard_after'].get('available',True):
            require(r['dashboard_before']==r['dashboard_after'],'DASHBOARD_CONFIG_CHANGED');r['dashboard_comparison']='LIVE_API_AND_ARTIFACTS_MATCH'
        else:
            require(r['dashboard_before']['local_artifact_sha256']==r['dashboard_after']['local_artifact_sha256'],'DASHBOARD_ARTIFACT_CHANGED')
            r['dashboard_comparison']='API_UNAVAILABLE_LOCAL_ARTIFACTS_MATCH_ONLY'
        require(r['code_sha256']=={n:sha256(ROOT/n) for n in files},'CODE_CHANGED_DURING_RUN')
        r['status']='PASS'
    except Exception as e:
        r['error_code']=e.code if isinstance(e,SafeError) else 'G3_DISPATCH_RUNTIME_ERROR'
        r['error_details']=getattr(e,'details',{});r['exception_type']=type(e).__name__
        if r['error_details'].get('database_outcome')=='UNKNOWN':
            r['status']='UNKNOWN'
            if conn is not None:conn.close();conn=None
            try:r['unknown_reconciliation_new_read_only_connection']=observe(c,pkg,active_required=False)
            except Exception as obs:r['unknown_reconciliation_error']=type(obs).__name__
        elif r.get('transaction_result',{}).get('transaction') in ['COMMITTED','COMMITTED_NO_OP']:
            r['database_outcome']='COMMITTED_BUT_POSTCHECK_FAILED_DO_NOT_RETRY'
    finally:
        if conn is not None:conn.close()
    r['duration_seconds']=round(time.monotonic()-start,3)
    try:
        # Report publication is separate from DB COMMIT; IO failure is not a rollback.
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=a.report.parent,delete=False) as f:
            json.dump(r,f,ensure_ascii=False,indent=2,default=str);f.write('\n');tmp=f.name
        require(not a.report.exists(),'REPORT_EXISTS_KEEP_HISTORY');os.replace(tmp,a.report)
    except Exception:
        print(json.dumps({'status':'REPORT_WRITE_FAILED','run_id':r['run_id'],'database_outcome':r.get('transaction_result',{}).get('transaction',r.get('database_outcome','UNKNOWN'))}));return 2
    print(json.dumps({'status':r['status'],'run_id':r['run_id'],'mode':r['mode'],'seconds':r['duration_seconds'],'transaction':r.get('transaction_result',{}).get('transaction'),'error_code':r.get('error_code')}))
    return 0 if r['status']=='PASS' else 2
if __name__=='__main__':raise SystemExit(main())
