#!/usr/bin/env python3
"""Lane-local capture: build a scratch crate copy with --emit llvm-ir and optional llvm-args. Never used for proposals."""
import sys, subprocess, json, shutil, os
from pathlib import Path
T=Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r1-sweep-ir/reconstruction/harness')
sys.path.insert(0,str(T)); import fastbuild
src,work,out=map(Path,sys.argv[1:4]); llvm=sys.argv[4:]
real=fastbuild.run_compiler
def hook(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit='+os.environ.get('EMIT','link,llvm-ir')]+os.environ.get('RFLAGS','').split()+[x for v in llvm for x in ('-C','llvm-args='+v)]
    return real(cmd,*a,**k)
fastbuild.run_compiler=hook
r=fastbuild.build(src,work,out,recipe='identity')
if r.get('ok'):
    d=work/'target-identity/sbpf-solana-solana/release/deps'
    for ext in ('ll','bc','mir'):
        p=d/f'pump_recovered.{ext}'
        if p.exists(): shutil.copy2(p,out/f'pump_recovered.{ext}'); p.unlink()
print(json.dumps(r,indent=1))
