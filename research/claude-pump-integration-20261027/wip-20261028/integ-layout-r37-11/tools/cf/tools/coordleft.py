#!/usr/bin/env python3
"""Unmatched original windows (any file) whose bytes equal some candidate function's up to Source slots
(same length, same coordinate-masked shape): what is left to gain by positioning alone."""
import sys
from cf import *
cand = sys.argv[1]
O = load_orig(); C = load_cand(cand)
M = matched_map(O, C)
byshape = defaultdict(list)
for a, f in C.items():
    byshape[(f['bytes'], f['shape'])].append(a)
for st in sorted(O):
    w = O[st]
    if st in M or not w['sites']:
        continue
    cs = byshape.get((w['bytes'], w['shape']), [])
    if cs:
        print(f"{st:#x} {w['bytes']}B {fmt_sites(w['sites'])}  <- " + '; '.join(f"{a:#x} {fmt_sites(C[a]['sites'])} {C[a]['name'][:60]}" for a in cs[:3]))
