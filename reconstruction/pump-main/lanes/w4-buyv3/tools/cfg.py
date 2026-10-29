#!/usr/bin/env python3
"""cfg.py raw.ll: print blocks in IR order with successors (terminator order) and RPO simulation."""
import sys,re
L=open(sys.argv[1]).read().split('\n')
blocks=[];succ={};cur=None;term=[]
for l in L[1:]:
    m=re.match(r'^([A-Za-z0-9_.$"]+):',l)
    if m: cur=m.group(1); blocks.append(cur); succ[cur]=[]; continue
    if cur is None: 
        if l.strip(): cur='start'; blocks.append(cur); succ[cur]=[]
        else: continue
    s=l.strip()
    if s.startswith(('br ','switch')) or re.match(r'i64 \d+, label',s) or s.startswith(']'):
        labs=re.findall(r'label %([A-Za-z0-9_.$"]+)',s)
        if s.startswith('switch'):  # default first in IR text; keep default last
            succ[cur].append(('D',labs[0]))
        else:
            for x in labs: succ[cur].append(('',x))
for b in blocks:
    ss=[x for t,x in succ[b] if t=='']+[x for t,x in succ[b] if t=='D']
    succ[b]=ss
if '--print' in sys.argv:
    for b in blocks: print(b,succ[b])
