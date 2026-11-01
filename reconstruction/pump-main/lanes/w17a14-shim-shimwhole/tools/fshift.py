#!/usr/bin/env python3
"""fshift.py <ref.so> <cand.so>: frame-offset shift census. Aligns ref and cand by difflib on reg+frame-masked tokens and
counts, for each matched pair that accesses r10, the offset delta cand-ref (histogram), split into alloca (>= -0x8e0) and
spill (< -0x8e0) slots."""
import sys, os, difflib, collections
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import rc
def fr(t):
    op = t[0]; cl = op & 7
    if (cl == 1 and (t[1] >> 4) == 10) or (cl in (2, 3) and (t[1] & 15) == 10):
        return int.from_bytes(t[2:4], 'little', signed=True)
    return None
A = rc.elf_fn(sys.argv[1]); B = rc.elf_fn(sys.argv[2])
at, _ = rc.mask(A); bt, _ = rc.mask(B)
am = rc.rfj(at, True, True, True); bm = rc.rfj(bt, True, True, True)
sm = difflib.SequenceMatcher(None, am, bm, autojunk=False)
h = {'alloca': collections.Counter(), 'spill': collections.Counter()}
for blk in sm.get_matching_blocks():
    for k in range(blk.size):
        x = at[blk.a + k]; y = bt[blk.b + k]
        fa = fr(x); fb = fr(y)
        if fa is None or fb is None: continue
        h['alloca' if fa >= -0x8e0 else 'spill'][fb - fa] += 1
for k, c in h.items():
    print(k, sum(c.values()), ' '.join(f'{d:+#x}:{n}' for d, n in c.most_common(12)))
