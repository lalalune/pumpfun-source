"""Source-site decoder with nearest-store matching (coords.sites picks the FIRST store in a +-30 window, which can
belong to a neighbouring site that reuses the same stack slots)."""
import struct


def decode(raw):
    insn = []
    i = 0
    while i < len(raw):
        op = raw[i]
        if op == 0x18:
            lo = struct.unpack_from('<I', raw, i + 4)[0]; hi = struct.unpack_from('<I', raw, i + 12)[0]
            insn.append((i, op, raw[i + 1], 0, lo | hi << 32)); i += 16
        else:
            _, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
            insn.append((i, op, regs, off, imm)); i += 8
    return insn


def sites(blob, secs, start, raw, read_cstr_at):
    insn = decode(raw)
    dst = lambda r: r & 0xf
    src = lambda r: r >> 4
    out = []
    for k, (pos, op, regs, off, L) in enumerate(insn):
        if not (op == 0x7a and dst(regs) == 10 and 1 <= L <= 200):
            continue
        X = off
        lo, hi = max(0, k - 30), min(len(insn), k + 30)
        order = sorted(range(lo, hi), key=lambda j: abs(j - k))
        ptr = None
        for j in order:
            p2, o2, r2, of2, v2 = insn[j]
            if o2 == 0x7b and dst(r2) == 10 and of2 == X - 8:
                ry = src(r2)
                for jj in range(j - 1, max(-1, j - 40), -1):
                    p3, o3, r3, of3, v3 = insn[jj]
                    if dst(r3) == ry and o3 == 0x18:
                        ptr = v3; break
                    if dst(r3) == ry and o3 not in (0x7b, 0x7a, 0x62, 0x72, 0x6a, 0x63, 0x73, 0x6b):
                        break
                if ptr is not None:
                    break
        if ptr is None:
            continue
        s = read_cstr_at(blob, secs, ptr, L)
        if not (s and s.endswith(b'.rs') and all(32 <= c < 127 for c in s)):
            continue
        line = None; line_slot = None
        for j in order:
            p2, o2, r2, of2, v2 = insn[j]
            if o2 == 0x62 and dst(r2) == 10 and of2 == X + 8:
                line, line_slot = v2, p2; break
        out.append({'slot': pos, 'path': s.decode(), 'line': line, 'len_slot': pos, 'line_slot': line_slot})
    return out
