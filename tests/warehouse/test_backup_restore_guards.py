"""Pure safety tests; never create/drop/truncate a database."""
import unittest,tempfile,hashlib
from pathlib import Path
from database.backup_restore import (Permit,validate_target_name,require_clone_identity,
 official_restore_args,validate_toc,SafeError)

class RestoreGuardTests(unittest.TestCase):
 def setUp(self):self.target='movielens_btl_restore_20261021_1234abcd';self.permit=Permit(self.target,'run-1','a'*64)
 def test_production_rejected(self):
  with self.assertRaises(SafeError):validate_target_name('movielens_btl')
 def test_maintenance_and_unrelated_rejected(self):
  for name in ['postgres','template0','template1','unrelated','movielens_btl_restore_20261021_1234abcd;DROP DATABASE x']:
   with self.subTest(name=name),self.assertRaises(SafeError):validate_target_name(name)
 def test_exact_approved_clone_marker_accepted(self):require_clone_identity(self.target,self.permit.marker,self.permit)
 def test_other_valid_clone_rejected(self):
  with self.assertRaises(SafeError):require_clone_identity('movielens_btl_restore_20261021_deadbeef',self.permit.marker,self.permit)
 def test_wrong_marker_rejected(self):
  with self.assertRaises(SafeError):require_clone_identity(self.target,'copied source marker',self.permit)
 def test_restore_has_no_create_clean_or_no_owner_acl(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'fixture.dump';path.write_bytes(b'synthetic archive fixture');permit=Permit(self.target,'run-1',hashlib.sha256(path.read_bytes()).hexdigest())
   args=official_restore_args({'POSTGRES_HOST':'localhost','POSTGRES_PORT':5432,'POSTGRES_USER':'fixture'},permit,path)
   self.assertEqual(args[args.index('--dbname')+1],self.target)
   self.assertIn('--single-transaction',args);self.assertIn('--exit-on-error',args)
   for bad in ['--create','--clean','--no-owner','--no-acl']:self.assertNotIn(bad,args)
 def test_archive_bytes_changed_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'fixture.dump';path.write_bytes(b'changed')
   with self.assertRaises(SafeError):official_restore_args({},self.permit,path)
 def test_database_commands_in_archive_rejected(self):
  for text in ['1; 0 0 DATABASE - movielens_btl postgres','1; 0 0 COMMENT - DATABASE movielens_btl postgres','1; 0 0 DATABASE PROPERTIES - movielens_btl postgres']:
   with self.subTest(text=text),self.assertRaises(SafeError):validate_toc(text)
 def test_project_object_toc_accepted(self):self.assertEqual(validate_toc('; synthetic\n1; 0 1 TABLE dw dim_user postgres\n2; 0 2 TABLE DATA dw dim_user postgres'),2)
if __name__=='__main__':unittest.main()
