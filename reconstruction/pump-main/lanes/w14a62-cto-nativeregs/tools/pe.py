#!/usr/bin/env python3
"""pe.py <name> <edits.py> [--base m.ll]: post-opt IR edit (slim m.ll) -> llc -> score (oracle only)."""
import sys,os,subprocess,runpy,json,time
sa=sys.argv[:]; sys.argv=['x','n']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read().split('OUT=os.environ')[0])
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a62-cto-nativeregs')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sa[1:]; name=a.pop(0); ed=a.pop(0) if a and not a[0].startswith('--') else None; base=OUT+'/rx/base/m.ll'; llcargs=[]
while a:
    x=a.pop(0)
    if x=='--base': base=a.pop(0)
    elif x=='--llc': llcargs=a; a=[]
d=OUT+'/pe/'+name; os.makedirs(d,exist_ok=True); t=open(base).read()
if ed:
    for e in runpy.run_path(ed)['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o',*llcargs],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
cand=elf_fn(d+'/m.o',KEEP); open(d+'/fn.bin','wb').write(cand)
rr,sd=metric(cand,orig_window())
print(json.dumps({'name':name,'ratio':round(rr,5),'M':MM,'bytes':len(cand),'slots_diff':sd}))
