#!/usr/bin/env python3
"""segdiff.py <base fn.bin> <variant fn.bin> [--lvl N] [--top K] : per call-segment match counts vs the original.
Segments are split at call instructions (equal call counts assumed); tokens use rx.py masks (call imm, lddw imm) plus
splice.py mask level N (0 raw, 1 frame, 2 +regs, 3 +jumps). Prints segments where the variant differs from base."""
import sys, difflib, struct, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util
sp_spec = importlib.util.spec_from_file_location('splice', Path(__file__).resolve().parent / 'splice.py')
sys.argv_s = sys.argv; sys.argv = ['x']
sp = importlib.util.module_from_spec(sp_spec); sp_spec.loader.exec_module(sp)
sys.argv = sys.argv_s
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
args = sys.argv[1:]
lvl = int(args[args.index('--lvl')+1]) if '--lvl' in args else 0
top = int(args[args.index('--top')+1]) if '--top' in args else 25
orig = [w for w in original_windows() if w['start'] == 0x22a10][0]['raw']
O = segs(toks(orig)); B = segs(toks(open(args[0], 'rb').read())); V = segs(toks(open(args[1], 'rb').read()))
assert len(O) == len(B) == len(V), (len(O), len(B), len(V))
def m(a, b):
    a = [sp.mask(x, lvl) for _, x in a]; b = [sp.mask(x, lvl) for _, x in b]
    return sum(x.size for x in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
rows = []
for i, (o, b, v) in enumerate(zip(O, B, V)):
    mb, mv = m(o, b), m(o, v)
    rows.append((mv - mb, i, o[0][0], len(o), len(b), len(v), mb, mv))
tb = sum(r[6] for r in rows); tv = sum(r[7] for r in rows)
print(f'lvl {lvl}: segment matches base {tb} variant {tv} (delta {tv-tb})')
for r in sorted(rows)[:top]:
    if r[0] != 0: print('seg %3d orig@%04x n_o %3d n_b %3d n_v %3d match base %3d var %3d  d %+d' % (r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[0]))
print('gains:')
for r in sorted(rows, reverse=True)[:8]:
    if r[0] > 0: print('seg %3d orig@%04x n_o %3d n_b %3d n_v %3d match base %3d var %3d  d %+d' % (r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[0]))
