#!/usr/bin/env python3
"""candlist.py <win.py --full diff> : print candidate listing as '<off hex> insn' (off relative to 0x22a10)"""
import sys,re
for l in open(sys.argv[1]):
    l=l.rstrip('\n')
    if not l or l[0] not in ' +-' or len(l)<20: continue
    t=l[0]; r=l[1:].split()
    if not r or not r[0].startswith('0x'): continue
    if t=='+': c=r[0]; ins=' '.join(r[1:])
    elif t==' ' and len(r)>1 and r[1].startswith('0x'): c=r[1]; ins=' '.join(r[2:])
    else: continue
    print('%05x %s'%(int(c,16)-0x22a10,ins))
