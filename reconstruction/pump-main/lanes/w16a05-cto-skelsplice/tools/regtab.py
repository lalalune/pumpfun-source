#!/usr/bin/env python3
"""regtab.py <idxS.npz> [--top N] [--md]: region-local re-rank of archived builds. For each sub-region: builds ranked by
skeleton gain dSk (orig tokens skeleton-matched in the region minus main's), with their region-local dM and the
M collateral outside the region (dM_out). Source builds only (res.json present, no relabel/RA-force suffix)."""
import sys,os,re
import numpy as np
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled,difflib
from regs import R
LANES=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
O=oracle.orig_window(); OT,OO=xled.toks(O); OF=xled.fmask(OT); OO=np.array(OO); N=len(OT)
def mainhits():
    C=xled.load('main'); ct,_=xled.toks(C); hm=np.zeros(N,bool); hs=np.zeros(N,bool)
    for bl in difflib.SequenceMatcher(None,OT,ct,autojunk=False).get_matching_blocks(): hm[bl.a:bl.a+bl.size]=True
    for bl in difflib.SequenceMatcher(None,OF,xled.fmask(ct),autojunk=False).get_matching_blocks(): hs[bl.a:bl.a+bl.size]=True
    return hm,hs
a=sys.argv[1:]; top=8; md="--md" in a; a=[x for x in a if x!="--md"]; minM=0
if "--minM" in a: i=a.index("--minM"); minM=int(a[i+1]); del a[i:i+2]
if '--top' in a: i=a.index('--top'); top=int(a[i+1]); del a[i:i+2]
Z=np.load(a[0]); names=[os.path.relpath(str(x),LANES).replace('/rx/','/').replace('/fn.bin','') for x in Z['names']]; nb=Z['nbytes']
ok=np.array([not re.search(r'(p2|ra|perm|relab|force|_hc)$',n) and (n.endswith('.so') or os.path.exists(os.path.join(LANES,n.split('/')[0],'rx',n.split('/',1)[1],'res.json'))) for n in names])
HM=Z["MP"]>=0; HS=Z["SP"]>=0; hm,hs=mainhits(); ok&=(HM.sum(1)>=minM)
rows=[]
for lo,hi,n in R:
    m=(OO>=lo)&(OO<hi)
    dsk=HS[:,m].sum(1)-hs[m].sum(); dm=HM[:,m].sum(1)-hm[m].sum(); dout=HM[:,~m].sum(1)-hm[~m].sum()
    dsk=np.where(ok,dsk,-999)
    o=np.lexsort((-dout,-dm,-dsk))[:top]
    print(f'== {n} {lo:04x}-{hi:04x}: tok {m.sum()} main M {hm[m].sum()} skM {hs[m].sum()}')
    for j in o:
        if dsk[j]<=0: break
        print(f'   dSk {dsk[j]:+4d} dM {dm[j]:+4d} dM_out {dout[j]:+5d} {nb[j]:6d}B {names[j]}')
        rows.append((n,int(dsk[j]),int(dm[j]),int(dout[j]),int(nb[j]),names[j]))
import json; json.dump(rows,open(a[0]+'.regtab.json','w'))
