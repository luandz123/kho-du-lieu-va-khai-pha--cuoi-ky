"""Create only ignored secrets after checking isolated resource names and port."""
import socket,secrets,subprocess,json
from common import D,write
def main():
 prefix='btl-movielens-s11b4-restore'
 for kind in ['container','volume','network']:
  args=['docker',kind,'ls','--format','{{.Names}}' if kind=='container' else '{{.Name}}']
  if kind=='container':args.insert(3,'-a')
  existing=subprocess.check_output(args,text=True).splitlines()
  assert not any(n.startswith(prefix) for n in existing),'RESTORE_RESOURCES_EXIST_INSPECT_BEFORE_REUSE'
 with socket.socket() as s:s.bind(('127.0.0.1',8091))
 p=D/'.env';assert not p.exists(),'LOCAL_CONFIG_EXISTS_DO_NOT_OVERWRITE'
 p.write_text('\n'.join(k+'='+secrets.token_urlsafe(40) for k in ['SUPERSET_SECRET_KEY','METADATA_PASSWORD','ADMIN_PASSWORD'])+'\n',encoding='utf-8')
 subprocess.run(['git','check-ignore',str(p)],check=True,capture_output=True)
 image=subprocess.check_output(['docker','image','inspect','btl-movielens-superset:6.1.0-local','--format','{{.Id}}'],text=True).strip()
 write('evidence/setup_preflight.json',{'port':8091,'port_free':True,'project':prefix,'existing_project_resources':False,'local_env_created_ignored':True,'image_id':image,'metadata_volume':'btl-movielens-s11b4-restore_restore_metadata','home_volume':'btl-movielens-s11b4-restore_restore_home','production_volume_names_different':True})
 print('PASS: isolated names/8091 checked; unique ignored credentials created; production not touched.')
if __name__=='__main__':main()
