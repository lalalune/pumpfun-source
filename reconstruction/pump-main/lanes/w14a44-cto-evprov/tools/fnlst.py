#!/usr/bin/env python3
"""fnlst.py <fn.bin> [lo hi] : lst.py-style listing (op dst src off imm) of an rx.py fn.bin; or diff two: fnlst.py a.bin b.bin lo hi"""
import sys, struct
def lst(b):
    out = []; i = 0
    while i < len(b):
        op = b[i]; r = b[i+1]; off, imm = struct.unpack_from('<hi', b, i+2)
        out.append((i, '%02x %d %d %d %d' % (op, r & 15, r >> 4, off, imm))); i += 16 if op == 0x18 else 8
    return out
a = sys.argv[1:]
if len(a) >= 2 and not a[1].startswith('0x'):
    import itertools
    x = lst(open(a[0], 'rb').read()); y = lst(open(a[1], 'rb').read()); lo, hi = int(a[2], 16), int(a[3], 16)
    x = [t for t in x if lo <= t[0] < hi]; y = [t for t in y if lo <= t[0] < hi]
    for p, q in itertools.zip_longest(x, y, fillvalue=(0, '')):
        print('%04x %-28s| %04x %s%s' % (p[0], p[1], q[0], q[1], '' if p[1] == q[1] else '   *'))
else:
    lo, hi = (int(a[1], 16), int(a[2], 16)) if len(a) >= 3 else (0, 1 << 30)
    for o, t in lst(open(a[0], 'rb').read()):
        if lo <= o < hi: print('%04x %s' % (o, t))
