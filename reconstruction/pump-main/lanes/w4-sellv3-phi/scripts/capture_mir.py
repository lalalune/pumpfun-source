#!/usr/bin/env python3
"""capture_pre.py <src> <out>: build with -C no-prepopulate-passes --emit=llvm-bc (experiment only), copy pre-opt bitcode."""
import subprocess,sys,shutil
from pathlib import Path
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-sellv3-phi/reconstruction/harness')
import fastbuild
real=subprocess.run
def emit(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit=mir']
    return real(cmd,*a,**k)
src=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
work=Path.home()/'.cache/pumpfun-reconstruction/lanes/w4-sellv3-phi/work-mir'
subprocess.run=emit
try: r=fastbuild.build(src,work,out,recipe='identity')
except Exception as e: r=repr(e)
finally: subprocess.run=real
print(str(r)[:300])
bc=work/'target-identity/sbpf-solana-solana/release/deps/pump_recovered.mir'
shutil.copy2(bc,out/'out.mir')
