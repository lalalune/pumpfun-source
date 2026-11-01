#!/usr/bin/env python3
"""Experiment-only builder (layout-order-census): fastbuild staging + optional Linux -vV shim + crate rename.
xbuild.py --src DIR --work DIR --out DIR [--linuxvv] [--jobs N]
"""
import argparse, os, sys, subprocess, shutil, tomllib, json, time
from pathlib import Path
TOOLS=Path('./worktrees/restore/reconstruction')
sys.path.insert(0,str(TOOLS/'harness'))
import fastbuild as F
ap=argparse.ArgumentParser(); ap.add_argument('--src',type=Path,required=True); ap.add_argument('--work',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True); ap.add_argument('--linuxvv',action='store_true'); ap.add_argument('--shim',default='rustc-linuxvv'); ap.add_argument('--jobs',default='2')
a=ap.parse_args()
R=F.RECIPES['identity']; triple=R['triple']
work=a.work.resolve(); out=a.out.resolve(); work.mkdir(parents=True,exist_ok=True); out.mkdir(parents=True,exist_ok=True)
ws=work/'ws'; crate=F.stage(a.src.resolve(),ws)
man=tomllib.loads((crate/'Cargo.toml').read_text()); pkg=man['package']['name']; lib=man.get('lib',{}).get('name',pkg.replace('-','_'))
target=work/(('target-'+a.shim) if a.linuxvv else 'target-identity')
if not target.exists() and not a.linuxvv and R['template'].exists():
    subprocess.run(['cp','-cRp',str(R['template']),str(target)],check=True)
env=os.environ.copy(); env.pop('CARGO_BUILD_TARGET_DIR',None); reg=Path.home()/'.cargo'
env.update(RUSTC_WRAPPER=str(F.H/'pump_physical_source_wrapper.py'),PUMP_LOGICAL_REGISTRY_SRC=str(reg/'registry/src'),CARGO_HOME=str(reg),
  CARGO_TARGET_DIR=str(target),CARGO_BUILD_JOBS=a.jobs,RUSTC=str(Path(__file__).resolve().parent/a.shim) if a.linuxvv else str(R['rustc']),
  CC=str(F.SDK/'llvm/bin/clang'),AR=str(F.SDK/'llvm/bin/llvm-ar'),OBJDUMP=str(F.SDK/'llvm/bin/llvm-objdump'),OBJCOPY=str(F.SDK/'llvm/bin/llvm-objcopy'))
env['CARGO_TARGET_'+triple.upper().replace('-','_')+'_RUSTFLAGS']='-Zremap-cwd-prefix='
env.pop('RUSTFLAGS',None); env.pop('CARGO_ENCODED_RUSTFLAGS',None)
for fp in list(target.glob(f'*/release/.fingerprint/{pkg}-*')): shutil.rmtree(fp,ignore_errors=True)
for so in target.glob(f'*/release/{lib}.so'): so.unlink()
cmd=[str(F.SDK/'rust/bin/cargo'),'build','-v','--manifest-path',str(crate/'Cargo.toml'),'--release','--target',triple,'--locked','--offline']
slot=F.acquire_slot(); t0=time.time()
try: r=subprocess.run(cmd,cwd=ws,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
finally: slot.close()
(out/'build.log').write_text(r.stdout)
if r.returncode: print(r.stdout[-4000:]); sys.exit(1)
built=target/triple/'release'/f'{lib}.so'; shutil.copy2(built,out/'unstripped.so')
print(json.dumps({'ok':True,'seconds':round(time.time()-t0,1),'unstripped':str(out/'unstripped.so'),'sha256':F.sha(out/'unstripped.so')}))
