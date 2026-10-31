#!/usr/bin/env python3
"""sdiff.py <unstripped.so> lo hi [--lvl 2] [--lst-o f --lst-c f]: masked-token opcode diff of a window region,
printing every non-equal block with original and candidate listing lines side by side."""
import sys, difflib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import splice
so, lo, hi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
args = sys.argv[4:]
lvl = int(args[args.index('--lvl')+1]) if '--lvl' in args else 2
lo_f = args[args.index('--lst-o')+1]; lc_f = args[args.index('--lst-c')+1]
def lst(f):
    d = {}
    for l in open(f):
        p = l.split(None, 1); d[int(p[0], 16)] = p[1].rstrip() if len(p) > 1 else ''
    return d
LO, LC = lst(lo_f), lst(lc_f)
o, k, on, cn = splice.load(so)
O = [(off, t) for off, t in o if lo <= off < hi]; K = [(off, t) for off, t in k if lo <= off < (hi if '--chi' not in args else int(args[args.index('--chi')+1], 0))]
a = [splice.mask(t, lvl) for _, t in O]; b = [splice.mask(t, lvl) for _, t in K]
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
tot = {'replace': [0, 0], 'delete': [0, 0], 'insert': [0, 0]}
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        print('  = %d insns  o%04x c%04x' % (i2-i1, O[i1][0], K[j1][0])); continue
    tot[tag][0] += i2-i1; tot[tag][1] += j2-j1
    print('--- %s o[%d] c[%d]' % (tag, i2-i1, j2-j1))
    n = max(i2-i1, j2-j1)
    for x in range(n):
        ol = '%04x %s' % (O[i1+x][0], LO[O[i1+x][0]]) if i1+x < i2 else ''
        cl = '%04x %s' % (K[j1+x][0], LC[K[j1+x][0]]) if j1+x < j2 else ''
        print('   %-52s | %s' % (ol[:52], cl[:60]))
print(tot)
