#!/usr/bin/env python3
"""rc.py <ref.so|fn.bin> <cand.so|fn.bin>... [--mask none|rfj]: per-region true-LCS matched original tokens of
admin_cto::execute (0x22a10), candidate minus reference, on the w17a01 Ghidra region map (orig offsets).
Tokens are the target_metric tokens (call imm and lddw imm masked). --mask rfj also masks registers, frame offsets
and jump offsets (structure only). Also prints the difflib ratio (the scored metric) and byte size."""
import sys, os, struct, difflib, re
H = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness'
sys.path.insert(0, H)
REG = [(0x0, 'E1'), (0x280, 'E2'), (0x420, 'E3'), (0x708, 'V1'), (0xb00, 'V2'), (0xe60, 'V3'), (0x1258, 'V4'), (0x1490, 'V5'),
       (0x1800, 'J1'), (0x1990, 'J2'), (0x1c88, 'W1'), (0x1f68, 'S1'), (0x26e8, 'T1'), (0x3c50, 'C1'), (0x4aa8, 'P1'),
       (0x4e50, 'EV'), (0x5558, 'TL'), (0x5a18, 'S2'), (0x5c18, 'W2')]
KEEP = r'admin_cto7execute'


def elf_fn(path, pat=KEEP):
    b = open(path, 'rb').read()
    if path.endswith('.bin'):
        return b
    shoff = struct.unpack_from('<Q', b, 0x28)[0]
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', b, 0x3a)
    sh = [struct.unpack_from('<IIQQQQIIQQ', b, shoff + i * shentsize) for i in range(shnum)]
    for s in sh:
        if s[1] == 2:
            so = sh[s[6]][4]
            for j in range(s[5] // 24):
                nm, info, oth, shndx, val, size = struct.unpack_from('<IBBHQQ', b, s[4] + j * 24)
                name = b[so + nm:b.index(b'\0', so + nm)].decode()
                if re.search(pat, name) and (info & 0xf) == 2:
                    sec = sh[shndx]
                    off = sec[4] + val - (sec[3] if path.endswith('.so') else 0)
                    return b[off:off + size]
    raise SystemExit('fn not found ' + path)


def mask(raw):
    m = bytearray(raw); i = 0; toks = []; offs = []
    while i < len(raw):
        op = raw[i]; n = 16 if op == 0x18 else 8
        if op == 0x85:
            m[i + 1] &= 0x0f; m[i + 4:i + 8] = b'\0' * 4
        if op == 0x18:
            m[i + 4:i + 8] = b'\0' * 4; m[i + 12:i + 16] = b'\0' * 4
        toks.append(bytes(m[i:i + n])); offs.append(i); i += n
    return toks, offs


SP = False; AL = False
def rfj(t, r=True, f=True, j=True):
    out = []
    for x in t:
        x = bytearray(x); op = x[0]; cl = op & 7
        if (f or SP or AL) and ((cl == 1 and (x[1] >> 4) == 10) or (cl in (2, 3) and (x[1] & 15) == 10)):
            off = int.from_bytes(x[2:4], 'little', signed=True)
            if f or (SP and off < -0x8e0) or (AL and off >= -0x8e0):
                x[2:4] = b'\0\0'
        if f and op in (0x07, 0x87) and (x[1] & 15) != 10 and False:
            pass
        if r:
            x[1] = 0
        if j and cl in (5, 6) and op not in (0x85, 0x95):
            x[2:4] = b'\0\0'
        if f and op in (0x07, 0x87):
            x[4:8] = b'\0' * 4
        out.append(bytes(x))
    return out


def orig_window():
    from score import original_windows
    for w in original_windows():
        if w['start'] == 0x22a10:
            return w['raw']


def lcs_hits(A, B):
    n, k = len(A), len(B)
    L = [[0] * (k + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        Li = L[i]; L1 = L[i + 1]; x = A[i]
        for j in range(k - 1, -1, -1):
            Li[j] = L1[j + 1] + 1 if x == B[j] else (L1[j] if L1[j] > Li[j + 1] else Li[j + 1])
    h = [0] * n; i = j = 0
    while i < n and j < k:
        if A[i] == B[j] and L[i][j] == L[i + 1][j + 1] + 1:
            h[i] = 1; i += 1; j += 1
        elif L[i + 1][j] >= L[i][j + 1]:
            i += 1
        else:
            j += 1
    return h


def reg_of(o):
    r = REG[0][1]
    for a, n in REG:
        if o >= a:
            r = n
    return r


def per(path, ot, oo, m):
    C = elf_fn(path); ct, _ = mask(C)
    global SP, AL
    SP = 's' in m; AL = 'a' in m
    if m:
        A = rfj(ot, 'r' in m, 'f' in m, 'j' in m); B = rfj(ct, 'r' in m, 'f' in m, 'j' in m)
    else:
        A = ot; B = ct
    h = lcs_hits(A, B)
    d = {}
    for x, o in zip(h, oo):
        r = reg_of(o); d[r] = d.get(r, 0) + x
    sm = difflib.SequenceMatcher(None, ot, ct, autojunk=False)
    M = sum(b.size for b in sm.get_matching_blocks())
    return d, sum(h), round(2 * M / (len(ot) + len(ct)), 5), M, len(C)


if __name__ == '__main__':
    a = sys.argv[1:]; m = ''
    if '--mask' in a:
        i = a.index('--mask'); m = a[i + 1].replace('none', ''); del a[i:i + 2]
    O = orig_window(); ot, oo = mask(O)
    tot = {}
    for o in oo:
        r = reg_of(o); tot[r] = tot.get(r, 0) + 1
    r0, t0, ra0, M0, b0 = per(a[0], ot, oo, m)
    print('ref', os.path.basename(os.path.dirname(a[0])) or a[0], 'lcs', t0, 'ratio', ra0, 'M', M0, 'bytes', b0)
    print('     ' + ' '.join(f'{n}:{r0.get(n,0)}/{tot[n]}' for _, n in REG))
    for p in a[1:]:
        d, t, ra, M, b = per(p, ot, oo, m)
        print(os.path.basename(os.path.dirname(p)) or p, 'lcs', t, f'{t-t0:+d}', 'ratio', ra, 'M', M, 'bytes', b)
        print('     ' + ' '.join(f'{n}:{d.get(n,0)-r0.get(n,0):+d}' for _, n in REG if d.get(n, 0) != r0.get(n, 0)))
