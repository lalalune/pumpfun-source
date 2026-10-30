#!/usr/bin/env python3
"""fm.py <so>...: plain and frame-masked (r10 offsets masked) token ratios of admin_cto vs the original."""
import sys,re,difflib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a46-cto-scugap/tools')
from census import O, cand_tok
def m(t):
    t=bytes(t); 
    if len(t)<8: return t
    cls=t[0]&7; dst=t[1]&15; src=t[1]>>4
    if (cls in (2,3) and dst==10) or (cls==1 and src==10): return t[:2]+b'FF'+t[4:]
    return t
OM=[m(x[2]) for x in O]
for p in sys.argv[1:]:
    ct,_,_=cand_tok(p)
    a=difflib.SequenceMatcher(None,[x[2] for x in O],[x[2] for x in ct],autojunk=False).ratio()
    b=difflib.SequenceMatcher(None,OM,[m(x[2]) for x in ct],autojunk=False).ratio()
    print(round(a,5),round(b,5),len(ct),p.split('/')[-2])
