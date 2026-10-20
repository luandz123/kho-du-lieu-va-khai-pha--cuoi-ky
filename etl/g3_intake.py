"""S11B-1: immutable G3 intake and READ ONLY dry-run; no production write CLI."""
from __future__ import annotations
import argparse,copy,csv,hashlib,io,json,math,re,subprocess,sys,uuid
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from collections import Counter
from etl.s05_staging import ROOT,SafeError,assert_project,catalog,config,connect,sha256

VERSION='kmeans_k4_seed42'
PINNED={'user_cluster.csv':'5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93',
        'cluster_genre_profile.csv':'59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d'}
HEADERS={'user_cluster.csv':['user_id','cluster_id','status','model_version'],
         'cluster_genre_profile.csv':['cluster_id','genre_name','mean_preference','n_users']}
SIZES={0:2478,1:1393,2:760,3:1407}
def fail(code):raise SafeError(code)
def require(condition,code):
    if not condition:fail(code)
def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()
def integer(text):
    require(isinstance(text,str) and re.fullmatch(r'0|[1-9][0-9]*',text) is not None,'INVALID_INTEGER')
    return int(text)
def csv_rows(blob,name):
    require(not blob.startswith(b'\xef\xbb\xbf') and b'\r' not in blob and blob.endswith(b'\n'),'CSV_ENCODING_OR_NEWLINE')
    try:rows=list(csv.reader(io.StringIO(blob.decode('utf-8')),strict=True))
    except (ValueError,UnicodeError,csv.Error):fail('CSV_PARSE_ERROR')
    require(bool(rows) and rows[0]==HEADERS[name] and all(len(r)==4 for r in rows[1:]),'CSV_SCHEMA')
    out=io.StringIO(newline='');csv.writer(out,lineterminator='\n').writerows(rows)
    require(out.getvalue().encode()==blob,'CSV_NOT_CANONICAL')
    return rows[1:]

def validate_records(user_rows,profile_rows,*,version,k,genres,user_ids):
    """Pure structural checks, also used with explicitly synthetic test cohorts."""
    users=[];seen=set();counts=Counter();assigned=[]
    for uid,cid,status,model in user_rows:
        u=integer(uid);require(u>0 and u not in seen,'DUPLICATE_USER');seen.add(u)
        require(u in user_ids,'ORPHAN_USER');require(model==version,'ROW_MODEL_VERSION')
        require(status in ['assigned','insufficient_evidence'],'INVALID_STATUS')
        if status=='assigned':
            require(cid!='','ASSIGNED_NULL_CLUSTER');c=integer(cid);require(c<k,'CLUSTER_OUT_OF_RANGE');counts[c]+=1;assigned.append(u)
        else:require(cid=='','INSUFFICIENT_NON_NULL_CLUSTER');c=None
        users.append((u,c,status,model))
    require(seen==set(user_ids),'USER_COHORT_INCOMPLETE')
    require([r[0] for r in users]==sorted(seen),'USER_ORDER')
    profiles=[];pairs=set();sums=Counter()
    for cid,g,mean,n in profile_rows:
        c=integer(cid);require(c<k and g in genres,'PROFILE_GENRE_OR_CLUSTER')
        require((c,g) not in pairs,'DUPLICATE_PROFILE');pairs.add((c,g))
        try:x=float(mean)
        except ValueError:fail('PROFILE_MEAN_PARSE')
        require(math.isfinite(x) and 0<=x<=1,'PROFILE_MEAN_DOMAIN')
        num=integer(n);require(num==counts[c] and num>0,'PROFILE_N_USERS')
        sums[c]+=x;profiles.append((c,g,x,num))
    require(pairs=={(c,g) for c in range(k) for g in genres},'PROFILE_GRID_INCOMPLETE')
    require(all(abs(sums[c]-1)<=1e-8 for c in range(k)),'PROFILE_SUM')
    require([(p[0],p[1]) for p in profiles]==sorted(pairs),'PROFILE_ORDER')
    return users,profiles,dict(counts),assigned

@dataclass
class Package:
    manifest:dict
    users:list
    profiles:list
    payload_sha256:dict
    manifest_sha256:str
    snapshot:dict|None=None

def read_package(directory):
    """Read the complete three-file snapshot into memory before any DB connection.

    No trust in three os.replace calls being atomic as a group. Rehash every
    member after reading; checksums and frozen pins must match the same manifest.
    """
    directory=Path(directory);names=[*PINNED,'manifest.json']
    require(all((directory/n).is_file() and not (directory/n).is_symlink() for n in names),'PACKAGE_INCOMPLETE')
    blobs={n:(directory/n).read_bytes() for n in names}
    require(all((directory/n).read_bytes()==b for n,b in blobs.items()),'PACKAGE_CHANGED_DURING_READ')
    return validate_snapshot(blobs)

def validate_snapshot(blobs):
    """Revalidate in-memory bytes without rereading package files."""
    require(set(blobs)=={*PINNED,'manifest.json'} and all(isinstance(v,bytes) for v in blobs.values()),'SNAPSHOT_INCOMPLETE')
    try:m=json.loads(blobs['manifest.json'])
    except (ValueError,UnicodeError):fail('MANIFEST_PARSE')
    require(isinstance(m,dict),'MANIFEST_SCHEMA')
    require(m.get('contract_version')==2 and m.get('model_version')==VERSION,'CONTRACT_OR_VERSION')
    require(m.get('algorithm')=='KMeans','ALGORITHM')
    for key in ['training_config','libraries','canonical_hashes','source_hashes','code_provenance','data_summary','files']:
        require(isinstance(m.get(key),dict),'METADATA_MISSING')
    hashes={n:hashlib.sha256(blobs[n]).hexdigest() for n in PINNED}
    for n,h in hashes.items():
        require(m['files'].get(n,{}).get('sha256')==h,'MANIFEST_CHECKSUM_MISMATCH')
        require(h==PINNED[n],'FROZEN_PAYLOAD_MISMATCH')
    t=m['training_config'];genres=t.get('genre_order',[])
    require(t.get('k')==4 and t.get('seed')==42 and t.get('n_init')==10 and t.get('preprocessing')=='raw','TRAINING_CONFIG')
    require(isinstance(genres,list) and len(genres)==18 and genres==sorted(set(genres)),'GENRE_ORDER')
    require(m.get('training_config_hash')==digest(t),'TRAINING_CONFIG_HASH')
    require(t.get('genre_order_hash')==hashlib.sha256(','.join(genres).encode()).hexdigest(),'GENRE_ORDER_HASH')
    for lib,value in {'numpy':'2.0.2','pandas':'2.3.3','scikit-learn':'1.5.2'}.items():require(m['libraries'].get(lib)==value,'MODEL_LIBRARY_VERSION')
    require(re.fullmatch(r'3\.12\.\d+',m['libraries'].get('python','')) is not None,'PYTHON_LIBRARY_VERSION')
    try:created=datetime.fromisoformat(m['generated_at_utc'].replace('Z','+00:00'))
    except (KeyError,ValueError,TypeError):fail('MODEL_TIME')
    require(created.utcoffset() is not None and created.utcoffset().total_seconds()==0,'MODEL_TIME_NOT_UTC')
    g1=json.loads((ROOT/'results/eda/canonical_manifest.json').read_text(encoding='utf-8'))
    g2=json.loads((ROOT/'results/warehouse/dw_manifest.json').read_text(encoding='utf-8'))
    require(m['canonical_hashes']==g1['canonical_hashes']==g2['canonical_hashes'],'CANONICAL_METADATA')
    require(m['source_hashes']==g1['source_hashes']==g2['source_hashes'],'SOURCE_METADATA')
    require(m['code_provenance'].get('g1_canonical_code_commit')==g1['source_code_commit'],'G1_CODE_PROVENANCE')
    for name in ['features','clustering']:
        path='mining/'+name+'.py';local=(ROOT/path).read_bytes();git=subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT)
        require(local.replace(b'\r\n',b'\n')==git,'P2_CODE_NOT_MERGED')
        require(m['code_provenance'].get(name+'_code_sha256') in {hashlib.sha256(local).hexdigest(),hashlib.sha256(git).hexdigest()},'P2_CODE_PROVENANCE')
    ur=csv_rows(blobs['user_cluster.csv'],'user_cluster.csv');pr=csv_rows(blobs['cluster_genre_profile.csv'],'cluster_genre_profile.csv')
    # IDs must additionally equal live dim_user during DB intake.
    users,profiles,counts,assigned=validate_records(ur,pr,version=VERSION,k=4,genres=genres,user_ids=set(range(1,6041)))
    require(len(users)==6040 and len(assigned)==6038 and counts==SIZES and len(profiles)==72,'FROZEN_COUNTS')
    require(t.get('total_assigned_users')==6038 and t.get('user_order_hash')==hashlib.sha256(','.join(map(str,assigned)).encode()).hexdigest(),'ASSIGNED_ORDER_HASH')
    summary={'total_users':6040,'assigned_users':6038,'insufficient_evidence_users':2,'num_clusters':4,'cluster_sizes':{str(k):v for k,v in SIZES.items()}}
    require(m['data_summary']==summary,'SUMMARY_MISMATCH')
    for n,count in [('user_cluster.csv',6040),('cluster_genre_profile.csv',72)]:require(m['files'][n].get('row_count')==count,'MANIFEST_ROW_COUNT')
    return Package(m,users,profiles,hashes,hashlib.sha256(blobs['manifest.json']).hexdigest(),dict(blobs))

def registry_metadata(pkg):
    # Existing jsonb column retains the exact input config plus payload identity.
    return copy.deepcopy({'method':pkg.manifest['training_config']['preprocessing'],'training_config':pkg.manifest['training_config'],
            'g3_payload_sha256':pkg.payload_sha256,'code_provenance':pkg.manifest['code_provenance']})

def assert_same_version(existing,pkg):
    require(existing['preprocessing']==registry_metadata(pkg) and existing['libraries']==pkg.manifest['libraries']
            and existing['canonical_hashes']==pkg.manifest['canonical_hashes'] and existing['source_hashes']==pkg.manifest['source_hashes']
            and existing['training_config_hash']==pkg.manifest['training_config_hash']
            and existing['k']==pkg.manifest['training_config']['k'] and existing['seed']==pkg.manifest['training_config']['seed']
            and existing['genre_order']==pkg.manifest['training_config']['genre_order'],'VERSION_PAYLOAD_CONFLICT')

REGISTRY_FIELDS=['preprocessing','libraries','canonical_hashes','source_hashes','training_config_hash','k','seed','genre_order','is_active','is_valid_for_dw']
def existing_plan(existing,pkg,stored_users,stored_profiles):
    assert_same_version(existing,pkg)
    if not stored_users and not stored_profiles and not existing['is_active'] and not existing['is_valid_for_dw']:
        return 'RELOAD_IDENTICAL_INVALIDATED_VERSION'
    require(stored_users==pkg.users,'EXISTING_USER_PAYLOAD_CONFLICT')
    require(stored_profiles==pkg.profiles,'EXISTING_PROFILE_PAYLOAD_CONFLICT')
    return 'NO_OP_IDENTICAL_ACTIVE_VERSION' if existing['is_active'] and existing['is_valid_for_dw'] else 'REACTIVATE_IDENTICAL_VERSION_AFTER_DW_RECHECK'

def check_dw(conn,pkg):
    """Caller owns READ ONLY transaction; fresh four-view hashes, not old reports."""
    from mining.data_io import load_dw_data,compute_canonical_hash
    assert_project(conn);cat=catalog(conn)
    require(cat['columns_match'] and cat['keys_match'],'CATALOG_MISMATCH')
    frames=load_dw_data(connection_or_engine=conn)
    hashes={t:compute_canonical_hash(t,f) for t,f in frames.items()}
    require(hashes==pkg.manifest['canonical_hashes'],'DW_CANONICAL_MISMATCH')
    require(set(frames['users']['user_id'])=={r[0] for r in pkg.users},'DW_USER_FK')
    with conn.cursor() as q:
        q.execute('SELECT genre_name FROM dw.dim_genre ORDER BY genre_name');require([r[0] for r in q.fetchall()]==pkg.manifest['training_config']['genre_order'],'DW_GENRE_SET')
        q.execute('SELECT '+','.join(REGISTRY_FIELDS)+' FROM analytics.model_registry WHERE model_version=%s',(VERSION,));row=q.fetchone()
        plan='INSERT_NEW_INACTIVE_VERSION_THEN_VERIFY_AND_ACTIVATE'
        if row:
            q.execute('SELECT user_id,cluster_id,status,model_version FROM analytics.user_cluster WHERE model_version=%s ORDER BY user_id',(VERSION,));stored_users=q.fetchall()
            q.execute('SELECT cluster_id,genre_name,mean_preference,n_users FROM analytics.cluster_genre_profile WHERE model_version=%s ORDER BY cluster_id,genre_name',(VERSION,));stored_profiles=q.fetchall()
            plan=existing_plan(dict(zip(REGISTRY_FIELDS,row)),pkg,stored_users,stored_profiles)
        counts={}
        for table in ['model_registry','user_cluster','cluster_genre_profile']:
            q.execute('SELECT count(*) FROM analytics.'+table);counts[table]=q.fetchone()[0]
    return {'canonical_hashes':hashes,'row_counts':{t:len(f) for t,f in frames.items()},'analytics_counts':counts,'plan':plan}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path,required=True);parser.add_argument('--dry-run',action='store_true',required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    report={'run_id':uuid.uuid4().hex,'at_utc':datetime.now(timezone.utc).isoformat(),'mode':'DRY_RUN','database_writes':False,'p2_intake_status':'NOT_CONFIRMED'}
    try:
        pkg=read_package(args.package)  # Complete package rejection precedes DB connection.
        conn=connect(config(ROOT/'.env'));conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
        try:
            with conn:
                with conn.cursor() as q:q.execute('SELECT pg_advisory_xact_lock_shared(20261027,1)')
                result=check_dw(conn,pkg)
                with conn.cursor() as q:q.execute("SELECT current_database(),current_setting('transaction_read_only')");db,ro=q.fetchone();require(ro=='on','DRY_RUN_NOT_READ_ONLY')
            conn.rollback()
        finally:conn.close()
        report.update(status='PASS',database=db,transaction_read_only=ro,package_path=str(args.package),model_version=VERSION,payload_sha256=pkg.payload_sha256,manifest_sha256=pkg.manifest_sha256,
                      libraries=pkg.manifest['libraries'],cluster_sizes=SIZES,assigned=6038,insufficient_evidence=2,profile_rows=72,result=result,
                      code_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),code_sha256=sha256(Path(__file__)))
    except SafeError as e:report.update(status='FAIL',error_code=e.code)
    except Exception as e:report.update(status='FAIL',error_code='INTAKE_RUNTIME_ERROR',exception_type=type(e).__name__)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    require(not args.report.exists(),'REPORT_EXISTS_KEEP_HISTORY')
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['run_id','status','mode','database_writes']}))
    return 0 if report['status']=='PASS' else 2
if __name__=='__main__':raise SystemExit(main())
