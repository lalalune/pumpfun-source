#!/usr/bin/env python3
"""rsize.py <a> <b> ...: candidate instruction count per original region (each cand insn is attributed to the region of
the last aligned original insn, rfj-masked difflib alignment). Prints per-region counts and deltas vs the first."""
import sys, os, difflib
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import rc
O = rc.orig_window(); ot, oo = rc.mask(O); X = rc.rfj(ot, True, True, True)
def reg(o):
    r = None
    for a, n in rc.REG:
        if o >= a: r = n
    return r
def counts(p):
    C = rc.elf_fn(p); ct, co = rc.mask(C); Y = rc.rfj(ct, True, True, True)
    sm = difflib.SequenceMatcher(None, X, Y, autojunk=False)
    cnt = {n: 0 for a, n in rc.REG}; last = 'E1'
    m = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1): m[j1 + k] = i1 + k
    for j in range(len(ct)):
        if j in m: last = reg(oo[m[j]])
        cnt[last] += 1
    return cnt, len(ct)
base = None
for p in sys.argv[1:]:
    c, n = counts(p)
    if base is None:
        base = c; print(os.path.basename(os.path.dirname(p)) or p, n, ' '.join(f'{k}:{v}' for k, v in c.items()))
    else:
        print(os.path.basename(os.path.dirname(p)) or p, n, ' '.join(f'{k}:{v-base[k]:+d}' for k, v in c.items() if v != base[k]))
