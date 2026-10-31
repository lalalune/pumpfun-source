#!/usr/bin/env python3
"""occ.py fn.bin lo hi: per callee-saved register (r6-r9) and r0/r5, the live spans inside [lo,hi) with their def
instruction (machine-code liveness, artifacts.liveness). Use on orig.bin and on ours to compare register occupancy."""
import sys, os
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from artifacts import liveness
f, lo, hi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
ins, lout = liveness(open(f, 'rb').read())
for r in (6, 7, 8, 9):
    spans = []; cur = None
    for k, d in enumerate(ins):
        if not (lo <= d['off'] < hi): continue
        live = r in lout[k] or r in d['reads']
        if live and cur is None:
            # find def: scan back
            dd = None
            for j in range(k, max(-1, k - 400), -1):
                if r in ins[j]['writes'] and r in lout[j]: dd = ins[j]; break
            cur = [d['off'], d['off'], dd, 0]
        if live: cur[1] = d['off']; cur[3] += (r in d['reads'])
        if not live and cur is not None: spans.append(cur); cur = None
    if cur: spans.append(cur)
    print('r%d:' % r)
    for a, b, dd, nu in spans:
        if b - a < 0x40 and nu < 2: continue
        print('   %04x-%04x uses %2d  def %s' % (a, b, nu, ('%04x %s' % (dd['off'], dd['txt'])) if dd else '?'))
