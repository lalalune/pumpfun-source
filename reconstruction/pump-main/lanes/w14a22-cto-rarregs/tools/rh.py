#!/usr/bin/env python3
# rh.py <orig> <A> <B> [bin]: per orig bin, count of aligned (reg-masked) insns whose raw differs only in registers, A vs B; plus B-only hunks list with VERBOSE=1
import sys,re,difflib,os
BN=int(sys.argv[4],16) if len(sys.argv)>4 else 0x400
def rd(f):
    R=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s); R.append((int(p[0],16),s))
    return R
def rm(s): return re.sub(r'\br[0-9]\b','R',s)
o=rd(sys.argv[1])
def m(f):
    c=rd(f); out={}
    for a,b,s in difflib.SequenceMatcher(None,[rm(x) for _,x in o],[rm(x) for _,x in c],autojunk=False).get_matching_blocks():
        for i in range(s):
            if o[a+i][1]!=c[b+i][1]: out[o[a+i][0]]=(c[b+i][0],c[b+i][1])
    return out
A=m(sys.argv[2]); B=m(sys.argv[3])
bins=sorted(set(k//BN for k in list(A)+list(B)))
for k in bins:
    a=sum(1 for x in A if x//BN==k); b=sum(1 for x in B if x//BN==k)
    if a!=b: print(f'{k*BN:#07x} A {a:3d} B {b:3d} {b-a:+d}')
print('total',len(A),len(B))
if os.environ.get('VERBOSE'):
    od=dict(o)
    for x in sorted(set(B)-set(A)): print(f'B-only {x:#06x} orig {od[x]:34s} B {B[x][1]}')
