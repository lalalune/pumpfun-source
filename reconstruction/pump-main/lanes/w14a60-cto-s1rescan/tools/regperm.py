#!/usr/bin/env python3
"""regperm.py <fn.bin> lo hi: in an orig range, align at L2 (frame+regs masked) and count (orig dst/src -> cand dst/src)
register pairs over aligned instructions whose registers differ."""
import sys, difflib, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rx_lib as R
import importlib.util
spec = importlib.util.spec_from_file_location('cls', Path(__file__).resolve().parent / 'cls.py')
src, lo, hi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
sys.argv = ['cls', src, hex(lo), hex(hi)]
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    cls = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls)
import json
info = json.loads(buf.getvalue().strip().split('\n')[-1]); clo, chi = int(info['clo'], 16), int(info['chi'], 16)
O = [x for x in cls.insns(R.orig_window()) if lo <= x[0] < hi]; C = [x for x in cls.insns(R.cand_fn(src)) if clo <= x[0] < chi]
sm = difflib.SequenceMatcher(None, [cls.mask(t, 2) for _, t in O], [cls.mask(t, 2) for _, t in C], autojunk=False)
pairs = collections.Counter(); diff = 0; tot = 0
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        to, tc = O[a+k][1], C[b+k][1]; tot += 1
        if to[1] != tc[1]:
            diff += 1
            for so, sc in ((to[1] & 15, tc[1] & 15), (to[1] >> 4, tc[1] >> 4)):
                if so != sc: pairs['r%d->r%d' % (so, sc)] += 1
print(json.dumps({'aligned': tot, 'reg_diff': diff, 'pairs': dict(pairs.most_common(14))}))
