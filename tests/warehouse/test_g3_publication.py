"""Regression: preserve historical producer identity after P2 code evolves."""
import sys,hashlib,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from etl import g3_intake as g
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'dashboard/restore'))
from publication_policy import evaluate_zip_state,PIN,ZIP

class ProducerTests(unittest.TestCase):
 def run_check(self,*,dirty=False,expected=None,ancestor=True):
  with TemporaryDirectory() as t:
   root=Path(t);(root/'mining').mkdir();(root/'mining/clustering.py').write_bytes(b'new head\n' if not dirty else b'local edit\n')
   producer=b'old approved producer\n';expected=expected or hashlib.sha256(producer.replace(b'\n',b'\r\n')).hexdigest()
   with patch.object(g,'ROOT',root),patch.object(g.subprocess,'check_output',side_effect=[b'new head\n',producer]) as show,patch.object(g.subprocess,'run',return_value=SimpleNamespace(returncode=0 if ancestor else 1)):
    g.verify_producer_code('clustering',expected)
    self.assertEqual(show.call_args_list[1].args[0][2],g.APPROVED_PRODUCER_COMMIT+':mining/clustering.py')
 def test_historical_windows_bytes_accepted_after_head_changes(self):self.run_check()
 def test_wrong_producer_hash_rejected(self):
  with self.assertRaises(g.SafeError) as e:self.run_check(expected='0'*64)
  self.assertEqual(e.exception.code,'P2_CODE_PROVENANCE')
 def test_dirty_p2_copy_rejected(self):
  with self.assertRaises(g.SafeError) as e:self.run_check(dirty=True)
  self.assertEqual(e.exception.code,'P2_CODE_NOT_MERGED')
 def test_unrelated_producer_rejected(self):
  with self.assertRaises(g.SafeError) as e:self.run_check(ancestor=False)
  self.assertEqual(e.exception.code,'APPROVED_PRODUCER_NOT_IN_HISTORY')

class ZipPolicyTests(unittest.TestCase):
 def approval(self):return {'phase':'AUTHORIZED_GIT_PUBLICATION','path':ZIP,'sha256':PIN}
 def test_local_stage_remains_ignored(self):self.assertEqual(evaluate_zip_state(PIN,True,None)['phase'],'LOCAL_ONLY_PENDING_REVIEW')
 def test_unapproved_unignored_rejected(self):
  with self.assertRaisesRegex(ValueError,'UNAPPROVED'):evaluate_zip_state(PIN,False,None)
 def test_exact_approved_zip_can_publish(self):self.assertFalse(evaluate_zip_state(PIN,False,self.approval())['ignored'])
 def test_different_payload_rejected(self):
  with self.assertRaisesRegex(ValueError,'IDENTITY'):evaluate_zip_state('0'*64,False,self.approval())
 def test_different_path_rejected(self):
  a=self.approval();a['path']='other.zip'
  with self.assertRaisesRegex(ValueError,'IDENTITY'):evaluate_zip_state(PIN,False,a)
 def test_ignored_approved_payload_needs_exact_exception(self):
  with self.assertRaisesRegex(ValueError,'EXCEPTION'):evaluate_zip_state(PIN,True,self.approval())
if __name__=='__main__':unittest.main()
