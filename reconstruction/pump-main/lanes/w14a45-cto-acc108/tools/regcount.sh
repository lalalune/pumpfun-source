#!/bin/bash
# regcount.sh <fn.bin|orig> lo hi : count register defs in a range
python3 $(dirname $0)/dump.py $1 $2 $3 | python3 -c "
import sys,collections
w=collections.Counter()
for l in sys.stdin:
    p=l.split(); op=int(p[1],16); d=int(p[2])
    if op in (0x79,0x71,0x69,0x61,0xbf,0xb7,0x07,0x18,0x67,0x77): w[d]+=1
print(' '.join('r%d:%d'%kv for kv in sorted(w.items())))"
