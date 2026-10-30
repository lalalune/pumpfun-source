#!/usr/bin/env python3
"""gaps.py <cand.o|.so>: list unmatched orig/cand hunks (score tokens), largest first, with orig offsets."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
import irre_lib as I
O=I.orig(); C=I.mask(I.elf_fn(sys.argv[1]))
oo=[0]
for t in O: oo.append(oo[-1]+len(t))
co=[0]
for t in C: co.append(co[-1]+len(t))
sm=difflib.SequenceMatcher(None,O,C,autojunk=False)
h=[]
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal': h.append((max(i2-i1,j2-j1),tag,oo[i1],i2-i1,co[j1],j2-j1))
h.sort(reverse=True)
print('M',sum(x[2] for x in sm.get_matching_blocks()),'unmatched orig',sum(x[3] for x in h))
for x in h[:int(sys.argv[2]) if len(sys.argv)>2 else 40]: print('%-8s orig %05x +%d  cand %05x +%d'%(x[1],x[2],x[3],x[4],x[5]))
