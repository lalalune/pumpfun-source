#!/usr/bin/env python3
"""For each original window with sites in scope: original callers (with their sites) and callees."""
import sys
from cf import *
O = load_orig()
C = load_cand(str(SC / 'base/i1/unstripped.so'))
M = matched_map(O, C)
oc = callers(O)
scope = sys.argv[1:] or None
def label(st):
    w = O.get(st)
    if not w: return f'{st:#x}(?)'
    m = 'M' if st in M else '-'
    nm = C[M[st][0]]['name'][:60] if st in M else ''
    ss = fmt_sites(w['sites'][:4])
    return f"{st:#x}[{m} {w['bytes']}B {ss} {nm}]"
for st in sorted(O):
    w = O[st]
    if not w['sites']: continue
    files = {s['short'] for s in w['sites']}
    if files == {'lib.rs'}: continue
    if scope and not any(any(f.startswith(x) for x in scope) for f in files): continue
    print(f"{label(st)}")
    for (p, off) in oc.get(st, []):
        print(f"    <- {label(p)} @+{off:#x}")
