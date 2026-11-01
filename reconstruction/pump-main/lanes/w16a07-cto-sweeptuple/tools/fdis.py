#!/usr/bin/env python3
"""dis.py <fn.bin> [lo hi]: relative-offset listing of a fn.bin."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import bdis
b=open(sys.argv[1],'rb').read(); lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 1<<30
for o,t in bdis.dis(b):
    if lo<=o<hi: print(f'{o:04x}  {t}')
