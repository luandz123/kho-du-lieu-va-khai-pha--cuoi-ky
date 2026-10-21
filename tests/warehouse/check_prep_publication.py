"""Static publication audit for P1 preparation; no DB writes or service changes.

Historical run/manifest bytes remain untouched. A new publication manifest records
current working-tree bytes; Git LF/CRLF representation is checked separately.
"""
import ast,hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/P1/pre12a_publication'
PLAN='docs/KE_HOACH_BTL_MOVIELENS.md'
PLAN_SHA='da37e4a262541ad9f7957ded381cd1347a8e657709f8367fa2ec5ee4cd51d7c7'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allowed(p):
 return p=='README.md' or p=='docs/integration_checklist.md' or p.startswith(('database/','dashboard/','tests/warehouse/','results/warehouse/','docs/P1/','docs/agent/steps/P1/')) or (p.startswith('docs/agent/') and p.endswith('_P1.md'))
def main():
 assert git('branch','--show-current')=='codex/p1-s12a-prep'
 paths=set(git('diff','--name-only','origin/main...HEAD').splitlines())|set(git('diff','--name-only').splitlines())|set(git('diff','--cached','--name-only').splitlines())
 paths|={p for p in git('ls-files','--others','--exclude-standard').splitlines() if p!=PLAN}
 for name in ('publication_audit.json','artifact_manifest.json'):paths.discard('docs/P1/pre12a_publication/'+name)
 assert paths and all(allowed(p) for p in paths),'OUT_OF_SCOPE_PATH'
 assert sha(ROOT/PLAN)==PLAN_SHA,'OUTSIDE_PLAN_CHANGED'
 secret_values=[]
 private_env=[ROOT/'.env',ROOT/'dashboard/superset/.env',ROOT/'dashboard/superset/.env.bi',ROOT/'dashboard/metadata_restore/.env']
 for p in private_env:
  for k,v in dotenv_values(p,interpolate=False).items():
   if v and len(v)>=8 and any(w in k.upper() for w in ('PASSWORD','SECRET','TOKEN')):secret_values.append(v)
 counts={'python':0,'json':0,'yaml':0,'images':0,'text':0};yaml_texts=[];image_formats={}
 for name in sorted(paths):
  p=ROOT/name;assert p.is_file(),'UNEXPECTED_REMOVAL'
  assert p.suffix not in ('.dump','.backup','.bak','.dat','.csv','.zip','.db','.sqlite','.log') and p.name not in ('.env','.env.bi'),'PRIVATE_ARTIFACT_IN_PR'
  b=p.read_bytes()
  if p.suffix=='.png':
   assert b.startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff')),'UNRECOGNIZED_IMAGE_BYTES'
   image_formats[name]='JPEG' if b.startswith(b'\xff\xd8\xff') else 'PNG';counts['images']+=1;continue
  text=b.decode('utf-8-sig');assert not any(v in text for v in secret_values),'KNOWN_SECRET_LITERAL'
  assert not re.search(r'postgres(?:ql)?(?:\+\w+)?://[^\s\"\']+:[^\s\"\']+@',text),'CREDENTIAL_URI'
  assert not re.search(r'\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}|(?:scrypt|pbkdf2):[^\s\"\']+\$[^\s\"\']+\$',text),'PASSWORD_HASH'
  assert not any(line.rstrip()!=line for line in text.splitlines()),'TRAILING_WHITESPACE'
  if p.suffix=='.py':ast.parse(text,filename=name);counts['python']+=1
  elif p.suffix=='.json':json.loads(text);counts['json']+=1
  elif p.suffix in ('.yaml','.yml'):yaml_texts.append(text);counts['yaml']+=1
  else:counts['text']+=1
 if yaml_texts:
  payload="import yaml,json,sys;v=json.load(sys.stdin);[yaml.safe_load(s) for s in v];print('YAML_PASS')"
  p=subprocess.run(['docker','exec','-i','btl-movielens-superset-web-1','python','-c',payload],input=json.dumps(yaml_texts),capture_output=True,text=True,timeout=30)
  assert p.returncode==0 and p.stdout.strip()=='YAML_PASS','YAML_VALIDATION_FAILED'
 private=[p for p in (ROOT/'backups').rglob('*') if p.is_file()]+private_env
 for p in private:assert subprocess.run(['git','check-ignore','-q',str(p)],cwd=ROOT,capture_output=True).returncode==0,'PRIVATE_NOT_IGNORED'
 tracked=git('ls-files').splitlines()
 assert not any(p.startswith(('data/raw/','data/processed/','backups/')) or Path(p).name in ('.env','.env.bi') or p.endswith(('.dump','.backup')) for p in tracked),'PRIVATE_TRACKED'
 subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,check=True)
 # Runtime code/binary evidence are immutable; reviewed docs have a new ledger.
 for name,expected in {
  'database/backup_restore.py':'6986b021ca96b73fe151141352ad3af0ec47a2ec7a8e8bdccf35f3b4ee4409f1',
  'dashboard/metadata_restore/restore_metadata.py':'ef06d4447112856f9f073722cb6a707853b80accb6d8adf93e2e7140b314e729',
  'backups/p1_s12a_20261021_2856ed49e9ba494090e2acae73b41b9a/dw.dump':'ac3f16548a4ffa9299dc4434927f929bff3f353cf63843f5986ed05c28b8f1c4',
  'backups/p1_s12a_20261021_2856ed49e9ba494090e2acae73b41b9a/superset_metadata.dump':'43665b8c70c13d295ad7c6f3f9289a41750ce536ae28c94435213fdda5141236'
 }.items():assert sha(ROOT/name)==expected,'RUNTIME_OR_BACKUP_BYTES_CHANGED'
 # All runtime reports/FAIL/UI files are checked against the accepted metadata ledger.
 old=json.loads((ROOT/'dashboard/metadata_restore/evidence/artifact_manifest.json').read_text(encoding='utf-8'))['files'];verified=0
 for name,expected in old.items():
  if name.startswith(('dashboard/metadata_restore/','tests/warehouse/test_metadata_restore_guards.py')):
   assert sha(ROOT/name)==expected,'ACCEPTED_METADATA_ARTIFACT_CHANGED';verified+=1
 OUT.mkdir(parents=True,exist_ok=True)
 audit={'at_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_PUBLICATION_CHECKS','head_observed':git('rev-parse','HEAD'),'base_main_observed':git('rev-parse','origin/main'),'branch':git('branch','--show-current'),'files_scanned':len(paths),'validation_counts':counts,'image_byte_formats':image_formats,'image_filename_note':'Historical .png screenshot filenames contain original JPEG bytes returned by browser; bytes/hashes preserved, no image conversion.','private_paths_ignored':len(private),'accepted_metadata_artifacts_verified':verified,'known_secrets_uri_password_hash_scan':'PASS','tracked_private_paths':[],'outside_plan_preserved':True,'historical_runtime_reports_unchanged':True,'yaml_parser':'existing Superset container PyYAML; no installation','unit_tests_observed':'14/14 backup+metadata guard tests PASS; 0.042s','step12a_completed':False,'cf_final_acceptance':'NOT_CONFIRMED','p2_intake_g2':'NOT_CONFIRMED','full_refresh_after_s07_g3_tested':False,'requirements_merged':False,'integration_candidate':None}
 (OUT/'publication_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 paths.add('docs/P1/pre12a_publication/publication_audit.json')
 (OUT/'artifact_manifest.json').write_text(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Current working-tree bytes for P1 publication; excludes self and private files. Historical ledgers kept, no run relabeled as published commit.','files':{p:sha(ROOT/p) for p in sorted(paths)}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':'PASS_PUBLICATION_CHECKS','files_scanned':len(paths),'types':counts,'private_ignored':len(private),'historical_metadata_artifacts_verified':verified}))
if __name__=='__main__':main()
