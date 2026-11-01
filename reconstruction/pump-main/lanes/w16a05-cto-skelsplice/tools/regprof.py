#!/usr/bin/env python3
"""regprof.py <build>... [--ref main|<build>] [--skel]: per-region matched orig tokens (M; with --skel also skeleton) vs ref."""
import sys,os,difflib
import numpy as np
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
from regs import R
LANES=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
O=oracle.orig_window(); OT,OO=xled.toks(O); OF=xled.fmask(OT); N=len(OT); OO=np.array(OO)
def path(p):
    if p=='main' or os.path.exists(p): return p
    q=os.path.join(LANES,p)
    if os.path.exists(q): return q
    a,b=p.split('/',1); return os.path.join(LANES,a,'rx',b,'fn.bin')
def hits(p,skel=False):
    C=xled.load(path(p)); ct,_=xled.toks(C)
    a,b=(OF,xled.fmask(ct)) if skel else (OT,ct)
    h=np.zeros(N,bool)
    for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks(): h[bl.a:bl.a+bl.size]=True
    return h,len(C)
if __name__=='__main__':
    a=sys.argv[1:]; ref='main'; sk='--skel' in a; a=[x for x in a if x!='--skel']
    if '--ref' in a: i=a.index('--ref'); ref=a[i+1]; del a[i:i+2]
    hr,br=hits(ref); hrs=hits(ref,True)[0] if sk else None
    rid=np.zeros(N,int)
    for k,(lo,hi,n) in enumerate(R): rid[(OO>=lo)&(OO<hi)]=k
    for p in a:
        h,b=hits(p); hs=hits(p,True)[0] if sk else None
        print(f'== {p}  M {h.sum()} ({h.sum()-hr.sum():+d})  bytes {b}'+(f'  skM {hs.sum()} ({hs.sum()-hrs.sum():+d})' if sk else ''))
        for k,(lo,hi,n) in enumerate(R):
            m=rid==k
            s=f'  {n:13s} {lo:04x}-{hi:04x} tok {m.sum():4d}  ref {hr[m].sum():4d}  dM {h[m].sum()-hr[m].sum():+4d}'
            if sk: s+=f'   ref_sk {hrs[m].sum():4d} dSk {hs[m].sum()-hrs[m].sum():+4d}'
            print(s)
