"""Explicit integration connection context. Original production guard unchanged."""
from dataclasses import dataclass
import re
import psycopg2
from psycopg2 import extensions
from etl.s05_staging import SafeError,assert_project,sha256,ROOT
@dataclass(frozen=True)
class IntegrationPermit:
    database:str
    run_id:str
    owner:str
    def __post_init__(self):
        if not re.fullmatch(r'movielens_btl_int_[0-9]{8}_[0-9a-f]{8}',self.database) or not re.fullmatch(r'[0-9a-f]{32}',self.run_id) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',self.owner):
            raise SafeError('INVALID_INTEGRATION_PERMIT')
        if not self.database.endswith(self.run_id[:8]):raise SafeError('INTEGRATION_RUN_NAME_MISMATCH')
    @property
    def marker(self):return f'BTL P1 12A isolated integration; run={self.run_id}; schema_sha256={sha256(ROOT/"database/schema.sql")}'
class IntegrationConnection(extensions.connection):
    permit:IntegrationPermit
    def verify_target(self):
        permit=getattr(self,'permit',None)
        if type(permit) is not IntegrationPermit:raise SafeError('MISSING_INTEGRATION_PERMIT')
        with self.cursor() as q:
            q.execute("SELECT current_database(),current_user,pg_get_userbyid(datdba),shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database()")
            if q.fetchone()!=(permit.database,permit.owner,permit.owner,permit.marker):raise SafeError('INTEGRATION_TARGET_IDENTITY_MISMATCH')
def integration_connect(c,permit,*,readonly=False):
    conn=psycopg2.connect(host=c['POSTGRES_HOST'],port=int(c['POSTGRES_PORT']),dbname=permit.database,user=c['POSTGRES_USER'],password=c['POSTGRES_PASSWORD'],connection_factory=IntegrationConnection,connect_timeout=10,options='-c timezone=UTC -c lock_timeout=10000 -c statement_timeout=300000')
    conn.permit=permit
    if readonly:conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
    with conn:conn.verify_target()
    return conn
def assert_warehouse(conn):
    if type(conn) is IntegrationConnection:return conn.verify_target()
    return assert_project(conn)
