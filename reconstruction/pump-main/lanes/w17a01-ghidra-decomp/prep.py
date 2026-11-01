#!/usr/bin/env python3
"""Prepare Solana-SBF facts for the Ghidra import (lane w17a01-ghidra-decomp).

Ghidra 12.2 has no SBF loader (e_machine 263), so SbfDecomp.java imports each ELF as a raw image at base 0
(every LOAD segment of these files has offset == vaddr) with the built-in eBPF:LE:64:default language and reads
the facts written here:

  sections.tsv   name  addr  size  flags            (section headers; SbfDecomp splits the raw block by them)
  funcs.tsv      addr  size  noreturn  name  mangled (FUNC symbols from main's unstripped .symtab; every function sits
                                                     at the same address in both files, so the names apply to both)
  syscalls.tsv   site  name  value                  (R_BPF_64_32 relocations: `call -1` sites -> sol_* syscall, or a
                                                     defined function such as custom_panic when value != 0)
  lddw.tsv       site  target  label  comment       (R_BPF_64_RELATIVE lddw sites in .text and their data targets)
  data.tsv       addr  size  kind  label  text      (sized .rodata/.data.rel.ro objects + lddw targets)

usage: prep.py <elf> <unstripped-with-symbols> <outdir>
"""
import re, struct, sys
from pathlib import Path

B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
KNOWN = {  # well-known program ids and mints that show up as 32-byte rodata constants
    '11111111111111111111111111111111': 'SYSTEM_PROGRAM_ID',
    'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA': 'TOKEN_PROGRAM_ID',
    'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb': 'TOKEN_2022_PROGRAM_ID',
    'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL': 'ASSOCIATED_TOKEN_PROGRAM_ID',
    'So11111111111111111111111111111111111111112': 'NATIVE_MINT',
    '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P': 'PUMP_PROGRAM_ID',
    'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA': 'PUMP_AMM_PROGRAM_ID',
    'pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ': 'PUMP_FEES_PROGRAM_ID',
    'SysvarRent111111111111111111111111111111111': 'SYSVAR_RENT_ID',
    'SysvarC1ock11111111111111111111111111111111': 'SYSVAR_CLOCK_ID',
    'metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s': 'METAPLEX_PROGRAM_ID',
}


def b58(b):
    n = int.from_bytes(b, 'big'); s = ''
    while n:
        n, r = divmod(n, 58); s = B58[r] + s
    return '1' * (len(b) - len(b.lstrip(b'\0'))) + s


def demangle(s):
    m = re.match(r'^_ZN(.*)E$', s)
    if not m:
        return s
    rest, parts = m.group(1), []
    while rest:
        k = re.match(r'^([1-9][0-9]*)', rest)
        if not k:
            return s
        n = int(k.group(1)); rest = rest[len(k.group(1)):]
        if n > len(rest):
            return s
        p = rest[:n]; parts.append(p[1:] if p.startswith('_$') else p); rest = rest[n:]
    if parts and re.fullmatch(r'h[0-9a-f]{16}', parts[-1]):
        parts = parts[:-1]
    t = '::'.join(parts)
    for a, c in [('$LT$', '<'), ('$GT$', '>'), ('$RF$', '&'), ('$BP$', '*'), ('$C$', ','), ('$u20$', ' '),
                 ('$u27$', "'"), ('$u5b$', '['), ('$u5d$', ']'), ('$u7b$', '{'), ('$u7d$', '}'), ('$u3b$', ';'),
                 ('$u2b$', '+'), ('$u22$', '"'), ('$LP$', '('), ('$RP$', ')'), ('..', '::'), ('$u7e$', '~')]:
        t = t.replace(a, c)
    return t


def elf(path):
    f = Path(path).read_bytes()
    shoff, = struct.unpack_from('<Q', f, 0x28); shnum, shstrndx = struct.unpack_from('<HH', f, 0x3c)
    secs = []
    for i in range(shnum):
        nm, typ, flags, addr, off, size, link, info, al, es = struct.unpack_from('<IIQQQQIIQQ', f, shoff + i * 64)
        secs.append(dict(nm=nm, typ=typ, flags=flags, addr=addr, off=off, size=size, link=link))
    sh = secs[shstrndx]
    for s in secs:
        a = sh['off'] + s['nm']
        s['name'] = f[a:f.index(b'\0', a)].decode()
    return f, secs, {s['name']: s for s in secs}


def symbols(f, S, tab, strtab):
    st, ss = S[tab], S[strtab]; out = []
    for i in range(st['size'] // 24):
        nm, info, other, shndx, val, size = struct.unpack_from('<IBBHQQ', f, st['off'] + i * 24)
        a = ss['off'] + nm
        out.append(dict(name=f[a:f.index(b'\0', a)].decode(errors='replace'), type=info & 15,
                        bind=info >> 4, shndx=shndx, value=val, size=size))
    return out


def insns(f, lo, hi):
    a = lo
    while a < hi:
        n = 16 if f[a] == 0x18 else 8
        yield a, f[a:a + n]; a += n


def printable(b):
    try:
        t = b.decode('utf-8')
    except UnicodeDecodeError:
        return None
    return t if t and all(c.isprintable() or c in '\n\t' for c in t) else None


def ident(t, n=40):
    s = re.sub(r'[^A-Za-z0-9]+', '_', t).strip('_')
    return s[:n] or 'x'


def main():
    elf_path, sym_path, outdir = sys.argv[1:4]
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    f, secs, S = elf(elf_path)
    fu, secu, Su = elf(sym_path)
    with open(out / 'sections.tsv', 'w') as w:
        for s in secs:
            if s['name'] and s['flags'] & 2:  # SHF_ALLOC
                w.write(f"{s['name']}\t{s['addr']:#x}\t{s['size']:#x}\t{s['flags']:#x}\n")
    text = S['.text']; tlo, thi = text['addr'], text['addr'] + text['size']
    # functions: main's unstripped .symtab (same addresses in both files: checked against the original's bytes below)
    syms = symbols(fu, Su, '.symtab', '.strtab')
    funcs = {}
    for s in syms:
        if s['type'] == 2 and s['size'] and tlo <= s['value'] < thi:
            funcs.setdefault(s['value'], (s['size'], s['name']))
    # dynsym names for the entry points (entrypoint, custom_panic) present in both
    dsyms = symbols(f, S, '.dynsym', '.dynstr')
    with open(out / 'funcs.tsv', 'w') as w:
        same = 0
        for a in sorted(funcs):
            size, name = funcs[a]
            body = list(insns(f, a, a + size))
            has_exit = any(b[0] == 0x95 for _, b in body)
            # a function whose body has no `exit` cannot return (it ends in a noreturn call or a loop)
            noret = 0 if has_exit else 1
            same += fu[a:a + size] == f[a:a + size]
            w.write(f"{a:#x}\t{size:#x}\t{noret}\t{demangle(name)}\t{name}\n")
    # syscalls: R_BPF_64_32 against .dynsym
    rel = S['.rel.dyn']; sysc, lddw_sites = [], []
    for i in range(rel['size'] // 16):
        off, info = struct.unpack_from('<QQ', f, rel['off'] + i * 16)
        t, si = info & 0xffffffff, info >> 32
        if t == 10 and tlo <= off < thi:
            sysc.append((off, dsyms[si]['name'], dsyms[si]['value']))
        elif t == 8 and tlo <= off < thi and f[off] == 0x18:
            lo, = struct.unpack_from('<I', f, off + 4); hi, = struct.unpack_from('<I', f, off + 12)
            lddw_sites.append((off, (hi << 32) | lo))
    with open(out / 'syscalls.tsv', 'w') as w:
        for off, n, v in sysc:  # v != 0: a defined function reached through the relocation (custom_panic)
            w.write(f"{off:#x}\t{n}\t{v:#x}\n")
    # data objects: sized OBJECT symbols in main's .rodata/.data.rel.ro (shared .rodata is byte-identical in both
    # files apart from the tail; only objects whose bytes agree are used for the original)
    ro = [S['.rodata'], S['.data.rel.ro']]
    def in_ro(a):
        return any(s['addr'] <= a < s['addr'] + s['size'] for s in ro)
    objs = {}
    for s in syms:
        if s['type'] == 1 and s['size'] and in_ro(s['value']):
            a, n = s['value'], s['size']
            if fu[a:a + n] == f[a:a + n]:
                objs.setdefault(a, n)
    data, labels = {}, {}
    def describe(a, n):
        b = f[a:a + n]
        t = printable(b)
        if t is not None and n >= 2:
            return 'str', 's_' + ident(t), t
        if n == 32:
            k = b58(b)
            return 'pubkey', KNOWN.get(k, 'pk_' + k[:10]), k
        return 'bytes', None, b[:48].hex()
    for a, n in objs.items():
        kind, lab, txt = describe(a, n)
        data[a] = (n, kind, lab or f'obj_{a:x}', txt)
    with open(out / 'lddw.tsv', 'w') as w:
        for off, tgt in lddw_sites:
            if tgt in data:
                n, kind, lab, txt = data[tgt]
            elif in_ro(tgt):
                # unsized target (mid-object pointer, e.g. a message slice): show the printable run or 32 bytes
                b = f[tgt:tgt + 64]
                run = b.split(b'\0')[0]
                t = printable(run[:60]) if len(run) >= 3 else None
                v32, = struct.unpack_from('<I', f, tgt)
                if t:
                    n, kind, lab, txt = len(run[:60]), 'str?', 's_' + ident(t), t
                elif tgt % 4 == 0 and v32 < 0x10000:
                    # pooled scalar constant passed by reference, e.g. &PumpError::X (u32 discriminant) to to_string
                    n, kind, lab, txt = 4, 'u32', f'k_u32_{v32}', f'u32 {v32} (= {v32:#x}; next {f[tgt + 4:tgt + 16].hex()})'
                else:
                    k = b58(f[tgt:tgt + 32])
                    n, kind, lab, txt = 32, 'bytes?', KNOWN.get(k, f'DAT_{tgt:x}'), 'b58 ' + k + ' hex ' + f[tgt:tgt + 16].hex()
                data.setdefault(tgt, (n, kind, lab, txt))
            else:
                n, kind, lab, txt = 0, 'imm', '', ''
            if lab:
                labels.setdefault(tgt, f'{lab}_{tgt:x}')
            safe = txt.replace('\t', ' ').replace('\n', '\\n')
            w.write(f"{off:#x}\t{tgt:#x}\t{labels.get(tgt, '')}\t{kind}: {safe[:160]}\n")
    with open(out / 'data.tsv', 'w') as w:
        for a in sorted(data):
            n, kind, lab, txt = data[a]
            safe = txt.replace('\t', ' ').replace('\n', '\\n')
            w.write(f"{a:#x}\t{n}\t{kind}\t{labels.get(a, lab + '_' + format(a, 'x'))}\t{safe[:200]}\n")
    print(f"{elf_path}: {len(funcs)} funcs ({same} byte-identical to the symbol source), {len(sysc)} syscall sites, "
          f"{len(lddw_sites)} lddw sites, {len(data)} data objects -> {out}")


if __name__ == '__main__':
    main()
