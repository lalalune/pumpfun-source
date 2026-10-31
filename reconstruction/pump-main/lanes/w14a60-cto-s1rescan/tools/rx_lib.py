import sys, os, struct, re
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness'
def orig_window():
    sys.path.insert(0, H)
    from score import original_windows
    for w in original_windows():
        if w['start'] == 0x22a10: return w['raw']
def elf_fn(path, pat=r'admin_cto7execute'):
    b = open(path, 'rb').read()
    shoff = struct.unpack_from('<Q', b, 0x28)[0]; shentsize, shnum, shstrndx = struct.unpack_from('<HHH', b, 0x3a)
    sh = [struct.unpack_from('<IIQQQQIIQQ', b, shoff+i*shentsize) for i in range(shnum)]
    for i, s in enumerate(sh):
        if s[1] == 2:
            so = sh[s[6]][4]
            for j in range(s[5]//24):
                nm, info, oth, shndx, val, size = struct.unpack_from('<IBBHQQ', b, s[4]+j*24)
                name = b[so+nm:b.index(b'\0', so+nm)].decode()
                if re.search(pat, name) and (info & 0xf) == 2:
                    sec = sh[shndx]; off = sec[4]+val-(sec[3] if path.endswith('.so') else 0)
                    return b[off:off+size]
def cand_fn(p):
    return open(p, 'rb').read() if p.endswith('.bin') else elf_fn(p)
def dis(o, t):
    op = t[0]; d = t[1] & 15; s = t[1] >> 4; off = struct.unpack_from('<h', t, 2)[0]; imm = struct.unpack_from('<i', t, 4)[0]
    return '%04x %02x r%d r%d %d %d' % (o, op, d, s, off, imm)
