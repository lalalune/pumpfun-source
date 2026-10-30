#!/usr/bin/env python3
"""regperm.py <fn.bin> lo hi: over abs+reg aligned pairs with orig offset in [lo,hi), count orig->cand register pairs (dst,src)."""
import sys, difflib, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctoracle
from regdiff import toks, regmask
otok,w=ctoracle.orig_tokens(); offs=[];o=0
for t in otok: offs.append(o); o+=len(t)
ct=toks(Path(sys.argv[1]).read_bytes()); lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
sm=difflib.SequenceMatcher(None,[regmask(t) for t in otok],[regmask(t) for t in ct],autojunk=False)
c=collections.Counter()
for a,b,s in sm.get_matching_blocks():
    for k in range(s):
        if lo<=offs[a+k]<hi:
            x,y=otok[a+k],ct[b+k]
            if x[0]==0x85: continue
            c[('d',x[1]&15,y[1]&15)]+=1
            if (x[0]&7) in (1,3) or (x[0]&8): c[('s',x[1]>>4,y[1]>>4)]+=1
m=collections.defaultdict(collections.Counter)
for (k,a,b),n in c.items():
    if a!=10: m[a][b]+=n
for a in sorted(m): print(f'orig r{a} ->', ' '.join(f'r{b}:{n}' for b,n in m[a].most_common(5)))
