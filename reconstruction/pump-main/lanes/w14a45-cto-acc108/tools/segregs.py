#!/usr/bin/env python3
"""segregs.py <fn.bin> [seg ...] : for call segments (default 69 = TCF clone run), align orig/variant with frame+regs
masked and count (orig reg -> variant reg) pairs, plus lvl1 (frame-masked) matches."""
import sys, difflib, collections, importlib.util
from pathlib import Path
T = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('segdiff_mod', T / 'splice.py'); a0 = sys.argv; sys.argv = ['x']
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp); sys.argv = a0
from score import original_windows
def toks(raw):
    out = []; i = 0
    while i < len(raw):
        op = raw[i]; n = 16 if op == 0x18 else 8; b = bytearray(raw[i:i+n])
        if op == 0x85: b[1] &= 0x0f; b[4:8] = b'\0'*4
        if op == 0x18: b[4:8] = b'\0'*4; b[12:16] = b'\0'*4
        out.append(bytes(b)); i += n
    return out
def segs(t):
    s = [[]]
    for b in t:
        s[-1].append(b)
        if b[0] == 0x85: s.append([])
    return s
orig = [w for w in original_windows() if w['start'] == 0x22a10][0]['raw']
O = segs(toks(orig)); V = segs(toks(open(sys.argv[1], 'rb').read()))
for k in [int(x) for x in sys.argv[2:]] or [69]:
    a, b = O[k], V[k]
    m1 = sum(x.size for x in difflib.SequenceMatcher(None, [sp.mask(x, 1) for x in a], [sp.mask(x, 1) for x in b], autojunk=False).get_matching_blocks())
    sm = difflib.SequenceMatcher(None, [sp.mask(x, 2) for x in a], [sp.mask(x, 2) for x in b], autojunk=False)
    c = collections.Counter(); n = 0; m2 = 0
    for blk in sm.get_matching_blocks():
        m2 += blk.size
        for i in range(blk.size):
            x, y = a[blk.a+i], b[blk.b+i]
            if x[1] != y[1]:
                n += 1
                if x[1] & 15 != y[1] & 15: c[('r%d' % (x[1] & 15), 'r%d' % (y[1] & 15))] += 1
                if x[1] >> 4 != y[1] >> 4: c[('r%d' % (x[1] >> 4), 'r%d' % (y[1] >> 4))] += 1
    print(f'seg {k}: n_o {len(a)} n_v {len(b)} lvl1 {m1} lvl2 {m2} regdiff {n} ::', ' '.join(f'{p}>{q}:{v}' for (p, q), v in c.most_common(8)))
