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
def verify(args,output):
 snapshot=ROOT/'research/imported-lab';manifest=json.loads((ROOT/'research/import-manifest.json').read_text())
 for f in manifest['files']:
  # Explicit check instead of `assert`: `python -O` / PYTHONOPTIMIZE strips
  # asserts, so a tampered import would otherwise verify with exit 0.
  if sha(snapshot/f['path'])!=f['sha256']:raise AssertionError(f['path'])
 binary_matches={}
 for n in ['pump','pump_amm','pump_fees']:
  binary_matches[n]=sha(snapshot/f'inputs/pump_fun/{n}.so')==sha(ROOT/f'evidence/original/{n}/deployed.so')
  if not binary_matches[n]:raise AssertionError(n)
 docs_commit=json.loads((snapshot/'analysis/pump_fun/program-manifest.json').read_text())['official_docs_commit']
 subprocess.run(['git','-C',str(args.docs_checkout),'cat-file','-e',docs_commit+'^{commit}'],check=True)
 output.mkdir(exist_ok=True);replay=output/'lab';shutil.copytree(snapshot,replay);(replay/'third_party').mkdir()
 subprocess.run(['git','clone','--no-hardlinks','--quiet',str(args.docs_checkout.resolve()),str(replay/'third_party/pump-public-docs')],check=True)
 subprocess.run(['git','-C',str(replay/'third_party/pump-public-docs'),'checkout','--quiet','--detach',docs_commit],check=True)
 steps=[]
 def run(name,phase):
  r=subprocess.run([sys.executable,str(replay/'scripts'/f'{name}.py')],cwd=replay,capture_output=True,text=True)
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
