#!/usr/bin/env python3
"""sbs.py <cand.dis> <orig_lo> <orig_hi>: side-by-side orig vs cand aligned (skeleton difflib, regs masked), marks reg diffs."""
import sys,difflib,re
sys.path.insert(0,__import__('os').path.dirname(__file__)); import absratio as A
O=[l.rstrip('\n') for l in open(A.__file__.replace('tools/absratio.py','orig.rel')) if len(l.split(None,1))>1]
C=[l.rstrip('\n') for l in open(sys.argv[1]) if len(l.split(None,1))>1]
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
on=[A.norm(l.split(None,1)[1],True) for l in O]; cn=[A.norm(l.split(None,1)[1],True) for l in C]
sm=difflib.SequenceMatcher(None,on,cn,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    n=max(i2-i1,j2-j1)
    for k in range(n):
        o=O[i1+k] if i1+k<i2 else ''; c=C[j1+k] if j1+k<j2 else ''
        oa=int(o.split()[0],16) if o else None
        if oa is None:
            # use previous orig addr
            pa=int(O[i1-1].split()[0],16) if i1>0 else 0
            if not(lo<=pa<hi): continue
        elif not(lo<=oa<hi): continue
        ot=re.sub(r'\s+<[^>]*>','',o.split(None,1)[1]) if o else ''; ct=re.sub(r'\s+<[^>]*>','',c.split(None,1)[1].strip()) if c else ''
        mark=' ' if tag=='equal' and A.norm(ot,False)==A.norm(ct,False) else ('R' if tag=='equal' else tag[0].upper())
        print(f"{mark} {o.split()[0] if o else '    '} {ot:40s}| {c.split()[0] if c else '    '} {ct}")
