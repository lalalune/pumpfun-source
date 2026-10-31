#!/usr/bin/env python3
"""lcsalign.py <cand> <orig_lo> <orig_hi> <cand_lo> <cand_hi> [mask rfj] [minrun 3]: true-LCS traceback; prints unmatched runs
(orig-only '-' / cand-only '+') of length >= minrun with addresses and first ops."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
import dis as D
a=sys.argv[1:]; p=a[0]; lo,hi,clo,chi=[int(x,16) for x in a[1:5]]; m=a[5] if len(a)>5 else 'rfj'; mn=int(a[6]) if len(a)>6 else 3
O=oracle.orig_window(); ot,oo=xled.toks(O)
C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C)
f=mk(m[0]=='r',m[1]=='f',m[2]=='j')
IA=[i for i,o in enumerate(oo) if lo<=o<hi]; IB=[i for i,o in enumerate(co) if clo<=o<chi]
A=f([ot[i] for i in IA]); B=f([ct[i] for i in IB]); n,k=len(A),len(B)
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
print(f'LCS {L[0][0]} of orig {n} / cand {k} ({m})')
run=[]
def flush():
    if len(run)>=mn:
        s=run[0][0]
        addrs=[(oo[IA[x]] if s=='-' else co[IB[x]]) for _,x in run]
        print(f"{s} {len(run):3d}  {addrs[0]:05x}-{addrs[-1]:05x}  "+' ; '.join((dO if s=='-' else dC).get(ad,'?') for ad in addrs[:4]))
for op in ops:
    if op[0]=='=': flush(); run=[]; continue
    x=op[1] if op[0]=='-' else op[2]
    if run and run[0][0]!=op[0]: flush(); run=[]
    run.append((op[0],x))
flush()
