import importlib.util,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path('dashboard/metadata_restore').resolve()))
import restore_metadata as m
class Guards(unittest.TestCase):
 def valid(self):return {'Name':'/'+m.META,'Config':{'Labels':{'btl.run_id':'test','btl.purpose':m.PURPOSE}},'Mounts':[{'Type':'volume','Name':m.PROJECT+'_restore_metadata'}]}
 def test_valid(self):m.guard_resource(self.valid(),'test')
 def test_production(self):
  v=self.valid();v['Name']='/btl-movielens-superset-metadata-1'
  with self.assertRaises(AssertionError):m.guard_resource(v,'test')
 def test_old_restore(self):
  v=self.valid();v['Name']='/btl-movielens-s11b4-restore-metadata-1'
  with self.assertRaises(AssertionError):m.guard_resource(v,'test')
 def test_bad_volume(self):
  v=self.valid();v['Mounts'][0]['Name']='btl-movielens-superset_metadata_data'
  with self.assertRaises(AssertionError):m.guard_resource(v,'test')
 def test_bad_run(self):
  with self.assertRaises(AssertionError):m.guard_resource(self.valid(),'wrong')
if __name__=='__main__':unittest.main()
