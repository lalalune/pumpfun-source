#!/usr/bin/env python3
"""Lane-local IR capture (experiment only, never for proposals)."""
import sys, json, shutil
from pathlib import Path
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[4]/'harness')); import fastbuild
src,work,out=map(Path,sys.argv[1:4])
real=fastbuild.run_compiler
def hook(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit=link,llvm-ir']
    return real(cmd,*a,**k)
fastbuild.run_compiler=hook
r=fastbuild.build(src,work,out,recipe='identity')
if r.get('ok'):
    p=work/'target-identity/sbpf-solana-solana/release/deps/pump_recovered.ll'
    shutil.copy2(p,out/'pump_recovered.ll')
print(json.dumps({k:r.get(k) for k in ('ok','unstripped_sha256')}))
