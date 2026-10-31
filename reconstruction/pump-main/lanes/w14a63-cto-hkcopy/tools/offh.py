#!/usr/bin/env python3
"""offh.py lo hi fn.bin...: histogram of r10-relative offsets (ld/st and lea) in [-hi,-lo], side by side."""
import sys, struct, collections
lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
def hist(p):
    b = open(p, 'rb').read(); h = collections.Counter(); fr = {}; i = 0
    while i < len(b):
        op, regs, off, imm = struct.unpack_from('<BBhi', b, i); dst = regs & 15; src = regs >> 4; cls = op & 7
        if cls in (1, 2, 3) and (dst == 10 or src == 10): h[-off] += 1
        if op == 0xbf and src == 10: fr[dst] = 1
        elif op == 0x07 and dst in fr: h[-imm] += 1; del fr[dst]
        elif dst in fr and cls in (4, 7): del fr[dst]
        i += 16 if op == 0x18 else 8
    return h
H = [hist(p) for p in sys.argv[3:]]
ks = sorted({k for h in H for k in h if lo <= k <= hi})
print('off     ' + ' '.join(f'{p.split("/")[-2] if "/" in p else p:>8s}' for p in sys.argv[3:]))
for k in ks: print(f'{-k:#07x} ' + ' '.join(f'{h.get(k,0):8d}' for h in H).replace('-0x','-'))
