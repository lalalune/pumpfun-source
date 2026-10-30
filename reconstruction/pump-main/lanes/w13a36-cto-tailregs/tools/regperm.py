#!/usr/bin/env python3
"""regperm.py <fn.bin> lo hi [seg]: per segment, orig->cand register pair counts over reg-masked-aligned tokens."""
import sys,os,difflib,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../w12a02-cto-iroracle/scripts"))
import tail
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16); seg=int(sys.argv[4],16) if len(sys.argv)>4 else 0x200
OT=tail.OT; OFF=tail.OFF; ct=tail.toks(p)
sm=difflib.SequenceMatcher(None,[tail.regmask(t) for t in OT],[tail.regmask(t) for t in ct],autojunk=False)
S=collections.defaultdict(collections.Counter)
for a,b,s in sm.get_matching_blocks():
    for k in range(s):
        o=OT[a+k]; c=ct[b+k]; off=OFF[a+k]
        if not(lo<=off<hi): continue
        for sh in (0,4):
            ro=(o[1]>>sh)&15; rc=(c[1]>>sh)&15
            if ro==10 or (sh==4 and o[0]==0x85): continue
            if ro!=rc: S[off//seg][(ro,rc)]+=1
for k in sorted(S):
    print(hex(k*seg), ' '.join(f'r{a}->r{b}:{n}' for (a,b),n in S[k].most_common(8)))
