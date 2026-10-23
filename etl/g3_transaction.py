"""One transaction engine, separate guarded fixture and production dispatchers."""
import re
from psycopg2 import sql
from psycopg2.extras import Json,execute_values
from etl.s05_staging import SafeError,assert_project
from etl.integration_target import assert_warehouse as assert_project
from etl.g3_intake import (REGISTRY_FIELDS,require,registry_metadata,existing_plan,validate_records,
                           validate_snapshot,check_dw,VERSION,PINNED)

SOURCE_TABLES={
 'staging.users_raw':'source_line','staging.movies_raw':'source_line','staging.ratings_raw':'source_line',
 'dw.dim_user':'user_key','dw.dim_movie':'movie_key','dw.dim_date':'date_key','dw.dim_genre':'genre_key',
 'dw.bridge_movie_genre':'movie_key,genre_key','dw.fact_rating':'rating_key'}

def database_outcome(phase,conn):
    if phase=='COMMIT_REQUESTED':return 'UNKNOWN'
    try:
        if not conn.closed and conn.get_transaction_status()==0:return 'ROLLED_BACK'
    except Exception:pass
    return 'UNKNOWN'

def stored_rows(q,schema,version):
    q.execute(sql.SQL('SELECT user_id,cluster_id,status,model_version FROM {} WHERE model_version=%s ORDER BY user_id').format(sql.Identifier(schema,'user_cluster')),(version,));u=q.fetchall()
    q.execute(sql.SQL('SELECT cluster_id,genre_name,mean_preference,n_users FROM {} WHERE model_version=%s ORDER BY cluster_id,genre_name').format(sql.Identifier(schema,'cluster_genre_profile')),(version,));return u,q.fetchall()

def verify_active(q,pkg,schema='analytics',*,views=False):
    version=pkg.manifest['model_version']
    require(stored_rows(q,schema,version)==(pkg.users,pkg.profiles),'PRECOMMIT_STORED_PAYLOAD_MISMATCH')
    q.execute(sql.SQL('SELECT model_version,is_valid_for_dw FROM {} WHERE is_active').format(sql.Identifier(schema,'model_registry')))
    require(q.fetchall()==[(version,True)],'ACTIVE_VERSION_COUNT')
    if views:
        q.execute('SELECT user_id,cluster_id,status,model_version FROM analytics.v_active_user_cluster ORDER BY user_id')
        require(q.fetchall()==pkg.users,'ACTIVE_USER_VIEW_PAYLOAD')
        q.execute('SELECT cluster_id,genre_name,mean_preference,n_users,model_version FROM analytics.v_active_cluster_genre_profile ORDER BY cluster_id,genre_name')
        require(q.fetchall()==[(*p,version) for p in pkg.profiles],'ACTIVE_PROFILE_VIEW_PAYLOAD')

def _transaction(conn,pkg,*,schema,source_schema,production=False,expect_empty=False,fail_after=None):
    """Shared write/verify/activation path. No helper opens another connection."""
    require(conn.get_transaction_status()==0,'CALLER_TRANSACTION_ALREADY_OPEN')
    require(not production or fail_after is None,'PRODUCTION_FAIL_INJECTION_FORBIDDEN')
    conn.set_session(readonly=False,isolation_level='READ COMMITTED')
    phase='PRECOMMIT';progress={};checked=None
    def table(n):return sql.Identifier(schema,n)
    try:
        with conn:
            with conn.cursor() as q:
                q.execute('SELECT pg_advisory_xact_lock(20261027,1)');progress['exclusive_etl_lock']=True
                if production:assert_project(conn)
                if not production:
                    q.execute("SELECT obj_description(oid,'pg_namespace'),nspowner=(SELECT oid FROM pg_roles WHERE rolname=current_user) FROM pg_namespace WHERE nspname=%s",(schema,))
                    require(q.fetchone()==('BTL P1 G3 disposable synthetic fixture',True),'FIXTURE_NOT_OWNED_OR_MARKED')
                q.execute(sql.SQL('LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE').format(sql.SQL(',').join(table(n) for n in ['model_registry','user_cluster','cluster_genre_profile'])))
                sources=[sql.Identifier(*n.split('.')) for n in SOURCE_TABLES] if production else [sql.Identifier(source_schema,n) for n in ['dim_user','dim_genre']]
                q.execute(sql.SQL('LOCK TABLE {} IN SHARE MODE').format(sql.SQL(',').join(sources)));progress['sources_and_targets_locked']=True
                if production:
                    checked=check_dw(conn,pkg)
                    if expect_empty:require(not any(checked['analytics_counts'].values()),'EXPECTED_EMPTY_ANALYTICS_CHANGED')
                    progress['production_checks_same_connection']=True
                q.execute(sql.SQL('SELECT user_id FROM {}').format(sql.Identifier(source_schema,'dim_user')));user_ids={r[0] for r in q.fetchall()}
                q.execute(sql.SQL('SELECT genre_name FROM {} ORDER BY genre_name').format(sql.Identifier(source_schema,'dim_genre')));genres=[r[0] for r in q.fetchall()]
                require(genres==pkg.manifest['training_config']['genre_order'],'GENRE_SET')
                validate_records([[str(u),'' if c is None else str(c),s,v] for u,c,s,v in pkg.users],[[str(c),g,str(x),str(n)] for c,g,x,n in pkg.profiles],version=pkg.manifest['model_version'],k=pkg.manifest['training_config']['k'],genres=genres,user_ids=user_ids)
                version=pkg.manifest['model_version']
                q.execute(sql.SQL('SELECT {} FROM {} WHERE model_version=%s').format(sql.SQL(',').join(map(sql.Identifier,REGISTRY_FIELDS)),table('model_registry')),(version,));row=q.fetchone()
                plan=existing_plan(dict(zip(REGISTRY_FIELDS,row)),pkg,*stored_rows(q,schema,version)) if row else 'INSERT_NEW_VERSION'
                if not row:
                    m=pkg.manifest;t=m['training_config']
                    q.execute(sql.SQL('INSERT INTO {}(model_version,contract_version,source_hashes,canonical_hashes,k,seed,preprocessing,genre_order,libraries,training_config_hash,model_created_at) VALUES(%s,2,%s,%s,%s,%s,%s,%s,%s,%s,%s)').format(table('model_registry')),
                              (version,Json(m['source_hashes']),Json(m['canonical_hashes']),t['k'],t['seed'],Json(registry_metadata(pkg)),genres,Json(m['libraries']),m['training_config_hash'],m['generated_at_utc']))
                require(fail_after!='registry','FIXTURE_INJECTED_FAILURE')
                if plan in ['INSERT_NEW_VERSION','RELOAD_IDENTICAL_INVALIDATED_VERSION']:
                    execute_values(q,sql.SQL('INSERT INTO {}(user_id,cluster_id,status,model_version) VALUES %s').format(table('user_cluster')).as_string(conn),pkg.users)
                    require(fail_after!='users','FIXTURE_INJECTED_FAILURE')
                    execute_values(q,sql.SQL('INSERT INTO {}(model_version,cluster_id,genre_name,mean_preference,n_users) VALUES %s').format(table('cluster_genre_profile')).as_string(conn),[(version,*r) for r in pkg.profiles])
                require(fail_after!='profiles','FIXTURE_INJECTED_FAILURE')
                require(stored_rows(q,schema,version)==(pkg.users,pkg.profiles),'PRECOMMIT_STORED_PAYLOAD_MISMATCH')
                if plan!='NO_OP_IDENTICAL_ACTIVE_VERSION':
                    q.execute(sql.SQL('UPDATE {} SET is_active=false WHERE is_active AND model_version<>%s').format(table('model_registry')),(version,))
                    q.execute(sql.SQL('UPDATE {} SET is_valid_for_dw=true,is_active=true WHERE model_version=%s').format(table('model_registry')),(version,))
                verify_active(q,pkg,schema,views=production)
                require(fail_after!='activate','FIXTURE_INJECTED_FAILURE')
                progress['all_rows_and_active_state_verified']=True
                phase='COMMIT_REQUESTED'
        if fail_after=='commit_ack':raise ConnectionError('synthetic lost acknowledgement AFTER fixture COMMIT')
        return {'plan':plan,'transaction':'COMMITTED_NO_OP' if plan=='NO_OP_IDENTICAL_ACTIVE_VERSION' else ('COMMITTED' if production else 'COMMITTED_FIXTURE_ONLY'),
                'rows_verified':len(pkg.users)+len(pkg.profiles),'checks':checked,'progress':progress}
    except Exception as exc:
        err=SafeError(exc.code if isinstance(exc,SafeError) else 'G3_TRANSACTION_SQL_OR_CONNECTION_ERROR')
        err.details={'database_outcome':database_outcome(phase,conn),
                     'phase':phase,'sqlstate':getattr(exc,'pgcode',None),'progress':progress}
        raise err from None

def fixture_transaction(conn,pkg,*,schema,fail_after=None):
    require(re.fullmatch(r'p1_g3_fixture_[0-9a-f]{32}',schema) is not None,'PRODUCTION_WRITE_DISABLED_11B1')
    return _transaction(conn,pkg,schema=schema,source_schema=schema,fail_after=fail_after)

def production_transaction(conn,pkg,*,expect_empty=False):
    require(pkg.snapshot is not None,'PRODUCTION_REQUIRES_VERIFIED_BYTE_SNAPSHOT')
    verified=validate_snapshot(pkg.snapshot)
    require(verified.manifest['model_version']==VERSION and verified.payload_sha256==PINNED,'PRODUCTION_FROZEN_IDENTITY')
    return _transaction(conn,verified,schema='analytics',source_schema='dw',production=True,expect_empty=expect_empty)
