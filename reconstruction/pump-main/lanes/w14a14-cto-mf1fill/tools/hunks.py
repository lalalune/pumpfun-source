#!/usr/bin/env python3
"""hunks.py <cand.so|.o> [lo hi] : orig-vs-cand diff hunks (masked tokens, score.py-like) with disassembly text, orig offsets lo..hi."""
import sys,os,difflib,subprocess
sys.path.insert(0,os.path.dirname(__file__))
import irre_lib as I
O=I.orig()
c=I.mask(I.elf_fn(sys.argv[1]))
lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 1<<30
od=[l.split(None,1) for l in open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a14-cto-mf1fill/orig.txt')) if l.startswith('0x')]
def offs(T):
    o=[0]
    for t in T: o.append(o[-1]+len(t))
    return o
oo=offs(O); co=offs(c)
cd=sys.argv[4] if len(sys.argv)>4 else None
ctext={}
if cd:
    for l in open(cd):
        p=l.split(None,1)
        if len(p)==2: ctext[int(p[0],16)]=p[1].strip()
otext={int(a,16)-0x22a10:b.strip() for a,b in od}
sm=difflib.SequenceMatcher(None,O,c,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal' or oo[i1]<lo or oo[i1]>hi: continue
    print('%s orig %04x+%d cand %04x+%d'%(op,oo[i1],i2-i1,co[j1],j2-j1))
    for k in range(i1,i2): print('   - %04x %s'%(oo[k],otext.get(oo[k],'?')))
    for k in range(j1,j2): print('   + %04x %s'%(co[k],ctext.get(co[k],'?')))
