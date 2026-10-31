#!/usr/bin/env python3
"""lcs.py <cand>... [--lo 0x0 --hi 0x7000] [--masks ---,--j,-fj,rfj]: TRUE LCS (DP, not difflib greedy) of masked tokens,
orig range [lo,hi) vs the whole candidate (or --clo/--chi). difflib's greedy longest-block alignment flips on tiny
changes (e.g. ev_cb_local's +62 rfj in 0x3c00-0x4800 is such a flip: true LCS is equal)."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
def lcs(A,B):
    """bit-parallel LCS length (Hyyro 2004); exact."""
    k=len(B); full=(1<<k)-1; M={}
    for j,y in enumerate(B): M[y]=M.get(y,0)|(1<<j)
    V=full
    for x in A:
        m=M.get(x)
        if m is None: continue
        U=V&m; V=((V+U)|(V-U))&full
    return k-bin(V).count('1')
def lcs_dp(A,B):
    prev=[0]*(len(B)+1)
    for x in A:
        cur=[0]*(len(B)+1)
        for j,y in enumerate(B):
            cur[j+1]=prev[j]+1 if x==y else (prev[j+1] if prev[j+1]>cur[j] else cur[j])
        prev=cur
    return prev[-1]
if __name__=='__main__':
    a=sys.argv[1:]; lo,hi,clo,chi=0,1<<20,None,None; ms='---,--j,-fj,rfj'
    for k in ('--lo','--hi','--clo','--chi','--masks'):
        if k in a:
            i=a.index(k); v=a[i+1]; del a[i:i+2]
            if k=='--masks': ms=v
            else: globals()[k[2:]]=int(v,16)
    if clo is None: clo,chi=0,1<<20
    O=oracle.orig_window(); ot,oo=xled.toks(O)
    A0=[t for t,o in zip(ot,oo) if lo<=o<hi]
    for p in a:
        C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C)
        B0=[t for t,o in zip(ct,co) if clo<=o<chi]; row=[]
        for m in ms.split(','):
            f=mk(m[0]=='r',m[1]=='f',m[2]=='j'); row.append(f'{m}:{lcs(f(A0),f(B0))}')
        print(p,len(C),' '.join(row),flush=True)
