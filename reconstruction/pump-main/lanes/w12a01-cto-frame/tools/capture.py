#!/usr/bin/env python3
"""Lane-local capture: scratch build with --emit link,llvm-ir(,mir). Research only, never used for proposals.
capture.py <src> <work> <out>"""
import sys, json, shutil, os
from pathlib import Path
T=Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a01-cto-frame/reconstruction/harness')
sys.path.insert(0,str(T)); import fastbuild
src,work,out=map(Path,sys.argv[1:4])
real=fastbuild.run_compiler
def hook(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit='+os.environ.get('EMIT','link,llvm-ir')]
    return real(cmd,*a,**k)
fastbuild.run_compiler=hook
try: r=fastbuild.build(src,work,out,recipe='identity')
finally: fastbuild.run_compiler=real
if r.get('ok'):
    d=work/'target-identity/sbpf-solana-solana/release/deps'
    for ext in ('ll','mir'):
        p=d/f'pump_recovered.{ext}'
        if p.exists(): shutil.copy2(p,out/f'pump_recovered.{ext}'); p.unlink()
print(json.dumps({k:r.get(k) for k in ('ok','seconds','unstripped_sha256','error')}))
