"""Official Superset REST API client; secrets stay in memory/local ignored env."""
import json,urllib.request,urllib.error,http.cookiejar
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[2]
class SupersetAPI:
 def __init__(self):
  self.base='http://127.0.0.1:8089';self.token=None;self.csrf=None
  self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  secret=dotenv_values(ROOT/'dashboard/superset/.env',interpolate=False)
  self.token=self.request('POST','/api/v1/security/login',{'username':'btl_admin','password':secret['ADMIN_PASSWORD'],'provider':'db','refresh':True})['access_token']
  self.csrf=self.request('GET','/api/v1/security/csrf_token/')['result']
 def request(self,method,path,body=None,raw=False):
  headers={'Content-Type':'application/json','Referer':self.base+'/'}
  if self.token:headers['Authorization']='Bearer '+self.token
  if self.csrf:headers['X-CSRFToken']=self.csrf
  req=urllib.request.Request(self.base+path,method=method,headers=headers,data=None if body is None else json.dumps(body).encode())
  try:
   with self.opener.open(req,timeout=120) as r:
    b=r.read();return b if raw else json.loads(b)
  except urllib.error.HTTPError as e:
   # Never expose raw request/response data (database API may echo credentials).
   raise RuntimeError('SUPERSET_HTTP_'+str(e.code)+'_'+path.split('?')[0]) from None
