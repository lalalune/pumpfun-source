#!/usr/bin/env python3
"""jx.py name..: jumps aligned (jump-masked) to orig but with wrong offset, bucketed by (src region -> dst region) of orig (0x800)."""
import sys,os,difflib,collections,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
from jm import jm
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
orw=oracle.orig_window(); o=jm(orw); ot=oracle.mask(orw)
def offs(toks):
    r=[];x=0
    for t in toks: r.append(x); x+=len(t)
    return r
oo=offs(ot)
for n in sys.argv[1:]:
    raw=open(f'{O}/rx/{n}/fn.bin','rb').read(); c=jm(raw); ct=oracle.mask(raw)
    sm=difflib.SequenceMatcher(None,o,c,autojunk=False); bad=collections.Counter(); good=0
    for a,b,s in sm.get_matching_blocks():
        for k in range(s):
            x=ot[a+k]; y=ct[b+k]; op=x[0]
            if (op&7) in (5,6) and op not in (0x85,0x95):
                if x==y: good+=1
                else:
                    off=struct.unpack_from('<h',x,2)[0]; src=oo[a+k]; dst=src+8+off*8
                    bad[(src//0x800*0x800,dst//0x800*0x800)]+=1
    print(n,'good',good,'bad',sum(bad.values()))
    print('  ',' '.join(f'{s:x}>{d:x}:{v}' for (s,d),v in sorted(bad.items(),key=lambda t:-t[1])[:24]))
