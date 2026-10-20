"""Prepared transaction engine. S11B-1 permits execution ONLY in owned fixtures.

No production apply entry point is enabled. S11B-2 must separately authorize and
review dispatch to analytics, live check_dw under the exclusive lock, and final
precommit business checks. This prototype uses the approved registry/table layout.
"""
import re
from psycopg2 import sql
from psycopg2.extras import Json,execute_values
from etl.g3_intake import (REGISTRY_FIELDS,require,registry_metadata,existing_plan,validate_records)

def fixture_transaction(conn,pkg,*,schema,fail_after=None):
    require(re.fullmatch(r'p1_g3_fixture_[0-9a-f]{32}',schema) is not None,'PRODUCTION_WRITE_DISABLED_11B1')
    require(conn.get_transaction_status()==0,'CALLER_TRANSACTION_ALREADY_OPEN')
    conn.set_session(readonly=False,isolation_level='READ COMMITTED')
    def table(n):return sql.Identifier(schema,n)
    with conn:
        with conn.cursor() as q:
            q.execute('SELECT pg_advisory_xact_lock(20261027,1)')
            q.execute("SELECT obj_description(oid,'pg_namespace'),nspowner=(SELECT oid FROM pg_roles WHERE rolname=current_user) FROM pg_namespace WHERE nspname=%s",(schema,))
            require(q.fetchone()==('BTL P1 G3 disposable synthetic fixture',True),'FIXTURE_NOT_OWNED_OR_MARKED')
            q.execute(sql.SQL('LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE').format(sql.SQL(',').join(table(n) for n in ['model_registry','user_cluster','cluster_genre_profile'])))
            q.execute(sql.SQL('LOCK TABLE {},{} IN SHARE MODE').format(table('dim_user'),table('dim_genre')))
            q.execute(sql.SQL('SELECT user_id FROM {}').format(table('dim_user')));user_ids={r[0] for r in q.fetchall()}
            q.execute(sql.SQL('SELECT genre_name FROM {} ORDER BY genre_name').format(table('dim_genre')));genres=[r[0] for r in q.fetchall()]
            require(genres==pkg.manifest['training_config']['genre_order'],'FIXTURE_GENRE_SET')
            validate_records([[str(u),'' if c is None else str(c),s,v] for u,c,s,v in pkg.users],[[str(c),g,str(x),str(n)] for c,g,x,n in pkg.profiles],version=pkg.manifest['model_version'],k=pkg.manifest['training_config']['k'],genres=genres,user_ids=user_ids)
            version=pkg.manifest['model_version']
            q.execute(sql.SQL('SELECT {} FROM {} WHERE model_version=%s').format(sql.SQL(',').join(map(sql.Identifier,REGISTRY_FIELDS)),table('model_registry')),(version,));row=q.fetchone()
            plan='INSERT_NEW_VERSION'
            def rows():
                q.execute(sql.SQL('SELECT user_id,cluster_id,status,model_version FROM {} WHERE model_version=%s ORDER BY user_id').format(table('user_cluster')),(version,));u=q.fetchall()
                q.execute(sql.SQL('SELECT cluster_id,genre_name,mean_preference,n_users FROM {} WHERE model_version=%s ORDER BY cluster_id,genre_name').format(table('cluster_genre_profile')),(version,));return u,q.fetchall()
            if row:plan=existing_plan(dict(zip(REGISTRY_FIELDS,row)),pkg,*rows())
            if plan=='NO_OP_IDENTICAL_ACTIVE_VERSION':return {'plan':plan,'transaction':'COMMITTED_NO_OP','rows_verified':len(pkg.users)+len(pkg.profiles)}
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
            require(rows()==(pkg.users,pkg.profiles),'PRECOMMIT_STORED_PAYLOAD_MISMATCH')
            q.execute(sql.SQL('UPDATE {} SET is_active=false WHERE is_active AND model_version<>%s').format(table('model_registry')),(version,))
            q.execute(sql.SQL('UPDATE {} SET is_valid_for_dw=true,is_active=true WHERE model_version=%s').format(table('model_registry')),(version,))
            q.execute(sql.SQL('SELECT count(*) FROM {} WHERE is_active AND is_valid_for_dw').format(table('model_registry')));require(q.fetchone()[0]==1,'ACTIVE_VERSION_COUNT')
            require(fail_after!='activate','FIXTURE_INJECTED_FAILURE')
    return {'plan':plan,'transaction':'COMMITTED_FIXTURE_ONLY','rows_verified':len(pkg.users)+len(pkg.profiles)}
