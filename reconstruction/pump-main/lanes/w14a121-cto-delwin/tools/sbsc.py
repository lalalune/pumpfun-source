#!/usr/bin/env python3
"""sbsc.py fn.bin lo hi [level]: side-by-side by OURS offset range [lo,hi), masked SequenceMatcher (rx tokens)."""
import sys, os, difflib
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from bdis import decode
import cls as C
f, lo, hi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0); lv = int(sys.argv[4]) if len(sys.argv) > 4 else 1
O = open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a121-cto-delwin/orig.bin'), 'rb').read(); c = open(f, 'rb').read()
oi = decode(O); ci = decode(c)
def tk(raw, ins): return [C.mask(raw[d['off']:d['off'] + d['n']], lv) for d in ins]
sm = difflib.SequenceMatcher(None, tk(O, oi), tk(c, ci), autojunk=False)
for tag, a1, a2, b1, b2 in sm.get_opcodes():
    if b2 <= b1 and not (a2>a1): continue
    cs = ci[b1]['off'] if b1 < len(ci) else len(c)
    ce = ci[b2-1]['off'] if b2>b1 else cs
    if ce < lo or cs >= hi: continue
    n = max(a2 - a1, b2 - b1)
    for k in range(n):
        x = oi[a1 + k] if a1 + k < a2 else None; y = ci[b1 + k] if b1 + k < b2 else None
        if y and not (lo <= y['off'] < hi): continue
        if y is None and not (lo<=cs<hi): continue
        mark = ' ' if tag == 'equal' else '*'
        print('%s %05s %-34s | %05s %s' % (mark, '%05x' % x['off'] if x else '', x['txt'] if x else '', '%05x' % y['off'] if y else '', y['txt'] if y else ''))
