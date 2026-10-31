#!/usr/bin/env python3
"""regideal.py fn.bin out.bin [lo hi]: ideal-register bound (experiment only). For every L2-aligned instruction pair in
orig [lo,hi) whose L1 tokens differ only by registers, copy the original's register byte into ours. The frame and
everything else stay as built, so the plain ratio of out.bin bounds what perfect register naming in the region buys."""
import sys, os, difflib
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from bdis import decode
import types
C = types.ModuleType('C'); _s = open(D + '/cls.py').read(); C.__dict__['__file__'] = D + '/cls.py'; exec(_s[:_s.index('def main')], C.__dict__)
f, out = sys.argv[1], sys.argv[2]; lo = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0; hi = int(sys.argv[4], 0) if len(sys.argv) > 4 else 1 << 30
O = open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a85-cto-s1reload/orig.bin'), 'rb').read(); c = bytearray(open(f, 'rb').read())
oi = decode(O); ci = decode(bytes(c))
def tk(raw, ins, lv): return [C.mask(raw[d['off']:d['off'] + d['n']], lv) for d in ins]
sm = difflib.SequenceMatcher(None, tk(O, oi, 2), tk(bytes(c), ci, 2), autojunk=False)
RF = os.environ.get('RF'); RF = set(int(x) for x in RF.split(',')) if RF else None
SUB = os.environ.get('SUB')
o1 = tk(O, oi, 1); c1 = tk(bytes(c), ci, 1); n = 0
for a, b, m in sm.get_matching_blocks():
    for k in range(m):
        od, cd = oi[a + k], ci[b + k]
        if lo <= od['off'] < hi and o1[a + k] != c1[b + k]:
            if RF is not None and not ({cd['dst'], cd['src']} & RF if SUB != 'orig' else {od['dst'], od['src']} & RF): continue
            c[cd['off'] + 1] = O[od['off'] + 1]; n += 1
open(out, 'wb').write(bytes(c)); print('rewrote', n)
