#!/usr/bin/env python3
"""outl.py orig|<so> lo hi: condensed outline (jumps/calls/exit/error code+line imm) of a window range."""
import sys,os,re
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
d=orig_dis() if p=='orig' else cand_dis(p)
tgt=set()
for o,t in d:
    m=re.match(r'^j\w+ .*?([+-])(0x[0-9a-f]+|\d+)$',t)
    if m: tgt.add(o+8+(1 if m.group(1)=='+' else -1)*int(m.group(2),0)*8)
for o,t in d:
    if not lo<=o<hi: continue
    show=False
    if t.startswith(('j','call','exit')): show=True
    m=re.search(r', 0x([0-9a-f]+)$',t)
    if m and t.startswith(('st','mov')):
        v=int(m.group(1),16)
        if 0x1700<=v<=0x1900 or 0xf0<=v<=0x2c0: show=True
    if 'lddw' in t: show=True
    if o in tgt: print('%5x: ----'%o)
    if show:
        m=re.match(r'^(j\w+ .*?)([+-])(0x[0-9a-f]+|\d+)$',t)
        if m: t=m.group(1)+'->%x'%(o+8+(1 if m.group(2)=='+' else -1)*int(m.group(3),0)*8)
        print('%5x  %s'%(o,t))
