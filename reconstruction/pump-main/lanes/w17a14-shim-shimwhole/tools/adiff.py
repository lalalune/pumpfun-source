#!/usr/bin/env python3
"""adiff.py <cand.so|main> <orig_lo> <orig_hi> [--mask rfj]: aligned listing of the original admin_cto window
[orig_lo, orig_hi) against the candidate, aligned by difflib on masked tokens; '=' exact match, '~' masked match only,
'-' orig only, '+' cand only. Disassembly by the w14a128 dis.py."""
import sys, os, difflib
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import rc
sys.path.insert(0, T)
import dis14 as D

a = sys.argv[1:]
m = 'rfj'
if '--mask' in a:
    i = a.index('--mask'); m = a[i + 1]; del a[i:i + 2]
p = a[0]
if p == 'main':
    p = os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
lo, hi = int(a[1], 16), int(a[2], 16)
O = rc.orig_window(); C = rc.elf_fn(p)
ot, oo = rc.mask(O); ct, co = rc.mask(C)
A = rc.rfj(ot, 'r' in m, 'f' in m, 'j' in m); B = rc.rfj(ct, 'r' in m, 'f' in m, 'j' in m)
od = dict(D.d(O)); cd = dict(D.d(C))
sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if i2 <= 0 or (i1 < len(oo) and oo[min(i2, len(oo)) - 1] < lo) or (i1 < len(oo) and oo[i1] >= hi):
        continue
    if tag == 'equal':
        for k in range(i2 - i1):
            o = oo[i1 + k]; c = co[j1 + k]
            if not (lo <= o < hi):
                continue
            s = '=' if ot[i1 + k] == ct[j1 + k] else '~'
            print(f'{s} {o:05x} {od.get(o, "?"):40s} | {c:05x} {cd.get(c, "?")}')
    else:
        n = max(i2 - i1, j2 - j1)
        for k in range(n):
            ol = f'{oo[i1+k]:05x} {od.get(oo[i1+k], "?"):40s}' if i1 + k < i2 else ' ' * 46
            cl = f'{co[j1+k]:05x} {cd.get(co[j1+k], "?")}' if j1 + k < j2 else ''
            s = '!' if (i1 + k < i2 and j1 + k < j2) else ('-' if i1 + k < i2 else '+')
            print(f'{s} {ol} | {cl}')
