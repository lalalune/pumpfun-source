#!/usr/bin/env python3
"""deadld.py fn.bin...: frame reloads (ldxdw rX,[r10-o]) whose register is overwritten before any read, within
straight-line code (stops at jumps/calls/exit). Experiment only."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bdis import decode
for f in sys.argv[1:]:
    I=decode(open(f,'rb').read()); out=[]
    for i,d in enumerate(I):
        if not d['txt'].startswith('ldxdw') or '[r10' not in d['txt']: continue
        r=list(d['writes'])[0]
        for e in I[i+1:i+40]:
            t=e['txt'].split()[0]
            if r in e['reads']: break
            if t.startswith('j') or t in ('call','exit'): break
            if r in e['writes']: out.append('%x'%d['off']); break
    print(f.split('/')[-2] if '/' in f else f, len(out), ' '.join(out))
