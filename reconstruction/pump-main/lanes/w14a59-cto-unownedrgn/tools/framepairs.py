#!/usr/bin/env python3
"""framepairs.py <so> [lo hi] : global (or region) frame-offset remap table. Aligns orig/cand per 0x200 chunk... no:
aligns the whole window with frame masked (L1) and, for aligned pairs whose only difference is the r10 displacement,
counts (orig disp -> cand disp). Groups pairs into constant-shift runs (same delta over a contiguous orig range), which
is how a misplaced alloca shows up. Prints the top remaps with the number of instructions each would fix."""
import sys, difflib, collections, struct
from pathlib import Path
import importlib.util
p = Path(__file__).resolve().parent / 'splice.py'
spec = importlib.util.spec_from_file_location('splice', p); sv = sys.argv; sys.argv = ['x']
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp); sys.argv = sv
so = sys.argv[1]; lo = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0; hi = int(sys.argv[3], 0) if len(sys.argv) > 3 else 1 << 30
o, k, on, cn = sp.load(so)
a = [(off, t) for off, t in o if lo <= off < hi]; b = [(off, t) for off, t in k if lo <= off < hi]
sm = difflib.SequenceMatcher(None, [sp.mask(x, 1) for _, x in a], [sp.mask(x, 1) for _, x in b], autojunk=False)
pairs = collections.Counter(); where = collections.defaultdict(list); n_eq = 0
def disp(t):
    op = t[0]; cls = op & 7; d = t[1] & 15; s = t[1] >> 4
    if cls in (1, 2, 3) and (d == 10 or s == 10): return struct.unpack_from('<h', t, 2)[0]
    if op == 0x07 and struct.unpack_from('<i', t, 4)[0] < 0: return struct.unpack_from('<i', t, 4)[0]
    return None
for blk in sm.get_matching_blocks():
    for i in range(blk.size):
        (ao, x), (bo, y) = a[blk.a + i], b[blk.b + i]
        if x == y: n_eq += 1; continue
        dx, dy = disp(x), disp(y)
        if dx is not None and dy is not None and dx != dy:
            pairs[(dx, dy)] += 1; where[(dx, dy)].append(ao)
shift = collections.Counter()
for (dx, dy), v in pairs.items(): shift[dy - dx] += v
print('frame-only differing aligned insns:', sum(pairs.values()), ' equal aligned:', n_eq)
print('by constant shift (cand - orig):')
for s, v in shift.most_common(10):
    ks = sorted([kk for kk in pairs if kk[1] - kk[0] == s], key=lambda kk: kk[0])
    print(f'  {s:+#x}: {v} insns, orig disp {hex(ks[0][0])}..{hex(ks[-1][0])} ({len(ks)} slots)')
print('top single remaps:')
for (dx, dy), v in pairs.most_common(15):
    print(f'  orig -{-dx:#x} -> ours -{-dy:#x}: {v} insns at orig ' + ','.join(hex(x) for x in where[(dx, dy)][:6]))
