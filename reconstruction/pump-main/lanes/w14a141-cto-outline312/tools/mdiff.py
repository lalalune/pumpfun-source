#!/usr/bin/env python3
"""mdiff.py a.bin b.bin [lo hi]: orig instruction offsets matched by a but not b (and vice versa) in orig [lo,hi), with orig disasm."""
import sys,os,difflib
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'prov'))
import dis as D
exec(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'prov','chunk.py')).read().split('o=D.orig()')[0].split('import dis as D')[1])
o=D.orig(); oo=[]; i=0
while i<len(o): oo.append(i); i+=16 if o[i]==0x18 else 8
def mset(c):
    sm=difflib.SequenceMatcher(None,mask(o),mask(c),autojunk=False); s={}
    for m in sm.get_matching_blocks():
        for k in range(m.size): s[oo[m.a+k]]=m.b+k
    return s
a=mset(open(sys.argv[1],'rb').read()); b=mset(open(sys.argv[2],'rb').read())
lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0; hi=int(sys.argv[4],16) if len(sys.argv)>4 else len(o)
L=dict(D.d(o))
for off in oo:
    if lo<=off<hi and ((off in a)!=(off in b)): print('%05x %s %s'%(off,'A' if off in a else 'B',L.get(off,'?')))
