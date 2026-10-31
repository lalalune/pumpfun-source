#!/usr/bin/env python3
"""Verify frozen lab import and replay saved receipts in a disposable local tree.
Optional runtime replay submits signed transactions ONLY to offline loopback Surfpool.
Complete output is published with atomic no-replace semantics and normal umask
permissions; inputs cannot overlap the output tree.
"""
import argparse,hashlib,json,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from deep_disassembly import rename_directory,temporary_sibling
VERIFIERS=['pump_fun_verify_offline','pump_fun_admin_surfpool_verify','pump_fun_amm_v2_surfpool_verify','pump_fun_curve_fresh_surfpool_verify','pump_fun_curve_migration_surfpool_verify','pump_fun_post_migration_amm_surfpool_verify','pump_fun_fees_withdraw_surfpool_verify']
REPLAY=['pump_fun_admin_surfpool','pump_fun_amm_buy_v2_surfpool','pump_fun_curve_create_v2_surfpool','pump_fun_fees_withdraw_surfpool']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_snapshot(snapshot,manifest):
 if snapshot.is_symlink():raise ValueError('import snapshot root is a symlink')
 files=manifest.get('files')
 if type(files)is not list or not files:raise ValueError('import manifest requires a non-empty files list')
 if any(type(row)is not dict or type(row.get('path'))is not str or type(row.get('sha256'))is not str for row in files):raise ValueError('import manifest file metadata is invalid')
 listed=[row['path'] for row in files]
 if len(set(listed))!=len(listed):raise ValueError('import manifest contains duplicate file paths')
 entries=list(snapshot.rglob('*'))
 for path in entries:
  relative=path.relative_to(snapshot)
  if path.is_symlink():raise ValueError('import snapshot contains a symlink: '+relative.as_posix())
  if '__pycache__'in relative.parts or path.suffix in('.pyc','.pyo'):raise ValueError('import snapshot contains bytecode cache: '+relative.as_posix())
  if not path.is_dir()and not path.is_file():raise ValueError('import snapshot contains a non-regular entry: '+relative.as_posix())
 on_disk={path.relative_to(snapshot).as_posix() for path in entries if path.is_file()}
 unlisted=sorted(on_disk-set(listed));absent=sorted(set(listed)-on_disk)
 if unlisted or absent:raise AssertionError(f'import manifest coverage mismatch: unlisted files {unlisted}, listed but absent {absent}')
 for row in files:
  if sha(snapshot/row['path'])!=row['sha256']:raise AssertionError(row['path'])

def verify(args,output):
 snapshot=ROOT/'research/imported-lab';manifest=json.loads((ROOT/'research/import-manifest.json').read_text())
 verify_snapshot(snapshot,manifest)
 binary_matches={}
 for n in ['pump','pump_amm','pump_fees']:
  binary_matches[n]=sha(snapshot/f'inputs/pump_fun/{n}.so')==sha(ROOT/f'evidence/original/{n}/deployed.so')
  if not binary_matches[n]:raise AssertionError(n)
 docs_commit=json.loads((snapshot/'analysis/pump_fun/program-manifest.json').read_text())['official_docs_commit']
 subprocess.run(['git','-C',str(args.docs_checkout),'cat-file','-e',docs_commit+'^{commit}'],check=True)
 output.mkdir(exist_ok=True);replay=output/'lab';shutil.copytree(snapshot,replay)
 # Check the bytes that will execute, including changes during the copy.
 verify_snapshot(replay,manifest)
 (replay/'third_party').mkdir()
 subprocess.run(['git','clone','--no-hardlinks','--quiet',str(args.docs_checkout.resolve()),str(replay/'third_party/pump-public-docs')],check=True)
 subprocess.run(['git','-C',str(replay/'third_party/pump-public-docs'),'checkout','--quiet','--detach',docs_commit],check=True)
 steps=[]
 def run(name,phase):
  r=subprocess.run([sys.executable,'-B',str(replay/'scripts'/f'{name}.py')],cwd=replay,capture_output=True,text=True)
  log=output/f'{phase}-{name}.log';log.write_text(r.stdout+r.stderr,encoding='utf-8',newline='\n')
  steps.append({'script':name,'phase':phase,'exit_code':r.returncode,'log_sha256':sha(log)})
  print(phase,name,r.returncode,flush=True);return r.returncode==0
 initial=all([run(n,'saved') for n in VERIFIERS]);runtime=None;tool=None
 if args.surfpool:
  tool=args.surfpool.resolve();version=subprocess.check_output([str(tool),'--version'],text=True).strip()
  if version!='surfpool 1.6.1':raise AssertionError(version)
  (replay/'tools').mkdir();shutil.copy2(tool,replay/'tools/surfpool')
  runtime=all([run(n,'runtime') for n in REPLAY])
  if runtime:runtime=all([run(n,'fresh') for n in VERIFIERS])
 report={'source_commit':manifest['commit'],'imported_file_count':len(manifest['files']),'all_import_hashes_verified':True,'original_binary_matches':binary_matches,'docs_commit':docs_commit,'saved_receipt_verifiers_passed':initial,'fresh_offline_runtime_passed':runtime,'surfpool_sha256':sha(tool) if tool else None,'steps':steps,'scope':'Import integrity, original binary correspondence, and bounded offline paths only. No exact program source builds or complete security audit claimed.'}
 (output/'integration-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 return initial,runtime


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--docs-checkout',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);ap.add_argument('--surfpool',type=pathlib.Path);args=ap.parse_args()
 output=args.output.resolve()
 if output.exists() or output.is_symlink():raise FileExistsError(output)
 for source in ((ROOT/'research/imported-lab').resolve(),args.docs_checkout.resolve()):
  if output==source or source in output.parents or output in source.parents:
   raise ValueError('output must not overlap imported lab or docs inputs')
  # Case aliases can be physically identical despite different resolve() spellings.
  if source.exists():
   for ancestor in (output,*output.parents):
    if ancestor.exists() and ancestor.samefile(source):
     raise ValueError('output must not overlap imported lab or docs inputs')
 output.parent.mkdir(parents=True,exist_ok=True)
 staging=temporary_sibling(output,'staging')
 try:
  initial,runtime=verify(args,staging)
  rename_directory(staging,output)
 except BaseException:
  shutil.rmtree(staging,ignore_errors=True)
  raise
 if not initial or runtime is False:raise SystemExit(1)
if __name__=='__main__':main()
