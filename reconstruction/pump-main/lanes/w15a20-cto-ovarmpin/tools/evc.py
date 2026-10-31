#!/usr/bin/env python3
"""evc.py <rx>...: true-LCS rfj matched tokens per orig 0x800 chunk, delta vs main (whole function)."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
from lcschunk_m import matched_ops
O=oracle.orig_window(); ot,oo=xled.toks(O)
def load(p): return xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
f=mk(1,1,1)
def ch(p):
    ct,co=xled.toks(load(p)); ops=matched_ops(f(ot),f(ct)); c={};tot=0
    for op,i,j in ops:
        if op=='=': c[oo[i]//0x800]=c.get(oo[i]//0x800,0)+1; tot+=1
    return c,tot
b,bt=ch('main'); print('main',bt,' '.join(f'{k*0x800:x}:{v}' for k,v in sorted(b.items())))
for p in sys.argv[1:]:
    c,t=ch(p); print(f'{p:20s} {t-bt:+d}',' '.join(f'{k*0x800:x}:{c.get(k,0)-v:+d}' for k,v in sorted(b.items()) if c.get(k,0)!=v),flush=True)
