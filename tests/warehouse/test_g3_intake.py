"""Synthetic-only G3 rejection tests; no production rows/credentials in fixtures."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from etl.g3_intake import (Package,SafeError,csv_rows,read_package,validate_records,registry_metadata,existing_plan)
from etl.g3_transaction import fixture_transaction

def sample(version='fixture-v1'):
    users=[(10,0,'assigned',version),(20,1,'assigned',version),(30,None,'insufficient_evidence',version)]
    profiles=[(0,'Action',0.25,1),(0,'Comedy',0.75,1),(1,'Action',0.5,1),(1,'Comedy',0.5,1)]
    m={'model_version':version,'contract_version':2,'training_config':{'k':2,'seed':42,'n_init':10,'preprocessing':'raw','genre_order':['Action','Comedy']},
       'libraries':{'python':'3.12.14','numpy':'2.0.2'},'canonical_hashes':{k:'a'*64 for k in ['users','movies','movie_genres','ratings']},
       'source_hashes':{k:'b'*64 for k in ['users.dat','movies.dat','ratings.dat','README']},'training_config_hash':'c'*64,
       'generated_at_utc':'2026-10-20T00:00:00Z','code_provenance':{'synthetic':True}}
    return Package(m,users,profiles,{'user_cluster.csv':'d'*64,'cluster_genre_profile.csv':'e'*64},'f'*64)

def raw(pkg):
    return [[str(u),'' if c is None else str(c),s,v] for u,c,s,v in pkg.users],[[str(c),g,str(x),str(n)] for c,g,x,n in pkg.profiles]

def existing(pkg,active=True,valid=True):
    m=pkg.manifest
    return {'preprocessing':registry_metadata(pkg),'libraries':m['libraries'],'canonical_hashes':m['canonical_hashes'],
            'source_hashes':m['source_hashes'],'training_config_hash':m['training_config_hash'],'k':2,'seed':42,'genre_order':['Action','Comedy'],
            'is_active':active,'is_valid_for_dw':valid}

class ValidationTests(unittest.TestCase):
    def setUp(self):self.pkg=sample();self.u,self.p=raw(self.pkg)
    def validate(self):return validate_records(self.u,self.p,version='fixture-v1',k=2,genres=['Action','Comedy'],user_ids={10,20,30})
    def reject(self,code):
        with self.assertRaises(SafeError) as err:self.validate()
        self.assertEqual(err.exception.code,code)
    def test_valid_synthetic(self):self.assertEqual(self.validate()[2],{0:1,1:1})
    def test_duplicate_user(self):self.u.append(self.u[0]);self.reject('DUPLICATE_USER')
    def test_orphan_user(self):self.u[0][0]='99';self.reject('ORPHAN_USER')
    def test_missing_user(self):self.u.pop();self.reject('USER_COHORT_INCOMPLETE')
    def test_assigned_null(self):self.u[0][1]='';self.reject('ASSIGNED_NULL_CLUSTER')
    def test_insufficient_not_null(self):self.u[2][1]='0';self.reject('INSUFFICIENT_NON_NULL_CLUSTER')
    def test_invalid_status(self):self.u[0][2]='unknown';self.reject('INVALID_STATUS')
    def test_invalid_cluster(self):self.u[0][1]='2';self.reject('CLUSTER_OUT_OF_RANGE')
    def test_row_version(self):self.u[0][3]='other';self.reject('ROW_MODEL_VERSION')
    def test_missing_genre(self):self.p.pop();self.reject('PROFILE_GRID_INCOMPLETE')
    def test_unknown_genre(self):self.p[0][1]='Unknown';self.reject('PROFILE_GENRE_OR_CLUSTER')
    def test_duplicate_profile(self):self.p.append(self.p[0]);self.reject('DUPLICATE_PROFILE')
    def test_bad_n_users(self):self.p[0][3]='2';self.reject('PROFILE_N_USERS')
    def test_nonfinite(self):
        for val in ['NaN','inf','-inf','1.1','-0.1']:
            with self.subTest(value=val):self.p[0][2]=val;self.reject('PROFILE_MEAN_DOMAIN')
    def test_sum_not_one(self):self.p[0][2]='0.2';self.reject('PROFILE_SUM')
    def test_noncanonical_integer(self):self.u[0][0]='010';self.reject('INVALID_INTEGER')
    def test_encoding_rejected(self):
        for b in [b'\xef\xbb\xbfuser_id\n',b'user_id\r\n']:
            with self.assertRaises(SafeError):csv_rows(b,'user_cluster.csv')
    def test_incomplete_package(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SafeError) as e:read_package(d)
            self.assertEqual(e.exception.code,'PACKAGE_INCOMPLETE')
    def test_checksum_and_frozen_rejections_before_db(self):
        # Entirely synthetic metadata/bytes: portable without a local G3 package.
        from etl.g3_intake import VERSION,PINNED
        m={'contract_version':2,'model_version':VERSION,'algorithm':'KMeans',
           **{k:{} for k in ['training_config','libraries','canonical_hashes','source_hashes','code_provenance','data_summary']},
           'files':{name:{'sha256':h} for name,h in PINNED.items()}}
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            for name in ['user_cluster.csv','cluster_genre_profile.csv']:(d/name).write_bytes(b'synthetic,fixture\n')
            for expected in ['MANIFEST_CHECKSUM_MISMATCH','FROZEN_PAYLOAD_MISMATCH']:
                (d/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(SafeError) as e:read_package(d)
                self.assertEqual(e.exception.code,expected)
                for n in ['user_cluster.csv','cluster_genre_profile.csv']:m['files'][n]['sha256']=hashlib.sha256((d/n).read_bytes()).hexdigest()
    def test_same_version_changed_payload(self):
        old=existing(self.pkg);self.pkg.payload_sha256['user_cluster.csv']='0'*64
        with self.assertRaises(SafeError) as e:existing_plan(old,self.pkg,self.pkg.users,self.pkg.profiles)
        self.assertEqual(e.exception.code,'VERSION_PAYLOAD_CONFLICT')
    def test_same_version_missing_rows_conflict(self):
        with self.assertRaises(SafeError):existing_plan(existing(self.pkg),self.pkg,[],[])
    def test_invalidated_identical_reload(self):self.assertEqual(existing_plan(existing(self.pkg,False,False),self.pkg,[],[]),'RELOAD_IDENTICAL_INVALIDATED_VERSION')
    def test_production_write_guard(self):
        with self.assertRaises(SafeError) as e:fixture_transaction(None,self.pkg,schema='analytics')
        self.assertEqual(e.exception.code,'PRODUCTION_WRITE_DISABLED_11B1')

if __name__=='__main__':unittest.main()
