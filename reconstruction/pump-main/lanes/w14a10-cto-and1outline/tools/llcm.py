#!/usr/bin/env python3
"""llcm.py <name> <base m.ll> [edits.py] [--llc args]: post-opt oracle. Apply EDITS ((old,new) exact, each once; or callables) to
the slimmed post-opt module, llc like fastbuild, score with oracle.metric. Experiment only."""
import sys,os,subprocess,runpy,json,time
sys.path.insert(0,os.path.dirname(__file__))
import oracle
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a10-cto-and1outline')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; name=a.pop(0); base=a.pop(0); edits=None; llcargs=[]
while a:
    x=a.pop(0)
    if x=='--llc': llcargs=a; a=[]
    else: edits=x
d=OUT+'/rx/'+name; os.makedirs(d,exist_ok=True); t0=time.time()
t=open(base).read()
if edits:
    g=runpy.run_path(edits)
    for e in g['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o',*llcargs],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(cand)
orig=oracle.orig_window(); rr,sd=oracle.metric(cand,orig)
res={'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd,'secs':round(time.time()-t0,1)}
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
