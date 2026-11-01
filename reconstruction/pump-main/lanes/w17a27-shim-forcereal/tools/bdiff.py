#!/usr/bin/env python3
"""bdiff.py <a.bin> <b.bin>: positional instruction diff of two same-size candidates (offset, a, b). Experiment only."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import d as D
a=D.dis(D.load(sys.argv[1])); b=D.dis(D.load(sys.argv[2]))
da={o:s for o,s in a}; db={o:s for o,s in b}
n=0
for o in sorted(set(da)|set(db)):
    if da.get(o)!=db.get(o):
        n+=1
        if '--q' not in sys.argv: print(f'{o:#06x}  {da.get(o,""):<36} {db.get(o,"")}')
print('ndiff',n)
