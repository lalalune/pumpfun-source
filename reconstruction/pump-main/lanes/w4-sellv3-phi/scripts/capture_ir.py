#!/usr/bin/env python3
"""capture_ir.py <src crate> <out dir>: build with --emit=link,llvm-ir on the root crate (experiment only)."""
import subprocess,sys,shutil
from pathlib import Path
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
import fastbuild
real=subprocess.run
def emit(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit=link,llvm-ir']
    return real(cmd,*a,**k)
src=Path(sys.argv[1]); out=Path(sys.argv[2]); work=Path(sys.argv[3]) if len(sys.argv)>3 else Path.home()/'.cache/pumpfun-reconstruction/lanes/w4-sellv3-phi/work-ir'
subprocess.run=emit
try: r=fastbuild.build(src,work,out,recipe='identity')
finally: subprocess.run=real
print(r)
ll=work/'target-identity/sbpf-solana-solana/release/deps/pump_recovered.ll'
shutil.copy2(ll,out/'module.ll')
