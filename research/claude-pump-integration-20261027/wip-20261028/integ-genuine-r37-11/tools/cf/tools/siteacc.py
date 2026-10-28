#!/usr/bin/env python3
"""Site accuracy: for each original Source site (non-lib.rs), is there a candidate site with the same
(file, line, code)?  Prints per-file counts."""
import sys
from cf import *
cand = sys.argv[1]
O = load_orig(); C = load_cand(cand)
have = set()
for a, f in C.items():
    for s in f['sites']:
        have.add((s['short'], s['line'], s['code']))
from collections import Counter
tot = Counter(); ok = Counter()
for st, w in O.items():
    for s in w['sites']:
        if s['short'] == 'lib.rs':
            continue
        tot[s['short']] += 1
        if (s['short'], s['line'], s['code']) in have:
            ok[s['short']] += 1
for f in sorted(tot):
    print(f"{ok[f]:3d}/{tot[f]:3d}  {f}")
print(f"total {sum(ok.values())}/{sum(tot.values())}")
