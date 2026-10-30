#!/usr/bin/env python3
"""cap.py <srcname>: build $OUT/src/<name> with --emit=link,llvm-ir,mir into $OUT/ir/<name>/ (base.ll, module.mir, unstripped.so)"""
import json, os, sys, shutil
from pathlib import Path
OUT=Path(os.path.expanduser(os.environ.get('OUT','~/.cache/pumpfun-reconstruction/lanes/w7r1-buyexactquoteinh-frame')))
H=Path(__file__).resolve().parents[3]/'harness'
sys.path.insert(0,str(H)); import fastbuild
name=sys.argv[1]; o=OUT/'ir'/(sys.argv[2] if len(sys.argv)>2 else name); o.mkdir(parents=True,exist_ok=True)
real=fastbuild.run_compiler
def rc(cmd,*a,**k):
    cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit=link,llvm-ir,mir']+os.environ.get('EXTRA','').split()
    if os.environ.get('EXTRA'): k['env']=dict(k['env'],RUSTC_BOOTSTRAP='1')
    return real(cmd,*a,**k)
fastbuild.run_compiler=rc
work=OUT/('workir'+os.environ.get('WS',''))
res=fastbuild.build(OUT/'src'/name, work, o, quiet=True)
d=work/'target-identity/sbpf-solana-solana/release/deps'
for ext,dst in (('ll','base.ll'),('mir','module.mir')):
    fs=sorted(d.glob(f'pump_recovered*.{ext}'),key=lambda p:p.stat().st_mtime)
    if fs: shutil.move(str(fs[-1]),o/dst)
print(json.dumps({k:res.get(k) for k in ('ok','unstripped_sha256','seconds')}))
