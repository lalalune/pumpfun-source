#!/usr/bin/env python3
"""bdis.py: minimal SBF decoder for admin_cto fn.bin windows (experiment only).
decode(raw) -> list of dict(off, op, dst, src, o, imm, n, txt, reads, writes)."""
import struct
ALU = {0x0: 'add', 0x1: 'sub', 0x2: 'mul', 0x3: 'div', 0x4: 'or', 0x5: 'and', 0x6: 'lsh', 0x7: 'rsh', 0x8: 'neg',
       0x9: 'mod', 0xa: 'xor', 0xb: 'mov', 0xc: 'arsh', 0xd: 'end'}
JMP = {0x0: 'ja', 0x1: 'jeq', 0x2: 'jgt', 0x3: 'jge', 0x4: 'jset', 0x5: 'jne', 0x6: 'jsgt', 0x7: 'jsge', 0x8: 'call',
       0x9: 'exit', 0xa: 'jlt', 0xb: 'jle', 0xc: 'jslt', 0xd: 'jsle'}
SZ = {0x18: 'dw', 0x00: 'w', 0x08: 'h', 0x10: 'b'}


def decode(raw):
    out = []
    i = 0
    while i < len(raw):
        op = raw[i]; regs = raw[i + 1]; dst = regs & 15; src = regs >> 4
        o = struct.unpack_from('<h', raw, i + 2)[0]; imm = struct.unpack_from('<i', raw, i + 4)[0]
        n = 16 if op == 0x18 else 8
        cls = op & 7; rd = set(); wr = set(); txt = '?'
        if op == 0x18:
            imm2 = struct.unpack_from('<I', raw, i + 12)[0]
            txt = 'lddw r%d, 0x%x' % (dst, (imm2 << 32) | (imm & 0xffffffff)); wr = {dst}
        elif cls in (4, 7):
            a = ALU.get(op >> 4, '?') + ('64' if cls == 7 else '32')
            if (op >> 4) == 0xb:
                if op & 8: txt = '%s r%d, r%d' % (a, dst, src); rd = {src}
                else: txt = '%s r%d, %d' % (a, dst, imm)
                wr = {dst}
            else:
                if op & 8: txt = '%s r%d, r%d' % (a, dst, src); rd = {src, dst}
                else: txt = '%s r%d, %d' % (a, dst, imm); rd = {dst}
                wr = {dst}
        elif cls == 1:
            txt = 'ldx%s r%d, [r%d%+d]' % (SZ.get(op & 0x18, '?'), dst, src, o); rd = {src}; wr = {dst}
        elif cls == 3:
            txt = 'stx%s [r%d%+d], r%d' % (SZ.get(op & 0x18, '?'), dst, o, src); rd = {src, dst}
        elif cls == 2:
            txt = 'st%s [r%d%+d], %d' % (SZ.get(op & 0x18, '?'), dst, o, imm); rd = {dst}
        elif cls == 5:
            j = JMP.get(op >> 4, '?')
            if j == 'call':
                txt = 'call %s' % ('0x%x' % imm if src == 0 else 'rel'); rd = {1, 2, 3, 4, 5}; wr = {0, 1, 2, 3, 4, 5}
            elif j == 'exit':
                txt = 'exit'; rd = {0}
            elif j == 'ja':
                txt = 'ja %+d' % o
            else:
                if op & 8: txt = '%s r%d, r%d, %+d' % (j, dst, src, o); rd = {dst, src}
                else: txt = '%s r%d, %d, %+d' % (j, dst, imm, o); rd = {dst}
        out.append(dict(off=i, op=op, dst=dst, src=src, o=o, imm=imm, n=n, txt=txt, reads=rd, writes=wr, cls=cls))
        i += n
    return out


if __name__ == '__main__':
    import sys
    raw = open(sys.argv[1], 'rb').read()
    lo = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3], 0) if len(sys.argv) > 3 else len(raw)
    for d in decode(raw):
        if lo <= d['off'] < hi: print('%04x  %s' % (d['off'], d['txt']))
