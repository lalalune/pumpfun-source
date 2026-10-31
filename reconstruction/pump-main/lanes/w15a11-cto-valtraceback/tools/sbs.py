#!/usr/bin/env python3
"""sbs.py <cand> <orig_lo> <orig_hi> [mask rfj]: whole-function true-LCS traceback, printed side by side for orig range."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
import dis as D
from lcschunk_m import matched_ops
a=sys.argv[1:]; p=a[0]; lo,hi=int(a[1],16),int(a[2],16); m=a[3] if len(a)>3 else 'rfj'
O=oracle.orig_window(); ot,oo=xled.toks(O)
C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C)
f=mk(m[0]=='r',m[1]=='f',m[2]=='j'); ops=matched_ops(f(ot),f(ct))
dO=dict(D.d(O)); dC=dict(D.d(C)); on=False
for op,i,j in ops:
    if i is not None: on = lo<=oo[i]<hi
    if not on: continue
    L=f'{oo[i]:05x} {dO[oo[i]]}' if i is not None else ''
    R=f'{co[j]:05x} {dC[co[j]]}' if j is not None else ''
    print(f'{op} {L:44s} | {R}')
