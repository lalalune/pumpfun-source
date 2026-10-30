#!/usr/bin/env python3
"""Lane-local (experiment): fastbuild via `cargo rustc --lib -- <args>` so extra flags reach only the root crate."""
import sys, json
from pathlib import Path
T=Path(__file__).resolve().parents[4]/'harness'
sys.path.insert(0,str(T)); import fastbuild, build_process
src,work,out=map(Path,sys.argv[1:4]); extra=sys.argv[4:]
real=build_process.run_compiler
def hook(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--']+extra
    return real(cmd,*a,**k)
fastbuild.run_compiler=hook
print(json.dumps(fastbuild.build(src,work,out,recipe='identity'),indent=1))
