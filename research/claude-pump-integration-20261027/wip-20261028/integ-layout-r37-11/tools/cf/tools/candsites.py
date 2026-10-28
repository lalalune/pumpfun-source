#!/usr/bin/env python3
"""List candidate functions with sites, grouped by file (sorted by line). Marks matched."""
import sys
from cf import *
cand = sys.argv[1]
flt = sys.argv[2:] 
O = load_orig(); C = load_cand(cand)
M = matched_map(O, C)
cm = {}
for st, ms in M.items():
    for a in ms: cm[a] = st
rows = defaultdict(list)
for a, f in C.items():
    for s in f['sites']:
        rows[s["short"]].append((s["line"] or 0, a, s["code"] or 0, f["bytes"], f["name"]))
for p in sorted(rows):
    if flt and not any(p.startswith(x) for x in flt): continue
    print('==', p)
    for line, a, code, n, nm in sorted(rows[p]):
        print(f"   {line:5d} {code} {a:#08x} {n:6d}B {'M:'+hex(cm[a]) if a in cm else '-':10s} {nm[:110]}")
