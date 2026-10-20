"""Distinguish immutable historical local-only evidence from approved ZIP publication."""
import json,hashlib,subprocess
from pathlib import Path
PIN='b5a9c987e7d1e7f56b21f92785370cdb9089a4d1efc01c128568127d938f6fae'
ZIP='dashboard/superset_export.zip'
def evaluate_zip_state(digest,ignored,approval):
 if approval is None:
  if not ignored:raise ValueError('UNAPPROVED_ZIP_MUST_BE_IGNORED')
  return {'phase':'LOCAL_ONLY_PENDING_REVIEW','sha256':digest,'ignored':True}
 if approval.get('phase')!='AUTHORIZED_GIT_PUBLICATION' or approval.get('path')!=ZIP or approval.get('sha256')!=PIN or digest!=PIN:raise ValueError('ZIP_PUBLICATION_IDENTITY_MISMATCH')
 if ignored:raise ValueError('APPROVED_ZIP_EXACT_EXCEPTION_MISSING')
 return {'phase':'AUTHORIZED_GIT_PUBLICATION','sha256':digest,'ignored':False}
def zip_state(root):
 root=Path(root);p=root/'dashboard/restore/publication_approval.json'
 approval=json.loads(p.read_text(encoding='utf-8')) if p.exists() else None
 def ignored(path):return subprocess.run(['git','check-ignore','--no-index',str(path)],cwd=root,capture_output=True).returncode==0
 state=evaluate_zip_state(hashlib.sha256((root/ZIP).read_bytes()).hexdigest(),ignored(root/ZIP),approval)
 if not ignored(root/'dashboard/other_unapproved.zip'):raise ValueError('GLOBAL_ZIP_IGNORE_WEAKENED')
 return state
