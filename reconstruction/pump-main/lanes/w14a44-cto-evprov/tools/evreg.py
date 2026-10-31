#!/usr/bin/env python3
"""evreg.py <fn.bin> [lo hi] : per-level (0 raw,1 frame,2 +regs,3 +jumps) match counts against the original over the
call segments whose ORIGINAL start offset lies in [lo,hi) (default the AdminCtoEvent tail 0x4e60-0x5538).
Segments are split at calls (equal call counts assumed), tokens as segdiff.py. Prints JSON."""
import sys, difflib, json, importlib.util
from pathlib import Path
here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('splice', here / 'splice.py')
sv = sys.argv; sys.argv = ['x']; sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp); sys.argv = sv
from score import original_windows
def toks(raw):
    out = []; i = 0
    while i < len(raw):
        op = raw[i]; n = 16 if op == 0x18 else 8; b = bytearray(raw[i:i+n])
        if op == 0x85: b[1] &= 0x0f; b[4:8] = b'\0'*4
        if op == 0x18: b[4:8] = b'\0'*4; b[12:16] = b'\0'*4
        out.append((i, bytes(b))); i += n
    return out
def segs(t):
    s = [[]]
    for off, b in t:
        s[-1].append((off, b))
        if b[0] == 0x85: s.append([])
    return s
a = sys.argv[1:]
lo, hi = (int(a[1], 16), int(a[2], 16)) if len(a) >= 3 else (0x4e60, 0x5538)
orig = [w for w in original_windows() if w['start'] == 0x22a10][0]['raw']
O = segs(toks(orig)); V = segs(toks(open(a[0], 'rb').read()))
if len(O) != len(V): print(json.dumps({'error': 'segcount', 'o': len(O), 'v': len(V)})); sys.exit()
idx = [i for i, s in enumerate(O) if s and lo <= s[0][0] < hi]
res = {'segs': [idx[0], idx[-1]], 'n_o': sum(len(O[i]) for i in idx), 'n_v': sum(len(V[i]) for i in idx)}
for lvl in range(4):
    m = 0
    for i in idx:
        x = [sp.mask(t, lvl) for _, t in O[i]]; y = [sp.mask(t, lvl) for _, t in V[i]]
        m += sum(b.size for b in difflib.SequenceMatcher(None, x, y, autojunk=False).get_matching_blocks())
    res[f'L{lvl}'] = m
print(json.dumps(res))
