#!/usr/bin/env python3
"""sbs.py <cand> olo ohi clo chi [mask]: side-by-side true-LCS traceback, full listing."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
import dis as D
a=sys.argv[1:]; p=a[0]; lo,hi,clo,chi=[int(x,16) for x in a[1:5]]; m=a[5] if len(a)>5 else 'rfj'
O=oracle.orig_window(); ot,oo=xled.toks(O)
C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C)
f=mk(m[0]=='r',m[1]=='f',m[2]=='j')
IA=[i for i,o in enumerate(oo) if lo<=o<hi]; IB=[i for i,o in enumerate(co) if clo<=o<chi]
A=f([ot[i] for i in IA]); B=f([ct[i] for i in IB]); n,k=len(A),len(B)
A2=[ot[i] for i in IA]; B2=[ct[i] for i in IB]
L=[[0]*(k+1) for _ in range(n+1)]
for i in range(n-1,-1,-1):
    Li=L[i]; L1=L[i+1]; x=A[i]
    for j in range(k-1,-1,-1):
        Li[j]=L1[j+1]+1 if x==B[j] else (L1[j] if L1[j]>Li[j+1] else Li[j+1])
i=j=0; ops=[]
while i<n and j<k:
    if A[i]==B[j] and L[i][j]==L[i+1][j+1]+1: ops.append(('=',i,j)); i+=1; j+=1
    elif L[i+1][j]>=L[i][j+1]: ops.append(('-',i,None)); i+=1
    else: ops.append(('+',None,j)); j+=1
ops+= [('-',x,None) for x in range(i,n)]+[('+',None,y) for y in range(j,k)]
dO=dict(D.d(O)); dC=dict(D.d(C))
for op,x,y in ops:
    l=f"{oo[IA[x]]:05x} {dO.get(oo[IA[x]],'?'):34s}" if x is not None else ' '*40
    r=f"{co[IB[y]]:05x} {dC.get(co[IB[y]],'?')}" if y is not None else ''
    s=op if op!='=' else ('=' if A2[x]==B2[y] else '~')
    print(f"{s} {l} | {r}")
