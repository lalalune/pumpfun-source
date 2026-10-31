#!/usr/bin/env python3
"""lcschunk.py <ref> <cand>... [--mask rfj] [--sz 0x800]: true-LCS (DP traceback) matched orig tokens per orig chunk, cand minus ref."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
def matched(A,B):
    n,k=len(A),len(B); L=[[0]*(k+1) for _ in range(n+1)]
    for i in range(n-1,-1,-1):
        Li=L[i]; L1=L[i+1]; x=A[i]
        for j in range(k-1,-1,-1):
            Li[j]=L1[j+1]+1 if x==B[j] else (L1[j] if L1[j]>Li[j+1] else Li[j+1])
    h=[0]*n; i=j=0
    while i<n and j<k:
        if A[i]==B[j] and L[i][j]==L[i+1][j+1]+1: h[i]=1; i+=1; j+=1
        elif L[i+1][j]>=L[i][j+1]: i+=1
        else: j+=1
    return h
a=sys.argv[1:]; m='rfj'; sz=0x800
if '--mask' in a: i=a.index('--mask'); m=a[i+1]; del a[i:i+2]
if '--sz' in a: i=a.index('--sz'); sz=int(a[i+1],16); del a[i:i+2]
f=mk(m[0]=='r',m[1]=='f',m[2]=='j'); O=oracle.orig_window(); ot,oo=xled.toks(O); A=f(ot)
def per(p):
    C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,_=xled.toks(C); h=matched(A,f(ct)); d={}
    for x,o in zip(h,oo): d[o//sz]=d.get(o//sz,0)+x
    return d,sum(h)
r,rt=per(a[0]); print('ref',a[0],rt,' '.join(f'{c*sz:x}:{r[c]}' for c in sorted(r)))
for p in a[1:]:
    d,t=per(p); print(os.path.basename(os.path.dirname(p)) if '/' in p else p, t, ' '.join(f'{c*sz:x}:{d[c]-r[c]:+d}' for c in sorted(r) if d[c]-r[c]))
