#!/usr/bin/env python3
"""slots.py <unstripped.so|orig>: error-site From<AnchorError> sret slot (r1=r10-X) per source line."""
import sys, struct, re
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[3] / 'harness'))
from score import sections, BASE
from original_input import resolve_original
from elf_symbols import function_symbols
def scan(raw):
    i=0; r1fp=None; imms=[]; out=[]
    while i < len(raw):
        op, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
        dst, src = regs & 15, regs >> 4
        if op == 0xbf and dst == 1 and src == 10: r1fp = 0
        elif op == 0x07 and dst == 1 and r1fp == 0: r1fp = imm
        elif dst == 1 and op not in (0x7b, 0x73, 0x6b, 0x63, 0x7a, 0x72, 0x6a, 0x62): r1fp = None
        if op in (0x62, 0x6a, 0x72, 0x7a): imms.append(imm)
        if op == 0x85:
            lines = [x for x in imms if 280 <= x < 800]; codes = [x for x in imms if 2000 <= x < 6200]
            if lines and codes and r1fp: out.append((lines[-1], codes[-1], -r1fp))
            imms = []; r1fp = None
        i += 16 if op == 0x18 else 8
    return out
def fn(p):
    if p == 'orig':
        b = resolve_original(BASE / 'original.so').read_bytes(); s = sections(b); t = s['.text']
        o = 0x22a10 - t['addr'] + t['offset']; return b[o:o+27400]
    b = open(p,'rb').read(); s = sections(b); t = s['.text']
    f = [x for x in function_symbols(b) if re.search(r'admin_cto7execute17h', x[2])][0]
    o = f[0] - t['addr'] + t['offset']; return b[o:o+f[1]]
for p in sys.argv[1:]:
    rows = sorted(scan(fn(p)), key=lambda r: r[2])
    print(p.split('/')[-2] if '/' in p else p, ' '.join(f'{l}:{x:x}' for l, c, x in rows))
