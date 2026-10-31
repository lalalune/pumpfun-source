#!/usr/bin/env python3
"""fuse.py base.ll out.jsonl V...: weight oracle. For each value V and each non-trap block from V's def block to the TCF final
block, insert an empty `asm sideeffect "", "r"(V)` (a zero-byte extra use, raising V's spill weight) before the block's br,
and a control `asm sideeffect "", ""()` at the same point. Experiment only."""
import sys, os, re, json, subprocess
D = os.path.dirname(os.path.abspath(__file__))
sys.argv, A = sys.argv[:1], sys.argv[1:]
exec(open(D + '/wsweep.py').read().split('vals = sys.argv[3:]')[0].replace("base, outf = sys.argv[1], sys.argv[2]", "base, outf = A[0], A[1]"))
def blocks_between(d, end):
    out = []; j = d
    while True:
        b = blockend(j)
        if b >= end: break
        out.append(b)
        j = b + 1
        while not re.match(r'^\S.*:', L[j]): j += 1
        while 'llvm.trap' in L[j + 1]:
            j += 1
            while not re.match(r'^\S.*:', L[j]): j += 1
    return out
with open(outf, 'a') as fo:
    for v in A[2:]:
        d = defline(v); ty = 'ptr' if v in stores and stores[v][1] == 'ptr' else stores.get(v, (0, 'i64'))[1]
        bl = blocks_between(d, call) + [call]
        for k, b in enumerate(bl):
            for kind in ('use', 'ctl'):
                M = L[:]
                ins = f'  call void asm sideeffect "", "r"({ty} {v})' if kind == 'use' else '  call void asm sideeffect "", ""()'
                M[b:b] = [ins]
                r = run(f"{v.strip('%').replace('.', '_')}-b{k}-{kind}", '\n'.join(M)); r.update(v=v, k=k, kind=kind)
                fo.write(json.dumps(r) + '\n'); fo.flush()
        print(v, len(bl), 'blocks')
