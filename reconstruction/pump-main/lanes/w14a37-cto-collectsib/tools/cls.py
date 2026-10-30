#!/usr/bin/env python3
"""cls.py <orig.rel> <cand.rel> lo hi [lo hi ...]: per-region residual classes over difflib-aligned insns
(structural = masked insn differs; reg = registers only; frame = r10 offsets only; both)."""
import sys,re,difflib
def rd(p):
    r=[]
    for l in open(p):
        q=l.split(None,1)
        if len(q)<2: continue
        s=re.sub(r'\s*<[^>]*>','',q[1]).strip(); s='call' if s.startswith('call') else s
        r.append((int(q[0],16),s))
    return r
def mr(s): return re.sub(r'\br[0-9]\b','R',s)
def mf(s): return re.sub(r'r10 - 0x[0-9a-f]+','FP',s)
def mj(s): return re.sub(r'([+-])0x[0-9a-f]+$','J',s) if s.startswith('j') else s
O=rd(sys.argv[1]); C=rd(sys.argv[2]); a=sys.argv[3:]
for i in range(0,len(a),2):
    lo,hi=int(a[i],16),int(a[i+1],16)
    o=[x for x in O if lo<=x[0]<hi]; c=[x for x in C if lo-0x80<=x[0]<hi+0x40]
    sm=difflib.SequenceMatcher(None,[mj(mf(mr(x[1]))) for x in o],[mj(mf(mr(x[1]))) for x in c],autojunk=False)
    k={'same':0,'reg':0,'frame':0,'both':0,'jmp':0,'struct_o':0,'struct_c':0}
    for t,i1,i2,j1,j2 in sm.get_opcodes():
        if t=='equal':
            for p,q in zip(o[i1:i2],c[j1:j2]):
                x,y=p[1],q[1]
                if x==y: k['same']+=1
                elif mj(x)==mj(y): k['jmp']+=1
                elif mf(mj(x))==mf(mj(y)): k['frame']+=1
                elif mr(mj(x))==mr(mj(y)): k['reg']+=1
                else: k['both']+=1
        else: k['struct_o']+=i2-i1; k['struct_c']+=j2-j1
    print('%05x-%05x n=%d'%(lo,hi,len(o)),k)
