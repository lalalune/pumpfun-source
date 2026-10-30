#!/usr/bin/env python3
"""jcmp.py ref name: orig jumps good in ref but bad in name (jm alignment), with orig src/dst addr and name's delta (insns)."""
import sys,os,difflib,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
from jdiag import toks,jm,ot,O
def stat(n):
    ct=toks(open(f'{O}/rx/{n}/fn.bin','rb').read())
    A=[jm(x)[0] for _,x in ot]; B=[jm(x)[0] for _,x in ct]; r={}
    for a,b,s in difflib.SequenceMatcher(None,A,B,autojunk=False).get_matching_blocks():
        for k in range(s):
            (oa,ox),(ca,cx)=ot[a+k],ct[b+k]
            if not jm(ox)[1]: continue
            oo=struct.unpack_from('<h',ox,2)[0]; co=struct.unpack_from('<h',cx,2)[0]
            r[oa]=(oa+8+oo*8, co-oo)
    return r
R,N=stat(sys.argv[1]),stat(sys.argv[2])
lost=[(a,N[a]) for a in R if R[a][1]==0 and a in N and N[a][1]!=0]
won=[(a,N[a]) for a in N if N[a][1]==0 and a in R and R[a][1]!=0]
print('lost',len(lost),'won',len(won))
for a,(d,dl) in sorted(lost): print(f'  lost {a:#06x}->{d:#06x} delta {dl:+d}')
for a,(d,dl) in sorted(won): print(f'  won  {a:#06x}->{d:#06x}')
