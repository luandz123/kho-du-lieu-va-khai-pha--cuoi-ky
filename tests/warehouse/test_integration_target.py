import unittest
from unittest.mock import patch,MagicMock
from etl.integration_target import IntegrationPermit,IntegrationConnection,assert_warehouse
from etl.s05_staging import SafeError
class TargetTests(unittest.TestCase):
 def permit(self):return IntegrationPermit('movielens_btl_int_20261023_abcdef12','abcdef12'+'0'*24,'postgres')
 def test_valid(self):self.assertIn('schema_sha256=',self.permit().marker)
 def test_production_rejected(self):
  with self.assertRaises(SafeError):IntegrationPermit('movielens_btl','a'*32,'postgres')
 def test_clone_rejected(self):
  with self.assertRaises(SafeError):IntegrationPermit('movielens_btl_restore_20261021_abcdef12','abcdef12'+'0'*24,'postgres')
 def test_name_run_mismatch(self):
  with self.assertRaises(SafeError):IntegrationPermit('movielens_btl_int_20261023_abcdef12','0'*32,'postgres')
 def test_ordinary_connection_uses_original_guard(self):
  c=MagicMock()
  with patch('etl.integration_target.assert_project') as guard:assert_warehouse(c);guard.assert_called_once_with(c)
 def test_wrong_marker_or_owner(self):
  c=MagicMock();c.permit=self.permit();q=c.cursor.return_value.__enter__.return_value;q.fetchone.return_value=(c.permit.database,'postgres','postgres','wrong')
  with self.assertRaises(SafeError):IntegrationConnection.verify_target(c)
 def test_no_permit(self):
  c=MagicMock();c.permit=None
  with self.assertRaises(SafeError):IntegrationConnection.verify_target(c)
if __name__=='__main__':unittest.main()
