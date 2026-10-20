"""Official Superset HTTP API helpers; credentials remain local/in memory."""
import json,sys,urllib.request,urllib.error,http.cookiejar,uuid
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'dashboard/overview')]
from superset_api import SupersetAPI
D=ROOT/'dashboard/restore'
def write(name,obj):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
class RestoreAPI(SupersetAPI):
 def __init__(self):
  self.base='http://127.0.0.1:8091';self.token=None;self.csrf=None
  self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  c=dotenv_values(D/'.env',interpolate=False)
  self.token=self.request('POST','/api/v1/security/login',{'username':'btl_admin','password':c['ADMIN_PASSWORD'],'provider':'db','refresh':True})['access_token']
  self.csrf=self.request('GET','/api/v1/security/csrf_token/')['result']
 def import_zip(self,zipbytes,passwords):
  boundary='btl_'+uuid.uuid4().hex;parts=[]
  for name,val in [('overwrite','false'),('passwords',json.dumps(passwords))]:
   parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode())
  parts.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="formData"; filename="superset_export.zip"\r\nContent-Type: application/zip\r\n\r\n'.encode(),zipbytes,f'\r\n--{boundary}--\r\n'.encode()])
  req=urllib.request.Request(self.base+'/api/v1/dashboard/import/',method='POST',data=b''.join(parts),headers={'Content-Type':'multipart/form-data; boundary='+boundary,'Authorization':'Bearer '+self.token,'X-CSRFToken':self.csrf,'Referer':self.base+'/'})
  try:
   with self.opener.open(req,timeout=180) as r:return {'http_status':r.status,'response':json.loads(r.read())}
  except urllib.error.HTTPError as e:
   # Response may echo configuration. Emit only stable validation categories.
   raw=e.read()
   try:body=json.loads(raw);categories=[x.get('error_type') for x in body.get('errors',[])];fields=list(body.get('message',{})) if isinstance(body.get('message'),dict) else []
   except Exception:categories=[];fields=[]
   return {'http_status':e.code,'error_types':categories,'validation_fields':fields}
def production_objects(api):
 out={}
 for kind,ids,fields in [('dashboard',range(1,4),['dashboard_title','slug','position_json','json_metadata','css','uuid']),('dataset',range(1,7),['sql','metrics','columns','main_dttm_col','uuid']),('chart',range(1,24),['params','query_context','dashboards','slice_name','viz_type','uuid'])]:
  for i in ids:
   r=api.request('GET',f'/api/v1/{kind}/{i}')['result'];out[f'{kind}/{i}']={k:r.get(k) for k in fields}
 return out
