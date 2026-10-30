#!/usr/bin/env python3
"""errline.py <m.o>..: error sites as (offset:line) for orig and cands (stw [..],code ; stw [..-0x2b8],line)."""
import sys,os,re
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
def seq(d):
    r=[]
    for o,t in d:
        m=re.match(r'stw \[r10 - 0x[0-9a-f]+\], 0x([0-9a-f]+)$',t)
        if m:
            v=int(m.group(1),16)
            if 200<=v<=900: r.append('%x:%d'%(o,v))
    return r
print('orig',' '.join(seq(orig_dis())))
for p in sys.argv[1:]: print(p.split('/')[-2],' '.join(seq(cand_dis(p))))
