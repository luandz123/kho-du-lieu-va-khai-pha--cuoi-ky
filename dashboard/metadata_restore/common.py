"""Same official API client with a guarded isolated endpoint and backed-up login."""
import sys,json,urllib.request,http.cookiejar
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'dashboard/overview'))
from superset_api import SupersetAPI
sys.path.insert(0,str(ROOT/'dashboard/restore'))
# Import business-object selection without importing a second common module.
import importlib.util
spec=importlib.util.spec_from_file_location('zip_common',ROOT/'dashboard/restore/common.py')
zip_common=importlib.util.module_from_spec(spec);spec.loader.exec_module(zip_common)
production_objects=zip_common.production_objects
D=Path(__file__).resolve().parent
def write(name,obj):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
class RestoreAPI(SupersetAPI):
 def __init__(self):
  self.base='http://127.0.0.1:8092';self.token=None;self.csrf=None
  self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  c=dotenv_values(D/'.env',interpolate=False)
  self.token=self.request('POST','/api/v1/security/login',{'username':'btl_admin','password':c['ADMIN_PASSWORD'],'provider':'db','refresh':True})['access_token']
  self.csrf=self.request('GET','/api/v1/security/csrf_token/')['result']
