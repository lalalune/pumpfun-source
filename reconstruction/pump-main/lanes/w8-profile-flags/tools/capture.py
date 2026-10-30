#!/usr/bin/env python3
"""Lane-local capture (diagnostic only): fastbuild of a crate copy with --emit link,llvm-bc."""
import sys, subprocess, json, shutil
from pathlib import Path
T=Path(__file__).resolve().parents[4]/'harness'
sys.path.insert(0,str(T)); import fastbuild, build_process
src,work,out=map(Path,sys.argv[1:4]); extra=sys.argv[4:]
real=build_process.run_compiler
def hook(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit=link,llvm-bc']+extra
    return real(cmd,*a,**k)
fastbuild.run_compiler=hook
r=fastbuild.build(src,work,out,recipe='identity')
d=work/'target-identity/sbpf-solana-solana/release/deps'
for p in d.glob('pump_recovered*.bc'): shutil.copy2(p,out/'pump_recovered.bc')
print(json.dumps(r,indent=1))
