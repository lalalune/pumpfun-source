#!/usr/bin/env python3
"""sbs2.py fn.bin lo hi [level]: L2 (default) aligned side-by-side orig [lo,hi) vs cand, both via bdis (experiment only)."""
import sys, os, difflib
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from bdis import decode
import cls as C
f, lo, hi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0); lv = int(sys.argv[4]) if len(sys.argv) > 4 else 2
O = open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a85-cto-s1reload/orig.bin'), 'rb').read(); c = open(f, 'rb').read()
oi = decode(O); ci = decode(c)
def tk(raw, ins): return [C.mask(raw[d['off']:d['off'] + d['n']], lv) for d in ins]
sm = difflib.SequenceMatcher(None, tk(O, oi), tk(c, ci), autojunk=False)
for tag, a1, a2, b1, b2 in sm.get_opcodes():
    for k in range(max(a2 - a1, b2 - b1)):
        od = oi[a1 + k] if a1 + k < a2 else None; cd = ci[b1 + k] if b1 + k < b2 else None
        ref = od['off'] if od else (oi[a1]['off'] if a1 < len(oi) else 0)
        if not (lo <= ref < hi): continue
        ot = od['txt'] if od else ''; ct = cd['txt'] if cd else ''
        mark = ' ' if (tag == 'equal' and ot == ct) else ('~' if tag == 'equal' else '*')
        print('%s %5s %-34s | %5s %s' % (mark, '%04x' % od['off'] if od else '', ot, '%04x' % cd['off'] if cd else '', ct))
