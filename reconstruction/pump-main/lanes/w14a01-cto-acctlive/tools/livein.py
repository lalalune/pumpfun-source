#!/usr/bin/env python3
"""livein.py <dis> <start> <end>: registers read in [start,end) before any write (straight-line approx), with first-read offsets."""
import sys,re
f,a,b=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
w=set(); li={}
for l in open(f):
    p=l.split(None,1); x=int(p[0],16)
    if not a<=x<b: continue
    ins=p[1].strip(); op=ins.split()[0]
    regs=re.findall(r'\br(\d+)\b',ins)
    if op=='call': continue
    if op.startswith('st'):
        reads=regs; writes=[]
    elif op.startswith('j'):
        reads=regs; writes=[]
    elif op in ('mov64','mov32','lddw') or op.startswith('ldx'):
        writes=regs[:1]; reads=regs[1:]
    else:
        writes=regs[:1]; reads=regs
    for r in reads:
        if r!='10' and r not in w and r not in li: li[r]=hex(x)
    for r in writes: w.add(r)
print(' '.join(f'r{k}@{v}' for k,v in sorted(li.items(),key=lambda t:int(t[0]))))
