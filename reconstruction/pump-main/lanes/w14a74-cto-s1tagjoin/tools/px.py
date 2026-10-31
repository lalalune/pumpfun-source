#!/usr/bin/env python3
"""px.py <name> <base m.ll> [edits.py] [--dbg] : post-opt IR oracle (experiment only). Applies EDITS (exact (old,new)
pairs, each occurring once, or callables text->text) to an rx.py slimmed post-opt module, runs llc exactly like rx.py
and scores. --dbg also writes the greedy regalloc log (debug llc) to px/<name>/ra.log."""
import sys,os,subprocess,runpy,json,time
sys.argv_save=sys.argv
D=os.path.dirname(os.path.abspath(__file__))
src=open(D+'/rx.py').read(); pre=src[:src.index("OUT=os.environ.get")]
g={'__name__':'rxlib'}; exec(pre,g)
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a74-cto-s1tagjoin')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
DBG=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
a=sys.argv[1:]; name=a.pop(0); base=a.pop(0); edits=None; dbg=False
for x in a:
    if x=='--dbg': dbg=True
    else: edits=x
d=OUT+'/px/'+name; os.makedirs(d,exist_ok=True); t0=time.time()
t=open(base).read()
if edits:
    for e in runpy.run_path(edits)['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
F=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o']
r=subprocess.run([SDK+'/llc',*F],capture_output=True,text=True)
if r.returncode: print(json.dumps({'name':name,'error':r.stderr[-1500:]})); sys.exit(1)
if dbg:
    subprocess.run([DBG,*F[:-1],d+'/dbg.o','-debug-only=regalloc'],capture_output=True,text=True,stdout=None) if False else None
    with open(d+'/ra.log','w') as fo: subprocess.run([DBG,*F[:-1],d+'/dbg.o','-debug-only=regalloc'],stderr=fo,stdout=subprocess.DEVNULL)
cand=g['elf_fn'](d+'/m.o',g['KEEP']); open(d+'/fn.bin','wb').write(cand)
rr,sd=g['metric'](cand,g['orig_window']())
res={'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd,'secs':round(time.time()-t0,1)}
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
