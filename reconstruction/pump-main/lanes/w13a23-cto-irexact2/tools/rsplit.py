#!/usr/bin/env python3
"""rsplit.py <fn.bin>...: ratio split by original-window thirds (as w13a15 regcon.py) for oracle fn.bin token files."""
import sys,difflib,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ctoracle
O,w=ctoracle.orig_tokens(); cuts=[0,9133,18266,27400]
off=[];p=0
for t in O: off.append(p); p+=len(t)
for f in sys.argv[1:]:
    b=open(f,'rb').read(); C=[];i=0
    while i<len(b): n=16 if b[i]==0x18 else 8; C.append(b[i:i+n]); i+=n
    sm=difflib.SequenceMatcher(None,O,C,autojunk=False); M=[0,0,0]
    for a,_,k in sm.get_matching_blocks():
        for x in range(a,a+k): M[next(r for r in range(3) if off[x]<cuts[r+1])]+=1
    tot=len(O)+len(C); print(f, round(sm.ratio(),5), ' '.join(f'R{r+1}={2*M[r]/tot:.5f}' for r in range(3)))
