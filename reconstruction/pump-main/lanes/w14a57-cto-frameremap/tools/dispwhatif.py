#!/usr/bin/env python3
"""dispwhatif.py <fn.bin> 'lo-hi:a>b,c>d;lo-hi:...' : frame-displacement what-if (bound only, never a proposal).
Rewrites r10 displacements (and add64 rX,-imm frame-address immediates) inside window-offset ranges and scores the
patched admin_cto bytes with rx.py's metric. Example: '0x620-0x9e0:-0x470>-0x488,-0x468>-0x480,-0x460>-0x478'."""
import sys, struct, os, runpy
T = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a57-cto-frameremap/tools')
sys.argv_ = sys.argv; src = open(T + '/llcx.py').read(); g = {}
exec(src[:src.index("SDK=os.path.expanduser")], g)
b = bytearray(open(sys.argv[1], 'rb').read())
def run(spec):
    c = bytearray(b); n = 0
    for part in spec.split(';'):
        rng, maps = part.split(':'); lo, hi = [int(x, 0) for x in rng.split('-')]
        mp = {int(x.split('>')[0], 0): int(x.split('>')[1], 0) for x in maps.split(',')}
        i = 0
        while i < len(c):
            op = c[i]; ln = 16 if op == 0x18 else 8
            if lo <= i < hi:
                cls = op & 7; dst = c[i+1] & 15; srcr = c[i+1] >> 4
                if cls in (1, 2, 3) and (dst == 10 or srcr == 10):
                    d = struct.unpack_from('<h', c, i+2)[0]
                    if d in mp: struct.pack_into('<h', c, i+2, mp[d]); n += 1
                elif op == 0x07:
                    d = struct.unpack_from('<i', c, i+4)[0]
                    if d in mp: struct.pack_into('<i', c, i+4, mp[d]); n += 1
            i += ln
    r, sd = g['metric'](bytes(c), g['orig_window']())
    return n, round(r, 5), sd
for spec in sys.argv[2:]:
    print(spec, run(spec))
