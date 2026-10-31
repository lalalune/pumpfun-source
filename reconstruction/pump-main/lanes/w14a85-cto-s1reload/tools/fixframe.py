#!/usr/bin/env python3
"""fixframe.py <fn.bin> <out.bin> <newslot> <mapto> [shift]: undo a probe alloca's frame shift (experiment only).
Every r10-relative access at offset <newslot> (e.g. -8) is rewritten to <mapto> (an existing slot, in the probe's
frame), then every r10-relative offset <= -16 (and mov rX,r10; add rX,imm frame addresses) is shifted by +shift
(default 8). Approximates the build where the probe reuses an existing spill slot instead of adding an alloca."""
import sys, struct
src, dst, ns, mt = sys.argv[1], sys.argv[2], int(sys.argv[3], 0), int(sys.argv[4], 0)
sh = int(sys.argv[5], 0) if len(sys.argv) > 5 else 8
b = bytearray(open(src, 'rb').read()); i = 0; fp = {}
def fix(o):
    if o == ns: o = mt
    return o + sh if o <= -16 else o
while i < len(b):
    op = b[i]; dr = b[i+1] & 15; sr = b[i+1] >> 4; off = struct.unpack_from('<h', b, i+2)[0]; imm = struct.unpack_from('<i', b, i+4)[0]
    cls = op & 7
    if op == 0x18: fp.pop(dr, None); i += 16; continue
    if cls == 1 and sr == 10: struct.pack_into('<h', b, i+2, fix(off))           # ldx
    elif cls in (2, 3) and dr == 10: struct.pack_into('<h', b, i+2, fix(off))    # st/stx
    if op == 0xbf:  # mov64 reg
        if sr == 10: fp[dr] = True
        else: fp.pop(dr, None)
    elif op == 0x07 and fp.get(dr):  # add64 imm on a frame address
        struct.pack_into('<i', b, i+4, fix(imm)); fp.pop(dr, None)
    elif cls in (4, 7, 1, 0) and op not in (0x07,):
        if cls in (4, 7, 1) or cls == 0: fp.pop(dr, None)
    i += 8
open(dst, 'wb').write(bytes(b))
