#!/usr/bin/env python3
"""cdiff.py <a.bin|so> <b.bin|so> <orig_lo> <orig_hi> [--mask rfj]: side-by-side of two candidates over an original
window range: each candidate is aligned to the original (difflib, masked), then rows are joined on orig offset."""
import sys, os, difflib
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import rc, dis14 as D
a = sys.argv[1:]; m = 'rfj'
if '--mask' in a:
    i = a.index('--mask'); m = a[i+1]; del a[i:i+2]
def load(p):
    if p == 'main': p = os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
    return rc.elf_fn(p)
O = rc.orig_window(); A = load(a[0]); B = load(a[1]); lo, hi = int(a[2], 16), int(a[3], 16)
ot, oo = rc.mask(O)
def align(C):
    ct, co = rc.mask(C)
    X = rc.rfj(ot, 'r' in m, 'f' in m, 'j' in m); Y = rc.rfj(ct, 'r' in m, 'f' in m, 'j' in m)
    sm = difflib.SequenceMatcher(None, X, Y, autojunk=False); mp = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2-i1): mp[oo[i1+k]] = (co[j1+k], ot[i1+k] == ct[j1+k])
    return mp
od = dict(D.d(O)); ad = dict(D.d(A)); bd = dict(D.d(B))
ma = align(A); mb = align(B)
for o in oo:
    if not (lo <= o < hi): continue
    x = ma.get(o); y = mb.get(o)
    sa = ('%s%05x %-28s' % ('=' if x[1] else '~', x[0], ad.get(x[0], '?'))) if x else ' ' * 35
    sb = ('%s%05x %-28s' % ('=' if y[1] else '~', y[0], bd.get(y[0], '?'))) if y else ' ' * 35
    flag = '*' if (x and y and ad.get(x[0]) != bd.get(y[0])) or (bool(x) != bool(y)) else ' '
    print('%s %05x %-28s | %s | %s' % (flag, o, od[o], sa, sb))
