#!/usr/bin/env python3
"""polmap.py <fn.bin>: map of `?`-test polarity sites (experiment only). Lists every `jeq rX,K,+1; ja T` pair in the
candidate and the instruction the original has at the aligned position (opcode-class true-LCS alignment, so jeq and jne
can align). A site where ours has `jeq ..,+1; ja` and the original one `jne` is a -8 B polarity fix (w16a07 A6 at line
660, sh_iflet after the sharing CPI); on main 9bd38c7 those are the only two."""
import sys,os,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import numpy as np
from oracle import mask,orig_window
from bdis import dis
OR=orig_window(); C=open(sys.argv[1],'rb').read(); OT=mask(OR); CT=mask(C)
def opab(t): return (t[0]&0x0f, t[0]>>4 if (t[0]&7) not in (5,6) else 'J')
def lcs(A,B):
    v={}; a=np.array([v.setdefault(x,len(v)) for x in A],dtype=np.int32); b=np.array([v.setdefault(x,len(v)) for x in B],dtype=np.int32)
    n,m=len(a),len(b); dp=np.zeros((n+1,m+1),dtype=np.int16)
    for i in range(1,n+1):
        eq=(b==a[i-1]).astype(np.int16); pr=dp[i-1]; dp[i,1:]=np.maximum.accumulate(np.maximum(pr[1:],pr[:-1]+eq))
    i,j=n,m; P=[]
    while i>0 and j>0:
        if a[i-1]==b[j-1] and dp[i,j]==dp[i-1,j-1]+1: P.append((i-1,j-1)); i-=1; j-=1
        elif dp[i-1,j]>=dp[i,j-1]: i-=1
        else: j-=1
    return P[::-1]
c2o={j:i for i,j in lcs([opab(t) for t in OT],[opab(t) for t in CT])}
od=dis(OR); cd=dis(C); n=0
for j in range(len(CT)-1):
    t,u=CT[j],CT[j+1]
    if t[0]==0x15 and struct.unpack_from('<h',t,2)[0]==1 and u[0]==0x05:
        i=c2o.get(j); ot=od[i][1] if i is not None else '(unaligned)'; ot2=od[i+1][1] if i is not None and i+1<len(od) else ''
        flag='  <- original single jne' if ot.startswith('jne') or i is None else ''
        print(f'ours {cd[j][0]:#06x} {cd[j][1]:24s}; {cd[j+1][1]:12s} | orig {od[i][0] if i is not None else 0:#06x} {ot:26s} {ot2:18s}{flag}'); n+=1
print(n,'jeq+1/ja sites')
