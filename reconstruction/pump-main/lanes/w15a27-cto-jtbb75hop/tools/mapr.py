#!/usr/bin/env python3
"""mapr.py <cand> <lo> <hi>: global true-LCS (rfj); for orig tokens in [lo,hi) print matched cand offset runs, and unmatched orig runs."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
from lcschunk_m import matched_ops
import dis as D
p,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
O=oracle.orig_window(); ot,oo=xled.toks(O)
C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C)
f=mk(1,1,1); ops=matched_ops(f(ot),f(ct)); mp={}
for op,i,j in ops:
    if op=='=': mp[i]=j
runs=[]; cur=None
for i in range(len(ot)):
    if not(lo<=oo[i]<hi): continue
    j=mp.get(i); key=('m',co[j]-oo[i]) if j is not None else ('u',0)
    if cur and cur[0]==key: cur[2]=oo[i]; cur[3]+=1; cur[5]=co[j] if j is not None else cur[5]
    else:
        cur=[key,oo[i],oo[i],1,(co[j] if j is not None else None),(co[j] if j is not None else None)]; runs.append(cur)
for k,a,b,n,c0,c1 in runs:
    if n>=2 or k[0]=='u': print(f"{k[0]} orig {a:05x}-{b:05x} n={n:3d} " + (f"cand {c0:05x}-{c1:05x} d={k[1]:+x}" if k[0]=='m' else ''))
