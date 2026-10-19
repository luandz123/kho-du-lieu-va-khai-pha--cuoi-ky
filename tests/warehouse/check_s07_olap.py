"""Invented PostgreSQL OLAP fixture; all fixture DDL/data rolled back."""
import json
import re
import sys
import time
import uuid
from datetime import date,datetime,timezone
from decimal import Decimal
from pathlib import Path

from psycopg2 import sql
from psycopg2.extras import execute_values

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from etl.run_etl import atomic_json
from etl.s05_staging import assert_project,catalog,config,connect,sha256
from olap.run_olap import CODE,guard_signature,queries,rows


def main():
    run=uuid.uuid4().hex;schema='s07_test_'+run[:12];start=time.monotonic()
    report={'step':'S07_FIXTURE','run_id':run,'status':'FAIL','fixture':'INVENTED_ONLY',
            'code_sha256':{p:sha256(ROOT/p) for p in CODE},'test_code_sha256':sha256(Path(__file__))}
    conn=None
    try:
        conn=connect(config(ROOT/'.env'))
        with conn:
            assert_project(conn);catalog(conn);before=guard_signature(conn)
            with conn.cursor() as c:
                c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
                ddl=re.sub(r'--[^\n]*','',(ROOT/'database/schema.sql').read_text(encoding='utf-8'))
                statements=re.findall(r'^CREATE TABLE dw\.[\s\S]*?;',ddl,flags=re.M)
                assert len(statements)==6
                for statement in statements:c.execute(statement.replace('dw.',schema+'.'))
                c.execute(f"INSERT INTO {schema}.dim_genre(genre_name) VALUES ('Comedy'),('Drama'),('Fantasy')")
                c.execute(f"INSERT INTO {schema}.dim_movie(movie_id,title,release_year) VALUES (701,'Two genres',NULL),(702,'Comedy only',2000),(703,'No ratings',NULL)")
                users=[(101,'F','18-24',4),(2000,'M','18-24',4),(3000,'M','25-34',4)]+[(i,'F','18-24',4) for i in range(1000,1100)]
                execute_values(c,f'INSERT INTO {schema}.dim_user(user_id,gender,age_group,occupation) VALUES %s',users)
                c.execute(f"INSERT INTO {schema}.dim_date(full_date) SELECT s::date FROM generate_series('2000-01-15'::timestamp,'2001-01-15'::timestamp,interval '1 day') s")
                c.execute(f"INSERT INTO {schema}.bridge_movie_genre SELECT m.movie_key,g.genre_key FROM {schema}.dim_movie m CROSS JOIN {schema}.dim_genre g WHERE (m.movie_id=701 AND g.genre_name IN ('Comedy','Drama')) OR (m.movie_id=702 AND g.genre_name='Comedy')")
                c.execute(f'SELECT user_id,user_key FROM {schema}.dim_user');um=dict(c.fetchall())
                c.execute(f'SELECT movie_id,movie_key FROM {schema}.dim_movie');mm=dict(c.fetchall())
                c.execute(f'SELECT full_date,date_key FROM {schema}.dim_date');dm=dict(c.fetchall())
                source=[(101,701,5,date(2000,1,15))]+[(i,701,4,date(2000,7,15)) for i in range(1000,1100)]+[(2000,701,1,date(2000,7,15))]+[(i,702,4,date(2000,10,15)) for i in range(1000,1100)]+[(101,702,2,date(2001,1,15))]
                facts=[]
                for u,m,r,d in source:
                    instant=datetime(d.year,d.month,d.day,tzinfo=timezone.utc)
                    facts.append((um[u],mm[m],dm[d],r,int(instant.timestamp()),instant))
                execute_values(c,f'INSERT INTO {schema}.fact_rating(user_key,movie_key,date_key,rating,rating_timestamp,rated_at) VALUES %s',facts)
                script=(ROOT/'database/views.sql').read_text(encoding='utf-8').replace('analytics.',schema+'.').replace('dw.',schema+'.')
                c.execute(script)
            q={k:v.replace('analytics.',schema+'.').replace('dw.',schema+'.') for k,v in queries().items()}
            k=rows(conn,q['O1'])[0];assert (k['catalog_users'],k['catalog_movies'],k['rated_users'],k['rated_movies'],k['rating_count'],k['rating_sum'])==(103,3,102,2,203,808)
            o3=rows(conn,q['O3'],{'gender':None,'genres':['Comedy'],'ages':['18-24']})[0]
            assert o3['rating_count']==203 and o3['rating_sum']==808
            assert abs(o3['mean_rating']-Decimal(808)/203)<Decimal('1e-15')
            f=rows(conn,q['O3'],{'gender':'F','genres':['Comedy'],'ages':['18-24']})[0]
            m=rows(conn,q['O3'],{'gender':'M','genres':['Comedy'],'ages':['18-24']})[0]
            assert (f['rating_count'],m['rating_count'])==(202,1)
            assert abs(o3['mean_rating']-(f['mean_rating']+m['mean_rating'])/2)>1
            o4=rows(conn,q['O4']);assert all(sum(x['rating_count'] for x in o4 if x['time_level']==level)==203 for level in ['year','quarter','month'])
            assert next(x for x in o4 if x['time_level']=='quarter' and x['calendar_year']==2000 and x['quarter_number']==2)['rating_count']==0
            o5=rows(conn,q['O5']);assert len(o5)==15
            assert all(x['rating_count']==0 for x in o5 if x['quarter_start']==date(2000,4,1))
            assert all(x['qoq_pct'] is None for x in o5 if x['quarter_start']==date(2000,7,1))
            q4=[x for x in o5 if x['quarter_start']==date(2000,10,1)]
            assert len([x for x in q4 if x['eligible_for_ranking']])==2
            drama=next(x for x in q4 if x['genre_name']=='Drama');assert drama['previous_rating_count']==101 and drama['qoq_pct']==-100
            assert all(x['growth_rank'] is None for x in o5 if x['is_boundary_partial'] or x['previous_is_boundary_partial'])
            july=[x for x in o5 if x['quarter_start']==date(2000,7,1)];assert july[0]['genre_assignment_total']==202 and july[0]['system_rating_count']==101
            assert sum(x['genre_share_pct'] for x in july)==100
            args={'gender':None,'genres':['Comedy','Drama'],'ages':['18-24'],'start_date':date(2000,7,1),'end_date':date(2001,1,1)}
            o6=rows(conn,q['O6'],args);assert sum(x['rating_count'] for x in o6)==201 and sum(x['rating_sum'] for x in o6)==801
            args['gender']='F';assert sum(x['rating_count'] for x in rows(conn,q['O6'],args))==200
            args['ages']=['25-34'];assert not rows(conn,q['O6'],args)
            assert len(rows(conn,q['O2']))==2
            conn.rollback() # Restore the DB, removing every invented schema/table/view/row.
        with conn:
            catalog(conn);assert guard_signature(conn)==before
            with conn.cursor() as c:
                c.execute('SELECT count(*) FROM pg_namespace WHERE nspname=%s',(schema,));assert c.fetchone()[0]==0
        report.update(status='PASS',checks={'unique_kpi_and_multi_genre':True,'weighted_mean_unequal_groups':True,
            'zero_quarter_before_lag':True,'previous_zero_null_qoq':True,'fixed_100_threshold':True,
            'boundary_ranking_excluded':True,'genre_assignment_denominator':True,'combined_filters_exists_no_duplication':True,
            'rollup_each_level_matches_fact':True,'fixture_schema_rolled_back':True,'production_unchanged':True},
            fixture_totals={'unique_ratings':203,'rating_sum':808,'genre_grid_rows':15,'combined_filter_ratings':201,'female_slice':200})
    except Exception as e:
        if conn:conn.rollback()
        report.update(error_category=getattr(e,'code',type(e).__name__),sqlstate=getattr(e,'pgcode',None))
    finally:
        if conn:conn.close()
    report['duration_seconds']=round(time.monotonic()-start,3)
    path=ROOT/'results/olap'/('s07_fixture_'+run+'.json');atomic_json(path,report)
    print(json.dumps({'status':report['status'],'report':str(path.relative_to(ROOT)),'error_category':report.get('error_category'),'sqlstate':report.get('sqlstate')}))
    return 0 if report['status']=='PASS' else 2


if __name__=='__main__':raise SystemExit(main())
