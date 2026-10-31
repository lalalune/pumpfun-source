#!/usr/bin/env python3
"""dump.py <fn.bin|orig> [lo hi]: lst.py-style listing (off op dst src off imm) of a raw function binary."""
import sys, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'harness'))
a = sys.argv[1:]
if a[0] == 'orig':
    from score import original_windows
    raw = [w for w in original_windows() if w['start'] == 0x22a10][0]['raw']
else: raw = open(a[0], 'rb').read()
lo, hi = (int(a[1], 0), int(a[2], 0)) if len(a) > 2 else (0, len(raw))
i = 0
while i < len(raw):
    op = raw[i]; r = raw[i+1]; off, imm = struct.unpack_from('<hi', raw, i+2); n = 16 if op == 0x18 else 8
    if lo <= i < hi: print('%04x %02x %d %d %d %d' % (i, op, r & 15, r >> 4, off, imm) + (' ; call' if op == 0x85 else ''))
    i += n
