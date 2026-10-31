#!/usr/bin/env python3
"""post.py <src_rx> <name> <edits.py>: apply EDITS (callables or (old,new)) to rx/<src_rx>/m.ll (post-O3 slim IR), llc, score."""
import sys,os,subprocess,runpy,json
sys.path.insert(0,os.path.dirname(__file__)); import oracle
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,name,ed=sys.argv[1:4]; t=open(f'{OUT}/rx/{src}/m.ll').read()
for e in runpy.run_path(ed)['EDITS']:
    if callable(e): t=e(t); continue
    x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
d=f'{OUT}/rx/{name}'; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(cand)
rr,sd=oracle.metric(cand,oracle.orig_window()); res={'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
