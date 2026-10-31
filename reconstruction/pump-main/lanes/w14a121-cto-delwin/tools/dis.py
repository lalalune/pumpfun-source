#!/usr/bin/env python3
"""dis.py fn.bin lo hi : print instructions (offsets relative to fn start)"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bdis import decode
raw=open(sys.argv[1],'rb').read(); lo=int(sys.argv[2],0); hi=int(sys.argv[3],0)
for d in decode(raw):
    if lo<=d['off']<hi: print('%05x  %s'%(d['off'],d['txt']))
