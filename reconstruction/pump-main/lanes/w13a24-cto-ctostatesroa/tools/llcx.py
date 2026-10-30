#!/usr/bin/env python3
"""llcx.py <name> <base m.ll> [edits.py]: apply EDITS to post-opt IR, llc like fastbuild, score. Experiment only."""
import sys,os,subprocess,runpy,json,re
sys.argv_save=sys.argv[:]
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a24-cto-ctostatesroa'
src=open(OUT+'/tools/rx.py').read(); pre=src[:src.index("OUT=os.environ.get('RX_OUT'")]
g={}; exec(pre,g)
name,base=sys.argv[1],sys.argv[2]; edits=sys.argv[3] if len(sys.argv)>3 else None
d=OUT+'/lx/'+name; os.makedirs(d,exist_ok=True)
t=open(base).read()
if edits:
    for e in runpy.run_path(edits)['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
cand=g['elf_fn'](d+'/m.o',g['KEEP']); orig=g['orig_window'](); rr,sd=g['metric'](cand,orig)
res={'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
