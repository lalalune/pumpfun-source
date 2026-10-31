#!/usr/bin/env python3
"""ch.py <ref> <cand...>: per-orig-0x800-chunk M and rfjM, delta vs ref"""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled,fr
O=oracle.orig_window(); ot=oracle.mask(O)
def prof(p,mf):
    q=p if '.' in p else f'{T}/../rx/{p}/fn.bin'; c=mf(oracle.mask(xled.load(q))); o=mf(ot)
    off=[0]
    for x in o: off.append(off[-1]+len(x))
    ch={}
    for b in difflib.SequenceMatcher(None,o,c,autojunk=False).get_matching_blocks():
        for i in range(b.a,b.a+b.size): k=off[i]//0x800; ch[k]=ch.get(k,0)+1
    return ch
R=lambda t: fr.jm(fr.rm(fr.fm(t)))
ref=sys.argv[1]; a=prof(ref,lambda t:t); ar=prof(ref,R)
for p in sys.argv[2:]:
    b=prof(p,lambda t:t); br=prof(p,R)
    print(p, 'M:', ' '.join(f'{k:x}:{b.get(k,0)-a.get(k,0):+d}' for k in sorted(set(a)|set(b)) if b.get(k,0)!=a.get(k,0)))
    print(p, 'rfjM:', ' '.join(f'{k:x}:{br.get(k,0)-ar.get(k,0):+d}' for k in sorted(set(ar)|set(br)) if br.get(k,0)!=ar.get(k,0)))
