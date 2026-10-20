"""Official three-dashboard ZIP export; inventory UUID closure without logging secrets."""
import io,json,zipfile,subprocess,hashlib,re,urllib.parse,sys
from pathlib import Path
from datetime import datetime,timezone
from dotenv import dotenv_values
from common import ROOT,D,SupersetAPI,write,production_objects
from publication_policy import zip_state
PARSE=r'''import io,sys,zipfile,yaml,json
z=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()))
print(json.dumps({n:yaml.safe_load(z.read(n)) for n in z.namelist() if n.endswith(('.yaml','.yml'))}))'''
def parse_zip(data):
 p=subprocess.run(['docker','exec','-i','btl-movielens-superset-web-1','python','-c',PARSE],input=data,capture_output=True,timeout=60)
 if p.returncode:raise RuntimeError('YAML_PARSE_FAILED_NO_RAW_OUTPUT')
 return json.loads(p.stdout)
def main():
 target=ROOT/'dashboard/superset_export.zip'
 assert not target.exists() or '--inspect-existing' in sys.argv,'INSPECT_EXISTING_ZIP_DO_NOT_OVERWRITE'
 api=SupersetAPI()
 sys_path=str(ROOT/'dashboard/preferences')
 sys.path.insert(0,sys_path)
 from prepare import model_snapshot
 if target.exists():data=target.read_bytes()
 else:
  assert not (D/'evidence/production_before.json').exists(),'PRESERVE_BASELINE'
  write('evidence/production_before.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'objects':production_objects(api),'database':model_snapshot()})
  data=api.request('GET','/api/v1/dashboard/export/?q=!(1,2,3)',raw=True)
  target.write_bytes(data)
 z=zipfile.ZipFile(io.BytesIO(data));assert z.testzip() is None
 names=z.namelist();assert len(names)==len(set(names)),'DUPLICATE_MEMBERS'
 assert all(not n.startswith(('/','\\')) and '..' not in n.split('/') for n in names)
 parsed=parse_zip(data);objects={k:[] for k in ['dashboards','charts','datasets','databases']}
 for name,value in parsed.items():
  short=name.split('/',1)[1];kind=short.split('/')[0]
  if kind in objects:objects[kind].append((short,value))
 assert {k:len(v) for k,v in objects.items()}=={'dashboards':3,'charts':23,'datasets':6,'databases':1}
 inventory={k:[{'path':p,'uuid':v['uuid'],'name':v.get('dashboard_title',v.get('slice_name',v.get('table_name',v.get('database_name'))))} for p,v in rows] for k,rows in objects.items()}
 uuids={k:{v['uuid'] for p,v in rows} for k,rows in objects.items()}
 assert all(len(uuids[k])==len(rows) for k,rows in objects.items())
 edges=[];legacy_layout_nodes=0
 for p,v in objects['charts']:
  assert v['dataset_uuid'] in uuids['datasets'];edges.append([v['uuid'],v['dataset_uuid']])
 for p,v in objects['datasets']:
  assert v['database_uuid'] in uuids['databases'];edges.append([v['uuid'],v['database_uuid']])
 for p,v in objects['dashboards']:
  nodes=[node for node in v['position'].values() if isinstance(node,dict) and node.get('type')=='CHART']
  refs=[node['meta']['uuid'] for node in nodes if 'uuid' in node['meta']]
  legacy_layout_nodes+=sum('uuid' not in node['meta'] for node in nodes)
  assert set(refs)<=uuids['charts'];edges.extend([[v['uuid'],ref] for ref in refs])
  for f in v['metadata']['native_filter_configuration']:
   for t in f.get('targets',[]):
    if t:assert t['datasetUuid'] in uuids['datasets'];edges.append([v['uuid'],t['datasetUuid']])
 assert {b for a,b in edges if a in uuids['dashboards']} & uuids['charts']==uuids['charts']
 known=[]
 for path in [ROOT/'.env',ROOT/'dashboard/superset/.env',ROOT/'dashboard/superset/.env.bi',D/'.env']:
  for key,val in dotenv_values(path,interpolate=False).items():
   if val and len(val)>7 and any(x in key.upper() for x in ['PASSWORD','SECRET','TOKEN']):known.append(val)
 known.extend([api.token,api.csrf]);text='\n'.join(z.read(n).decode() for n in names if not n.endswith('/'))
 findings=[]
 if any(secret and secret in text for secret in known):findings.append('KNOWN_LOCAL_SECRET_BYTES_FOUND')
 def scan(value,path=''):
  if isinstance(value,dict):
   for k,v in value.items():
    key=k.lower();loc=path+'/'+k
    if ('password' in key or 'token' in key or 'private_key' in key or key in ['secret_key','encrypted_extra','masked_encrypted_extra','ssh_tunnel']) and v not in [None,'',{},False,'{}']:
     if not isinstance(v,str) or not re.fullmatch(r'[xX*]+',v):findings.append('NONEMPTY_SENSITIVE_FIELD:'+loc)
    if key=='sqlalchemy_uri' and v:
     uri=urllib.parse.urlsplit(v);pwd=urllib.parse.unquote(uri.password or '')
     if not pwd or not re.fullmatch(r'[xX*]+',pwd):findings.append('URI_PASSWORD_NOT_MASKED:'+loc)
     if uri.username!='movielens_bi_reader':findings.append('UNEXPECTED_DATABASE_ROLE')
    scan(v,loc)
  elif isinstance(value,list):
   for i,v in enumerate(value):scan(v,path+'/'+str(i))
 for name,value in parsed.items():scan(value,name)
 if re.search(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',text):findings.append('PRIVATE_KEY_MATERIAL')
 policy=zip_state(ROOT);ignored=policy['ignored']
 report={'status':'PASS' if not findings else 'REJECT_FOR_PUBLICATION','at_utc':datetime.now(timezone.utc).isoformat(),'mechanism':'GET /api/v1/dashboard/export/?q=!(1,2,3)','real_superset_zip':True,'zip_path':'dashboard/superset_export.zip','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'counts':{k:len(v) for k,v in objects.items()},'inventory':inventory,'dependency_edges_uuid':edges,'all_dependencies_resolved':True,'legacy_layout_nodes_without_uuid':legacy_layout_nodes,'restore_requires_uuid_layout_reconciliation':bool(legacy_layout_nodes),'members':[{'path':i.filename,'bytes':i.file_size,'sha256':hashlib.sha256(z.read(i)).hexdigest()} for i in z.infolist()],'secret_scan':{'known_local_secret_bytes_absent':not any(s and s in text for s in known),'database_uri_password_masked':not any('URI_' in x for x in findings),'findings':findings,'raw_uri_not_logged':True,'ssh_private_token_fields_reviewed':True},'zip_ignored':ignored,'publication_status':'LOCAL_ONLY_PENDING_REVIEW'}
 report['publication_status']=policy['phase']
 report['audit_code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 write('evidence/export_publication_audit.json' if policy['phase']=='AUTHORIZED_GIT_PUBLICATION' else 'evidence/export_inventory.json',report)
 print(json.dumps({k:report[k] for k in ['status','sha256','bytes','counts','all_dependencies_resolved','zip_ignored']}))
 assert not findings,'EXPORT_SENSITIVE_CONFIGURATION_REQUIRES_LOCAL_ONLY'
if __name__=='__main__':main()
