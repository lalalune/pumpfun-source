#!/usr/bin/env python3
"""shiftwi.py fn.bin below delta: what-if: every r10 offset more negative than -below gets +delta (frame shift fix)."""
import sys, os, struct, difflib
T = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a63-cto-hkcopy')
src = open(T + '/tools/llcx.py').read(); g = {}; exec(src[:src.index("SDK=os.path.expanduser")], g)
p, below, delta = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
b = bytearray(open(p, 'rb').read()); fr = set(); i = 0
while i < len(b):
    op, regs, off, imm = struct.unpack_from('<BBhi', b, i); dst = regs & 15; s = regs >> 4; cls = op & 7
    if cls in (1, 2, 3) and (dst == 10 or s == 10) and off < -below: struct.pack_into('<h', b, i + 2, off + delta)
    if op == 0xbf and s == 10: fr.add(dst)
    elif op == 0x07 and dst in fr:
        if imm < -below: struct.pack_into('<i', b, i + 4, imm + delta)
        fr.discard(dst)
    elif dst in fr and cls in (4, 7): fr.discard(dst)
    i += 16 if op == 0x18 else 8
rr, sd = g["metric"](bytes(b), g["orig_window"]()); print(p, round(rr, 5)); open(p + ".shift", "wb").write(bytes(b))
