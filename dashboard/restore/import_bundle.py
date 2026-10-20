"""Import authentic ZIP, then reconcile legacy layout on ISOLATED 8091 via REST."""
import json,hashlib,copy,subprocess,time
from datetime import datetime,timezone
from dotenv import dotenv_values
from common import ROOT,D,RestoreAPI,write
def main():
 start=time.monotonic();api=RestoreAPI();report={'at_utc':datetime.now(timezone.utc).isoformat(),'status':'FAIL','target':api.base,'overwrite':False,'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'import_bundle.py',D/'common.py']},'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
 try:
  assert api.base=='http://127.0.0.1:8091'
  for kind in ['dashboard','chart','dataset','database']:assert api.request('GET',f'/api/v1/{kind}/?q=(page_size:100)')['count']==0,'RESTORE_TARGET_NOT_EMPTY_INSPECT'
  inv=json.loads((D/'evidence/export_inventory.json').read_text(encoding='utf-8'));assert inv['status']=='PASS'
  data=(ROOT/'dashboard/superset_export.zip').read_bytes();assert hashlib.sha256(data).hexdigest()==inv['sha256']
  dbs=inv['inventory']['databases'];assert len(dbs)==1
  local=dotenv_values(ROOT/'dashboard/superset/.env.bi',interpolate=False)
  response=api.import_zip(data,{dbs[0]['path']:local['POSTGRES_PASSWORD']});report['import_response']=response
  write('evidence/import_attempt.json',report);assert response['http_status']==200,'OFFICIAL_IMPORT_FAILED'
  mapping={};idmaps={}
  before=json.loads((D/'evidence/production_before.json').read_text(encoding='utf-8'))['objects']
  for plural,kind in [('dashboards','dashboard'),('charts','chart'),('datasets','dataset'),('databases','database')]:
   entries=api.request('GET',f'/api/v1/{kind}/?q=(page_size:100)')['result'];assert len(entries)==len(inv['inventory'][plural])
   actual={}
   for entry in entries:
    obj=api.request('GET',f'/api/v1/{kind}/{entry["id"]}')['result'];actual[obj['uuid']]=entry['id']
   assert set(actual)=={x['uuid'] for x in inv['inventory'][plural]}
   mapping[kind]=actual
   if kind!='database':idmaps[kind]={int(key.split('/')[1]):actual[v['uuid']] for key,v in before.items() if key.startswith(kind+'/')}
  write('evidence/uuid_mapping.json',{'uuid_to_new_id':mapping,'old_id_to_new_id':idmaps,'source_export_sha256':inv['sha256']})
  repairs=[]
  for old_id,new_id in idmaps['dashboard'].items():
   source=before[f'dashboard/{old_id}'];layout=json.loads(source['position_json'])
   for node in layout.values():
    if isinstance(node,dict) and node.get('type')=='CHART':
     old_chart=node['meta']['chartId'];node['meta'].update(chartId=idmaps['chart'][old_chart],uuid=before[f'chart/{old_chart}']['uuid'])
   restored=api.request('GET',f'/api/v1/dashboard/{new_id}')['result'];meta=json.loads(restored['json_metadata']);expected_filters=copy.deepcopy(json.loads(source['json_metadata'])['native_filter_configuration'])
   for f in expected_filters:
    f['scope']['excluded']=[idmaps['chart'][x] for x in f['scope']['excluded']]
    for target in f.get('targets',[]):
     if target.get('datasetId') is not None:target['datasetId']=idmaps['dataset'][target['datasetId']]
   assert meta['native_filter_configuration']==expected_filters,'NATIVE_FILTER_IMPORT_MAPPING_MISMATCH'
   api.request('PUT',f'/api/v1/dashboard/{new_id}',{'position_json':json.dumps(layout,ensure_ascii=False)})
   got=api.request('GET',f'/api/v1/dashboard/{new_id}')['result'];assert json.loads(got['position_json'])==layout
   repairs.append({'old_dashboard':old_id,'new_dashboard':new_id,'reason':'Remove official-export orphan duplicates and remap legacy source layout with UUIDs','charts_in_layout':sum(isinstance(x,dict) and x.get('type')=='CHART' for x in layout.values()),'official_method':'PUT /api/v1/dashboard/<isolated_id>','metric_sql_filter_changed':False})
  report.update(status='PASS_IMPORT_AND_LAYOUT_RECONCILED',duration_seconds=round(time.monotonic()-start,3),zip_sha256=inv['sha256'],mapping_file='evidence/uuid_mapping.json',layout_reconciliation=repairs,urls={str(old):api.base+f'/superset/dashboard/{new}/' for old,new in idmaps['dashboard'].items()},credential_delivery='Official multipart passwords map, in memory from ignored BI config; URI not logged',production_write=False,restore_functionally_verified=False)
  write('evidence/import_result.json',report);print(json.dumps({'status':report['status'],'urls':report['urls'],'layout_reconciliation_count':len(repairs)}))
 except Exception as e:
  report['error_category']=str(e) if isinstance(e,AssertionError) else type(e).__name__;write('evidence/import_FAIL.json',report);raise
if __name__=='__main__':main()
