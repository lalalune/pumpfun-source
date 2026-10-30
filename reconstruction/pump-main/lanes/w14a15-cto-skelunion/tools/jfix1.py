#!/usr/bin/env python3
"""jfix1.py name addr,addr..|each: fix only the given orig jump addrs (or each lost-vs-main jump singly) and report ratio."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
from jdiag import toks,jm,ot,O
o=oracle.mask(oracle.orig_window())
n=sys.argv[1]; raw=open(f'{O}/rx/{n}/fn.bin','rb').read(); ct=toks(raw)
A=[jm(x)[0] for _,x in ot]; B=[jm(x)[0] for _,x in ct]; pos={}
for a,b,s in difflib.SequenceMatcher(None,A,B,autojunk=False).get_matching_blocks():
    for k in range(s):
        (oa,ox),(ca,cx)=ot[a+k],ct[b+k]
        if jm(ox)[1] and ox[2:4]!=cx[2:4]: pos[oa]=(ca,ox[2:4])
def r(addrs):
    f=bytearray(raw)
    for a in addrs: ca,v=pos[a]; f[ca+2:ca+4]=v
    return round(difflib.SequenceMatcher(None,o,oracle.mask(bytes(f)),autojunk=False).ratio(),5)
print('base',r([]),'all',r(list(pos)),'nbad',len(pos))
if sys.argv[2]=='each':
    res=sorted(((r([a]),a) for a in pos),reverse=True)
    for v,a in res[:25]: print(f'{a:#06x} {v}')
else: print(r([int(x,16) for x in sys.argv[2].split(',')]))
