#!/usr/bin/env python3
"""fm.py fn.bin...: ratio vs original with r10-relative ld/st offsets and add64-imm after mov rX,r10 masked (frame-masked)."""
import sys, os, difflib
T = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a63-cto-hkcopy')
src = open(T + '/tools/llcx.py').read(); g = {}; exec(src[:src.index("SDK=os.path.expanduser")], g)
def fmask(raw):
    toks = g['mask'](raw); out = []; fr = set()
    for t in toks:
        b = bytearray(t); op = b[0]; dst = b[1] & 15; srcr = b[1] >> 4; cls = op & 7
        if cls in (1, 2, 3) and (dst == 10 or srcr == 10): b[2:4] = b'\0\0'
        if op == 0xbf and srcr == 10: fr.add(dst)
        elif op == 0x07 and dst in fr: b[4:8] = b'\0'*4; fr.discard(dst)
        elif cls in (4, 7) and dst in fr: fr.discard(dst)
        out.append(bytes(b))
    return out
O = fmask(g['orig_window']())
for p in sys.argv[1:]:
    c = open(p, 'rb').read()
    print(p, len(c), round(difflib.SequenceMatcher(None, O, fmask(c), autojunk=False).ratio(), 5))
