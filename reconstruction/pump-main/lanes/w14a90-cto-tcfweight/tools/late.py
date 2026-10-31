#!/usr/bin/env python3
"""late.py base.ll out.jsonl: 'late reload' bound: the final-block store of a clone1 piece uses a fresh load from %x.i
placed right before that store (the original def becomes dead). Experiment only."""
import sys, os, re, json
D = os.path.dirname(os.path.abspath(__file__))
A = sys.argv[1:]; sys.argv = sys.argv[:1]
exec(open(D + '/wsweep.py').read().split('vals = sys.argv[3:]')[0].replace("base, outf = sys.argv[1], sys.argv[2]", "base, outf = A[0], A[1]"))
P = {'%_190.i': (0, 'ptr', 8), '%_189.i': (24, 'ptr', 8), '%_60.i': (32, 'i64', 8), '%365': (40, 'i8', 8), '%363': (41, 'i8', 1), '%361': (42, 'i8', 2)}
import itertools
def mk(vs):
    M = L[:]
    for v in vs:
        off, ty, al = P[v]; i = stores[v][0]
        nm = v.strip('%').replace('.', '_')
        M[i] = M[i].replace('store %s %s,' % (ty, v), 'store %s %%lr_%s,' % (ty, nm))
        M[i] = '  %%lg_%s = getelementptr inbounds i8, ptr %%x.i, i64 %d\n  %%lr_%s = load %s, ptr %%lg_%s, align %d\n' % (nm, off, nm, ty, nm, al) + M[i]
    return '\n'.join(M)
with open(outf, 'a') as fo:
    for n in (1, 2, 6):
        for vs in itertools.combinations(P, n):
            r = run('late-' + '+'.join(v.strip('%').replace('.', '_') for v in vs), mk(vs)); r['v'] = '+'.join(vs); r['mode'] = 'late'
            fo.write(json.dumps(r) + '\n'); fo.flush()
