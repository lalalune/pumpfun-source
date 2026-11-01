#!/usr/bin/env python3
"""mdiff.py <ref> <cand> <lo> <hi> [mask]: orig tokens in [lo,hi) matched (true LCS, mask) by ref but not cand ('-') and by cand not ref ('+'), with orig disasm."""
import sys,os
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a23-cto-s3ovarm/t2'; sys.path.insert(0,T); import oracle,xled
from fact import mk
import disw as D
def matched(A,B):
    n,k=len(A),len(B); L=[[0]*(k+1) for _ in range(n+1)]
    for i in range(n-1,-1,-1):
        Li=L[i]; L1=L[i+1]; x=A[i]
        for j in range(k-1,-1,-1):
            Li[j]=L1[j+1]+1 if x==B[j] else (L1[j] if L1[j]>Li[j+1] else Li[j+1])
    h=[None]*n; i=j=0
    while i<n and j<k:
        if A[i]==B[j] and L[i][j]==L[i+1][j+1]+1: h[i]=j; i+=1; j+=1
        elif L[i+1][j]>=L[i][j+1]: i+=1
        else: j+=1
    return h
a=sys.argv[1:]; ref,cand=a[0],a[1]; lo,hi=int(a[2],16),int(a[3],16); m=a[4] if len(a)>4 else 'rfj'
f=mk(m[0]=='r',m[1]=='f',m[2]=='j'); O=oracle.orig_window(); ot,oo=xled.toks(O); A=f(ot)
od=dict(D.d(O))
def get(p):
    C=xled.load(p if (p=='main' or '.' in p) else f'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a23-cto-s3ovarm/rx/{p}/fn.bin'); ct,co=xled.toks(C)
    return matched(A,f(ct)),co,dict(D.d(C))
hr,cr,dr=get(ref); hc,cc,dc=get(cand)
for i,o in enumerate(oo):
    if not (lo<=o<hi): continue
    r=hr[i] is not None; c=hc[i] is not None
    tag=' ' if r==c else ('-' if r else '+')
    ra=f'{cr[hr[i]]:5x}' if r else '     '; ca=f'{cc[hc[i]]:5x}' if c else '     '
    print(f'{tag} {o:5x} {od.get(o,"?"):40s} ref@{ra} cand@{ca}')
