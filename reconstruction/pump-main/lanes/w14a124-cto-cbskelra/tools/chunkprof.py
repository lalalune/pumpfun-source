#!/usr/bin/env python3
"""chunkprof.py <cand> [--ref main] [--sz 0x200]: per orig 0x200 chunk: tokens, orig-only (unmatched) tokens under
M (scorer mask), rM (register-masked), skM (skeleton: regs+frame+jump+lea+call masked). With --ref, prints deltas vs ref."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
def fm(t):
    out=[]
    for x in t:
        x=bytearray(x); op=x[0]; cl=op&7
        if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
        if op==0x07: x[4:8]=b'\0'*4
        out.append(bytes(x))
    return out
def rm(t): return [bytes([x[0],0])+x[2:] for x in t]
O=oracle.orig_window(); ot,oo=xled.toks(O)
def prof(p,sz):
    C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,_=xled.toks(C)
    res={}
    for nm,f in (('M',lambda t:t),('rM',rm),('fM',fm),('skM',xled.fmask)):
        a=f(ot); b=f(ct); h=[0]*len(a)
        for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
            for k in range(bl.size): h[bl.a+k]=1
        per={}
        for i,x in enumerate(h):
            c=oo[i]//sz; per.setdefault(c,[0,0]); per[c][0]+=1; per[c][1]+=(1-x)
        res[nm]=per
    return res,len(C)
a=sys.argv[1:]; sz=0x200; ref=None
if '--sz' in a: i=a.index('--sz'); sz=int(a[i+1],16); del a[i:i+2]
if '--ref' in a: i=a.index('--ref'); ref=a[i+1]; del a[i:i+2]
r,nb=prof(a[0],sz); rr=prof(ref,sz)[0] if ref else None
print(f'cand {a[0]} bytes {nb}  (orig-only tokens per orig chunk; lower is better)')
print(f"{'chunk':>13s} {'tok':>4s} {'M_oo':>5s} {'rM_oo':>5s} {'fM_oo':>5s} {'sk_oo':>5s}"+('  dM drM dfM dsk' if ref else ''))
tot=[0,0,0,0]
for c in sorted(r['M']):
    n=r['M'][c][0]; v=[r[k][c][1] for k in ('M','rM','fM','skM')]; tot=[x+y for x,y in zip(tot,v)]
    s=f'{c*sz:#06x}-{(c+1)*sz:#06x} {n:4d} {v[0]:5d} {v[1]:5d} {v[2]:5d} {v[3]:5d}'
    if rr: s+='  '+' '.join(f'{v[j]-rr[k][c][1]:+3d}' for j,k in enumerate(('M','rM','fM','skM')))
    print(s)
print('total orig-only', tot)
