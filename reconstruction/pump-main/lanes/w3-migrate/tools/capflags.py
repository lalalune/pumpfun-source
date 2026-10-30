#!/usr/bin/env python3
"""capflags.py src work out [rustc flags...]: scratch build emitting llvm-ir with extra rustc flags; reduce module."""
import sys, subprocess, json, shutil
from pathlib import Path
T=Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
sys.path.insert(0,str(T)); import fastbuild
src,work,out=map(Path,sys.argv[1:4]); extra=sys.argv[4:]
real=subprocess.run
def hook(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit=link,llvm-ir']+extra
    return real(cmd,*a,**k)
subprocess.run=hook
try: r=fastbuild.build(src,work,out,recipe='identity')
finally: subprocess.run=real
if r.get('ok'):
    p=work/'target-identity/sbpf-solana-solana/release/deps/pump_recovered.ll'
    subprocess.run(['python3',str(Path(__file__).parent/'reduce.py'),str(p),str(out/'red.ll')])
print(json.dumps({k:r.get(k) for k in ('ok','seconds','unstripped_sha256')}))
