#!/usr/bin/env python3
"""combo.py <m.ll> 'v@blk[@end]' ... : apply several asm-use insertions at once, llc, score; --keep writes fn.bin to var/combo"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import irext
from irre_lib import split_fn, orig
a = sys.argv[1:]; m = a.pop(0); keep = '--keep' in a; a = [x for x in a if x != '--keep']
pre, fn, post = split_fn(open(m).read()); O = orig()
A = irext.analyse(fn)
L = list(A['L'])
for spec in a:
    p = spec.split('@'); v, blk = p[0], p[1]; mode = p[2] if len(p) > 2 else 'start'
    insts = A['B'][blk]; t = A['types'][v]
    if mode == 'end': ln = insts[-1][0]
    else:
        k = 0
        while ' = phi ' in insts[k][2]: k += 1
        ln = insts[k][0]
    L[ln] = irext.asm(v, t) + '\n' + L[ln]
d = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a16-cto-fakeuse/var/combo')
r = irext.run(pre, '\n'.join(L), post, O, d, keep=keep); r.pop('_toks', None)
r['d'] = round(r['ratio'] - 0.63421, 5); r['specs'] = a
print(json.dumps(r))
