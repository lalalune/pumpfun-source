#!/usr/bin/env python3
"""mdiff.py <a.o|.so> <b.o|.so> : matched-original-instruction count M for each, and per 0x400 orig-bin delta."""
import sys,os,difflib,collections
sys.path.insert(0,os.path.dirname(__file__))
import irre_lib as I
O=I.orig()
def M(path):
    c=I.mask(I.elf_fn(path))
    sm=difflib.SequenceMatcher(None,O,c,autojunk=False)
    bins=collections.Counter(); m=0
    for a,b,n in sm.get_matching_blocks():
        for k in range(n):
            off=sum(len(t) for t in O[:a+k]) if False else None
        m+=n
        # orig byte offset of token index
    offs=[0]
    for t in O: offs.append(offs[-1]+len(t))
    for a,b,n in sm.get_matching_blocks():
        for k in range(a,a+n): bins[offs[k]//0x400]+=1
    return m,len(c),bins
ma,na,ba=M(sys.argv[1]); mb,nb,bb=M(sys.argv[2])
print('M',ma,mb,mb-ma,'n',na,nb)
for k in sorted(set(ba)|set(bb)):
    d=bb[k]-ba[k]
    if d: print(hex(k*0x400),ba[k],bb[k],d)
