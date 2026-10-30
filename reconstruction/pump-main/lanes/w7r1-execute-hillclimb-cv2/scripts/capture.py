#!/usr/bin/env python3
"""capture.py FILE.rs OUTDIR [llvm-args...]: scratch build (src-2/work-2) with --emit llvm-ir; extracts execute fn IR. Diagnostic only."""
import sys, os, shutil, re, json
from pathlib import Path
L='w7r1-execute-hillclimb-cv2'
OUT=Path.home()/f'.cache/pumpfun-reconstruction/lanes/{L}'
H=Path(f'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/{L}/reconstruction/harness')
sys.path.insert(0,str(H)); os.environ['PUMP_BUILD_SLOTS']='10'
import fastbuild
f,out=sys.argv[1],Path(sys.argv[2]); llvm=sys.argv[3:]; out.mkdir(parents=True,exist_ok=True)
src=OUT/'src-2'; work=OUT/'work-2'
shutil.copy2(f,src/'src/create_v2.rs')
real=fastbuild.run_compiler
def hook(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit=link,llvm-ir']+[x for v in llvm for x in ('-C','llvm-args='+v)]
    return real(cmd,*a,**k)
fastbuild.run_compiler=hook
r=fastbuild.build(src,work,out,quiet=True,recipe='identity')
d=work/'target-identity/sbpf-solana-solana/release/deps'
p=d/'pump_recovered.ll'
if r.get('ok') and p.exists():
    shutil.move(str(p),out/'pump_recovered.ll')
    t=(out/'pump_recovered.ll').read_text()
    m=re.search(r'\ndefine [^\n]*create_v27execute17h[^\n]*\n',t)
    if m:
        i=m.start()+1; j=t.index('\n}\n',i)+3; (out/'exec.ll').write_text(t[i:j])
(out/'candidate.so').unlink(missing_ok=True)
print(json.dumps({'ok':r.get('ok')}))
