#!/usr/bin/env python3
"""split win.py show --full output into orig and cand listings with window offsets."""
import re,sys
src=sys.argv[1]; which=sys.argv[2]  # orig|cand
lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0
hi=int(sys.argv[4],16) if len(sys.argv)>4 else 1<<30
base=0x22a10
for l in open(src):
    l=l.rstrip('\n')
    m=re.match(r'^- (0x[0-9a-f]+)\s{2,}(\S.*)$',l)
    if m and which=='orig':
        a=int(m.group(1),16)-base
        if lo<=a<hi: print('-',hex(a),m.group(2))
        continue
    m=re.match(r'^\+\s+(0x[0-9a-f]+)\s{2}(\S.*)$',l)
    if m and which=='cand':
        a=int(m.group(1),16)-base
        if lo<=a<hi: print('+',hex(a),m.group(2))
        continue
    m=re.match(r'^  (0x[0-9a-f]+) (0x[0-9a-f]+)\s{2}(\S.*)$',l)
    if m:
        a=int(m.group(1 if which=='orig' else 2),16)-base
        if lo<=a<hi: print(' ',hex(a),m.group(3))
