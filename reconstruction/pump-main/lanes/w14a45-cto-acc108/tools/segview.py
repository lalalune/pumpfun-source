#!/usr/bin/env python3
"""segview.py <fn.bin> <seg> [lvl] : opcode-level diff (orig vs variant) of one call segment at mask level lvl."""
import sys, difflib, importlib.util, struct
from pathlib import Path
T = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sp', T / 'splice.py'); a0 = sys.argv; sys.argv = ['x']
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp); sys.argv = a0
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
    for x in t:
        s[-1].append(x)
        if x[1][0] == 0x85: s.append([])
    return s
def fmt(x):
    o, b = x; r = b[1]; off, imm = struct.unpack_from('<hi', b, 2)
    return '%04x %02x r%d r%d %d %d' % (o, b[0], r & 15, r >> 4, off, imm)
orig = [w for w in original_windows() if w['start'] == 0x22a10][0]['raw']
k = int(sys.argv[2]); lvl = int(sys.argv[3]) if len(sys.argv) > 3 else 2
a = segs(toks(orig))[k]; b = segs(toks(open(sys.argv[1], 'rb').read()))[k]
sm = difflib.SequenceMatcher(None, [sp.mask(x[1], lvl) for x in a], [sp.mask(x[1], lvl) for x in b], autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal': print(f'  = {i2-i1} ({fmt(a[i1])} .. / {fmt(b[j1])})'); continue
    for i in range(max(i2-i1, j2-j1)):
        l = fmt(a[i1+i]) if i1+i < i2 else ''; r = fmt(b[j1+i]) if j1+i < j2 else ''
        print(f'  {tag[0]} {l:34s} | {r}')
