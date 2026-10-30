#!/usr/bin/env python3
"""llcx.py <name> <edits.py> [--base m.ll]: apply EDITS to post-opt slim module, llc like fastbuild, score."""
import sys,os,subprocess,runpy,json
sys.path.insert(0,os.path.dirname(__file__)); import oracle
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a38-cto-cbflagphi')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; name=a.pop(0); ed=a.pop(0); base=OUT+'/rx/base/m.ll'
if a and a[0]=='--base': base=a[1]
t=open(base).read()
for e in runpy.run_path(ed)['EDITS']:
    if callable(e): t=e(t); continue
    x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
d=OUT+'/lx/'+name; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(cand,oracle.orig_window())
print(json.dumps({'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}))
