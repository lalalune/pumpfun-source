#!/usr/bin/env python3
# regcmp.py <orig_fn> <candA_fn> <candB_fn> [bin]: matched orig insns per orig-address bin (A vs B), raw tokens
import sys,re,difflib
def toks(f):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s); out.append(s)
    return out
o=toks(sys.argv[1]); bn=int(sys.argv[4]) if len(sys.argv)>4 else 200
def m(f):
    c=toks(f); hit=[0]*len(o)
    for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,o,c,autojunk=False).get_opcodes():
        if t=='equal':
            for i in range(i1,i2): hit[i]=1
    return hit
A=m(sys.argv[2]); B=m(sys.argv[3])
for k in range(0,len(o),bn):
    a=sum(A[k:k+bn]); b=sum(B[k:k+bn]); print(f'{k*8:#07x} {a:4d} {b:4d} {b-a:+4d}')
print('tot',sum(A),sum(B))
