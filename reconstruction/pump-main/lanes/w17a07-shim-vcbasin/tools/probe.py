#!/usr/bin/env python3
"""probe.py <base m.ll> <name> [edits.py] [--opt] [--llc <llc>]: IR probe (experiment only).
Applies EDITS (list of (old,new) exact single-occurrence replacements or callables) to a post-opt slim module,
optionally re-runs opt -O3 (--opt), runs the SDK llc like fastbuild, and prints M, region dM vs main,
and the TCF / wallet register maps (orig r8 in tcf; orig r9, r7 in wallet)."""
import sys,os,subprocess,runpy,json,difflib
from collections import Counter,defaultdict
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,regprof,xled,numpy as np
from regs import R
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a07-shim-vcbasin/pr')
OPT=[p for p in __import__('glob').glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))][0]
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; base=a.pop(0); name=a.pop(0); edits=None; doopt=False; llc=SDK+'/llc'; env=dict(os.environ)
while a:
    x=a.pop(0)
    if x=='--opt': doopt=True
    elif x=='--llc': llc=a.pop(0); env['RAPRIO_STICKY']='1'
    else: edits=x
d=OUT+'/'+name; os.makedirs(d,exist_ok=True)
t=open(base).read()
if edits:
    g=runpy.run_path(edits)
    for e in g['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
if doopt:
    r=subprocess.run([OPT,'-O3',d+'/m.ll','-S','-o',d+'/o3.ll'],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
    open(d+'/m.ll','w').write(oracle.slim(open(d+'/o3.ll').read())); os.remove(d+'/o3.ll')
r=subprocess.run([llc,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True,env=env)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
c=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(c); os.remove(d+'/m.o')
HR=regprof.hits('main')[0]; h,_=regprof.hits(d+'/fn.bin'); OO=np.array(regprof.OO); dr={}
for lo,hi,n in R:
    mm=(OO>=lo)&(OO<hi); x=int(h[mm].sum()-HR[mm].sum())
    if x: dr[n]=x
# register maps over skeleton-matched instructions
O=oracle.orig_window(); ot,oo=xled.toks(O); ct,co=xled.toks(c)
def rmap(lo,hi):
    m=defaultdict(Counter)
    for bl in difflib.SequenceMatcher(None,xled.fmask(ot),xled.fmask(ct),autojunk=False).get_matching_blocks():
        for k in range(bl.size):
            i=bl.a+k; j=bl.b+k
            if not (lo<=oo[i]<hi): continue
            for sh in (0,4):
                p=(ot[i][1]>>sh)&15; q=(ct[j][1]>>sh)&15
                if p==10 and q==10: continue
                m[p][q]+=1
    return m
mt=rmap(0x2600,0x3c00); mw=rmap(0x5a00,0x6c00)
f=lambda m,r: ' '.join(f'r{b}:{n}' for b,n in m[r].most_common(3))
res={'name':name,'bytes':len(c),'M':int(h.sum()),'dM':int(h.sum()-HR.sum()),'dreg':dr,
     'tcf_r8':f(mt,8),'tcf_r9':f(mt,9),'w_r9':f(mw,9),'w_r7':f(mw,7)}
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
