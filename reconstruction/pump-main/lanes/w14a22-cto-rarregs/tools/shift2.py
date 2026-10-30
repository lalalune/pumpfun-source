#!/usr/bin/env python3
# shift2.py <orig_fn> <cand_fn>... [BIN env]: median (cand-orig) address offset of aligned insns per orig bin (jumps/frame/regs masked)
import sys,re,difflib,statistics,os
BN=int(os.environ.get('BIN','0x200'),16)
def rd(f):
    A=[];T=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw',s)
        s=re.sub(r'r10 - 0x[0-9a-f]+','F',s); s=re.sub(r'\br[0-9]\b','R',s); s=re.sub(r'[+-]0x[0-9a-f]+$','J',s) if s.startswith('j') else s
        A.append(int(p[0],16)); T.append(s)
    return A,T
oa,ot=rd(sys.argv[1])
for f in sys.argv[2:]:
    ca,ct=rd(f); d={}
    for a,b,s in difflib.SequenceMatcher(None,ot,ct,autojunk=False).get_matching_blocks():
        for i in range(s): d.setdefault(oa[a+i]//BN,[]).append(ca[b+i]-oa[a+i])
    print(f.split('/')[-2],' '.join('%x:%+d'%(k*BN,int(statistics.median(v))) for k,v in sorted(d.items()) if len(v)>8))
