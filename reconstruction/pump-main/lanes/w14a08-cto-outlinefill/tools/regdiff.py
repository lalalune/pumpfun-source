#!/usr/bin/env python3
# regdiff.py <orig_fn> <A_fn> <B_fn> <lo> <hi>: orig instrs in [lo,hi) with match flag in A and B (raw tokens), show where they differ
import sys,re,difflib
def rd(f):
    A=[];T=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s); A.append(p[1].strip()); T.append(s)
    return A,T
oa,o=rd(sys.argv[1])
def m(f):
    ca,c=rd(f); mp={}
    for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,o,c,autojunk=False).get_opcodes():
        if t=='equal':
            for k in range(i2-i1): mp[i1+k]=ca[j1+k]
        elif t=='replace' and i2-i1==j2-j1:
            for k in range(i2-i1): mp[i1+k]='~'+ca[j1+k]
    return mp
A=m(sys.argv[2]); B=m(sys.argv[3]); lo,hi=int(sys.argv[4],16)//8,int(sys.argv[5],16)//8
for i in range(lo,hi):
    a=i in A and not A[i].startswith('~'); b=i in B and not B[i].startswith('~')
    if a!=b: print(f'{i*8:#06x} {"A" if a else "-"}{"B" if b else "-"} {oa[i]:36s} | B: {B.get(i,"")}')
