#!/usr/bin/env python3
"""regcon.py <unstripped.so>... : admin_cto target_metric ratio split by ORIGINAL-window thirds.
For each region r (orig byte ranges [0,9133),[9133,18266),[18266,27400)): M_r = difflib-matched tokens whose
original index lies in r; share = 2*M_r/(|O|+|C|) (shares sum to the ratio); loc = M_r/|O_r|."""
import sys,difflib,re
import os
H=os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../../../harness')
sys.path.insert(0,H)
from score import original_windows
from win import Cand, insns, demangle, ORIG_SECS
w={x['start']:x for x in original_windows()}[0x22a10]
O=insns(w['raw'],0x22a10,ORIG_SECS); otok=[x[2] for x in O]; ooff=[x[0]-0x22a10 if x[0]>=0x22a10 else x[0] for x in O]
cuts=[0,9133,18266,27400]
reg=[sum(1 for o in ooff if cuts[i]<=o<cuts[i+1]) for i in range(3)]
pat=re.compile(r'admin_cto::execute$')
FR='--frame' in sys.argv; RG='--regs' in sys.argv; JM='--jumps' in sys.argv
def mk(t):
    t=bytearray(t)
    if FR and ((t[1]&15)==10 or (t[1]>>4)==10): t[2]=t[3]=0
    if FR and t[0]==0x07 and t[4]>=0x80 and t[7]==0xff: t[4:8]=b'\0\0\0\0'
    if RG: t[1]=0
    if JM and 0x05<=t[0]<=0xde and (t[0]&7)==5: t[2]=t[3]=0
    return bytes(t)
otok=[mk(t) for t in otok]
for p in [a for a in sys.argv[1:] if not a.startswith('--')]:
    c=Cand(p); s,n,nm=[(s,n,nm) for s,n,nm in c.funcs if pat.search(demangle(nm))][0]
    ctok=[mk(x[2]) for x in insns(c.fn(s,n),s,c.secs)]
    sm=difflib.SequenceMatcher(None,otok,ctok,autojunk=False)
    M=[0,0,0]
    for a,b,k in sm.get_matching_blocks():
        for i in range(a,a+k):
            o=ooff[i]
            for r in range(3):
                if cuts[r]<=o<cuts[r+1]: M[r]+=1
    T=len(otok)+len(ctok)
    print(f'{p.split("/")[-2][:24]:24s} {n:6d} ratio {2*sum(M)/T:.5f} | '+' | '.join(f'R{r+1} M {M[r]:4d}/{reg[r]} share {2*M[r]/T:.5f}' for r in range(3)))
