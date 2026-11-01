#!/usr/bin/env python3
"""jdiff.py <A fn.bin> <B fn.bin>: original jumps (aligned under the jump-masked LCS) whose displacement matches in A but
not in B, and vice versa. Shows where B's byte moves break or fix jump displacements. Experiment only."""
import sys,os,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import numpy as np
from oracle import mask,orig_window
from bdis import dis
OR=orig_window(); OT=mask(OR); od=dict(dis(OR))
JMP={0x05,0x15,0x1d,0x25,0x2d,0x35,0x3d,0x45,0x4d,0x55,0x5d,0x65,0x6d,0x75,0x7d,0xa5,0xad,0xb5,0xbd,0xc5,0xcd,0xd5,0xdd}
def mj(toks):
    out=[]
    for t in toks:
        if t[0] in JMP: t=t[:2]+b'JJ'+t[4:]
        out.append(t)
    return out
def lcs(A,B):
    v={}; a=np.array([v.setdefault(x,len(v)) for x in A],dtype=np.int32); b=np.array([v.setdefault(x,len(v)) for x in B],dtype=np.int32)
    n,m=len(a),len(b); dp=np.zeros((n+1,m+1),dtype=np.int16)
    for i in range(1,n+1):
        eq=(b==a[i-1]).astype(np.int16); pr=dp[i-1]; dp[i,1:]=np.maximum.accumulate(np.maximum(pr[1:],pr[:-1]+eq))
    i,j=n,m; pairs=[]
    while i>0 and j>0:
        if a[i-1]==b[j-1] and dp[i,j]==dp[i-1,j-1]+1: pairs.append((i-1,j-1)); i-=1; j-=1
        elif dp[i-1,j]>=dp[i,j-1]: i-=1
        else: j-=1
    return pairs[::-1]
oo=[];o=0
for t in OT: oo.append(o); o+=len(t)
def good(fb):
    C=mask(open(fb,'rb').read()); P=lcs(mj(OT),mj(C))
    return {i for i,j in P if OT[i][0] in JMP and OT[i]==C[j]},{i for i,j in P if OT[i][0] in JMP}
ga,aa=good(sys.argv[1]); gb,ab=good(sys.argv[2])
print('A good',len(ga),'of',len(aa),'| B good',len(gb),'of',len(ab))
print('good in A, bad in B:',[(hex(oo[i]),od[oo[i]]) for i in sorted(ga-gb)])
print('good in B, bad in A:',[(hex(oo[i]),od[oo[i]]) for i in sorted(gb-ga)])
