"""12A static publication audit. No ETL/loader/DB/CLI/evaluator execution."""
import ast,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[2]
RID='57c1e8e3d3f445c4b3eeddbfc3364709'
RUN=ROOT/'results/warehouse/s12a'/RID
OUT=ROOT/'docs/P1/12a_publication'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allowed(p):
 return p in ('.env.example','README.md','requirements.txt','docs/integration_checklist.md') or p.startswith(('etl/','olap/','tests/warehouse/','results/warehouse/s12a/','docs/P1/','docs/agent/steps/P1/')) or (p.startswith('docs/agent/') and p.endswith('_P1.md'))
def write(name,obj):
 OUT.mkdir(parents=True,exist_ok=True);(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 assert git('branch','--show-current')=='codex/p1-s12a-integration'
 paths=set(git('diff','--name-only','origin/main...HEAD').splitlines())|set(git('diff','--name-only').splitlines())|set(git('diff','--cached','--name-only').splitlines())|{p for p in git('ls-files','--others','--exclude-standard').splitlines() if p!='docs/KE_HOACH_BTL_MOVIELENS.md'}
 paths-={'docs/P1/12a_publication/publication_audit.json','docs/P1/12a_publication/artifact_manifest.json'}
 assert paths and all(allowed(p) for p in paths),'OUT_OF_SCOPE_FILE'
 sensitive=[]
 for p in [ROOT/'.env',ROOT/'dashboard/superset/.env',ROOT/'dashboard/superset/.env.bi',ROOT/'dashboard/metadata_restore/.env']:
  for k,v in dotenv_values(p,interpolate=False).items():
   if v and any(w in k.upper() for w in ('PASSWORD','SECRET','TOKEN')):sensitive.append(v)
 counts={'python':0,'json':0,'text':0}
 for name in sorted(paths):
  p=ROOT/name;assert p.is_file() and p.suffix not in ('.csv','.dat','.dump','.backup','.zip','.log','.pkl','.joblib','.npz','.npy','.db','.pyc') and p.name not in ('.env','.env.bi'),'PRIVATE_OR_REMOVED_FILE'
  text=p.read_text(encoding='utf-8-sig');assert not any(v in text for v in sensitive if len(v)>=8),'KNOWN_SECRET_LITERAL'
  assert not re.search(r'postgres(?:ql)?(?:\+\w+)?://[^\s\"\']+:[^\s\"\']+@',text),'CREDENTIAL_URI'
  assert not re.search(r'\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}|(?:scrypt|pbkdf2):[^\s\"\']+\$[^\s\"\']+\$',text),'PASSWORD_HASH'
  assert not any(line.rstrip()!=line for line in text.splitlines()),'TRAILING_WHITESPACE'
  if p.suffix=='.py':
   tree=ast.parse(text,filename=name);assert not any(isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value in sensitive for n in ast.walk(tree)),'SECRET_PY_LITERAL';counts['python']+=1
  elif p.suffix=='.json':json.loads(text);counts['json']+=1
  else:counts['text']+=1
 r=json.loads((RUN/'summary.json').read_text(encoding='utf-8'));assert r['status']=='PASS_WAITING_REVIEW' and len(r['cycles'])==2
 for p,h in r['code_sha256'].items():assert sha(ROOT/p)==h,'RUNTIME_CODE_BYTES_CHANGED'
 bundle=hashlib.sha256(json.dumps(r['code_sha256'],sort_keys=True,separators=(',',':')).encode()).hexdigest();assert bundle=='3114721fd957a9c98da89b0bfcf615500ae6d6833bfdae31ad58111d23424e22'
 old=json.loads((RUN/'handoff_manifest.json').read_text(encoding='utf-8'))['files'];retained=0
 for p,h in old.items():
  if p.startswith('results/warehouse/s12a/'+RID+'/'):
   assert sha(ROOT/p)==h,'HISTORICAL_RUN_REPORT_CHANGED';retained+=1
 ref=json.loads((RUN/'official_test_metrics_reference.json').read_text(encoding='utf-8'))
 assert sha(ROOT/ref['source_report'])==ref['source_report_sha256'] and sha(ROOT/ref['source_receipt'])==ref['source_receipt_sha256'],'OFFICIAL_REPORT_OR_RECEIPT_CHANGED'
 frozen=['mining','tests/mining','docs/P2','data/source_manifest.json','docs/shared/data_contract.md','docs/shared/data_contract.json','database/schema.sql','database/views.sql','etl/s05_staging.py']
 assert not git('diff','--name-only','origin/main','--',*frozen),'P2_OR_ORIGINAL_GUARD_CONTRACT_DDL_CHANGED'
 assert sha(ROOT/'docs/KE_HOACH_BTL_MOVIELENS.md')=='da37e4a262541ad9f7957ded381cd1347a8e657709f8367fa2ec5ee4cd51d7c7','OUTSIDE_PLAN_CHANGED'
 private=[p for p in (ROOT/'tmp/s12a_private').rglob('*') if p.is_file()]+[p for p in (ROOT/'backups').rglob('*') if p.is_file()]+[ROOT/'.env',ROOT/'dashboard/superset/.env',ROOT/'dashboard/superset/.env.bi',ROOT/'dashboard/metadata_restore/.env',ROOT/'tmp/s12a-venv/pyvenv.cfg']
 for p in private:assert subprocess.run(['git','check-ignore','-q',str(p)],cwd=ROOT,capture_output=True).returncode==0,'PRIVATE_NOT_IGNORED'
 tracked=git('ls-files').splitlines();assert not any(p.startswith(('data/raw/','data/processed/','backups/','tmp/')) or Path(p).name in ('.env','.env.bi') or p.endswith(('.dump','.pkl','.joblib')) for p in tracked),'PRIVATE_TRACKED'
 subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,check=True)
 audit={'at_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_PUBLICATION_CHECKS','branch':git('branch','--show-current'),'head_observed':git('rev-parse','HEAD'),'base_main_observed':git('rev-parse','origin/main'),'files_checked':len(paths),'validation_counts':counts,'private_files_ignored':len(private),'historical_run_artifacts_unchanged':retained,'runtime_bundle_sha256':bundle,'runtime_code_bytes_unchanged':True,'official_test_receipt_and_report_unchanged':True,'p2_original_production_guard_contract_schema_unchanged':True,'outside_plan_preserved':True,'known_secret_uri_password_hash_scan':'PASS','ast_json_whitespace':'PASS','technical_review_source':'Coordinator accepted12A run57c1e8e3; no pipeline/test evaluator rerun for publication','unit_test_evidence':'88 tests passed in technical run; not rerun by this static audit','pipeline_etl_g3_dump_restore_evaluator_called':False,'p2_intake_g2':'NOT_CONFIRMED','g4_complete':False,'final_candidate_selected':False,'final_candidate_policy':'Merge commit of12A PR after review+merge; never this branch HEAD'}
 write('publication_audit.json',audit);paths.add('docs/P1/12a_publication/publication_audit.json')
 write('artifact_manifest.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Current working-tree publication bytes; excludes self and private files. Runtime ledger/receipts preserved; no new commit assigned to historical run.','files':{p:sha(ROOT/p) for p in sorted(paths)}})
 print(json.dumps({'status':audit['status'],'files_hashed':len(paths),'types':counts,'private_ignored':len(private),'historical_run_files_verified':retained,'runtime_code_unchanged':True}))
if __name__=='__main__':main()
