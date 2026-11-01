#!/usr/bin/env python3
"""evc3.py <rx>...: true-LCS matched tokens per orig 0x800 chunk under '---' and 'rfj', deltas vs main (whole function DP)."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
from lcschunk_m import matched_ops
O=oracle.orig_window(); ot,oo=xled.toks(O)
def load(p): return xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
def ch(p,m):
    f=mk(m[0]=='r',m[1]=='f',m[2]=='j'); ct,co=xled.toks(load(p)); ops=matched_ops(f(ot),f(ct)); c={};tot=0
    for op,i,j in ops:
        if op=='=': c[oo[i]//0x800]=c.get(oo[i]//0x800,0)+1; tot+=1
    return c,tot
for m in ('---','rfj'):
    b,bt=ch('main',m); print(m,'main',bt,' '.join(f'{k*0x800:x}:{v}' for k,v in sorted(b.items())),flush=True)
    for p in sys.argv[1:]:
        c,t=ch(p,m); print(m,f'{p:14s} {t-bt:+d}',' '.join(f'{k*0x800:x}:{c.get(k,0)-v:+d}' for k,v in sorted(b.items())),flush=True)
