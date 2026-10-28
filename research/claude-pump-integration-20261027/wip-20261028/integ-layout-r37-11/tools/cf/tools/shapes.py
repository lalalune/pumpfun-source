#!/usr/bin/env python3
"""For every original window with sites in scope: same-shape candidates and their sites."""
import sys
from cf import *
cand = sys.argv[1] if len(sys.argv) > 1 else str(SC / 'base/i1/unstripped.so')
O = load_orig(); C = load_cand(cand)
M = matched_map(O, C)
byshape = defaultdict(list)
for a, f in C.items():
    if f['sites']:
        byshape[(f['bytes'], f['shape'])].append(a)
oby = defaultdict(list)
for st, w in O.items():
    if w['sites']:
        oby[(w['bytes'], w['shape'])].append(st)
for k in sorted(oby, key=lambda k: -len(oby[k])):
    os_ = oby[k]; cs_ = byshape.get(k, [])
    if all(all(s['short'] == 'lib.rs' for s in O[st]['sites']) for st in os_):
        continue
    print(f"== shape {k[1]} {k[0]}B: {len(os_)} orig / {len(cs_)} cand")
    for st in sorted(os_, key=lambda st: [(s['short'], s['line']) for s in O[st]['sites']]):
        print(f"   O {st:#08x} {'M' if st in M else '-'} {fmt_sites(O[st]['sites'])}")
    for a in cs_:
        print(f"   C {a:#08x} {fmt_sites(C[a]['sites'])}  {C[a]['name'][:90]}")
