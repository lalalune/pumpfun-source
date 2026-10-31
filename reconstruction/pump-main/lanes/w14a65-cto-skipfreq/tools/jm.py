#!/usr/bin/env python3
"""jm.py <a.dis>..: jump-offset-masked ratio vs orig (frame offsets and registers kept; call/lddw imms masked).
Estimates a candidate's plain ratio if its size matched (jump displacements are the size-sensitive part)."""
import sys,re,difflib,os
T=os.path.dirname(os.path.abspath(__file__))
def norm(s):
    s=re.sub(r'\s*<[^>]*>','',s).strip()
    if s.startswith('call'): return 'call'
    if s.startswith('lddw'): return re.sub(r'0x[0-9a-f]+','IMM',s)
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$','J',s)
    return s
def rd(p):
    r=[]
    for l in open(p):
        q=l.split(None,1)
        if len(q)==2: r.append(norm(q[1]))
    return r
O=rd(T+'/../or.dis')
for p in sys.argv[1:]:
    C=rd(p); print(p,'J=%.5f'%difflib.SequenceMatcher(None,O,C,autojunk=False).ratio(),len(C))
