#!/usr/bin/env python3
"""splice.py <front.o> <back.o> addr...: bound = ratio of front's insns up to orig addr + back's insns after (masked metric)."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import oracle
o=oracle.mask(oracle.orig_window())
def load(p): return oracle.mask(oracle.elf_fn(p,oracle.KEEP))
F=load(sys.argv[1]); B=load(sys.argv[2])
def amap(c):
    sm=difflib.SequenceMatcher(None,o,c,autojunk=False); m={}
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): m[a+k]=b+k
    return m
mf=amap(F); mb=amap(B)
# orig insn index -> byte addr
addr=[];x=0
for t in o: addr.append(x); x+=len(t)
print('front',round(difflib.SequenceMatcher(None,o,F,autojunk=False).ratio(),5),'back',round(difflib.SequenceMatcher(None,o,B,autojunk=False).ratio(),5))
for s in sys.argv[3:]:
    A=int(s,16); k=next(i for i,a in enumerate(addr) if a>=A and i in mf and i in mb)
    c=F[:mf[k]]+B[mb[k]:]
    print(s,'splice at orig %x'%addr[k],'ratio',round(difflib.SequenceMatcher(None,o,c,autojunk=False).ratio(),5),'bytes',sum(len(t) for t in c))
