#!/usr/bin/env python3
"""relaylib.py: sBPF ELF parsing, function boundaries and normalization for the Donation Relay lanes. No JVM."""
import os, re, struct, sys, hashlib, collections, json
JMP = {0x05, 0x15, 0x1d, 0x25, 0x2d, 0x35, 0x3d, 0x45, 0x4d, 0x55, 0x5d, 0x65, 0x6d, 0x75, 0x7d, 0xa5, 0xad, 0xb5, 0xbd, 0xc5, 0xcd, 0xd5, 0xdd,
       0x16, 0x1e, 0x26, 0x2e, 0x36, 0x3e, 0x46, 0x4e, 0x56, 0x5e, 0x66, 0x6e, 0x76, 0x7e, 0xa6, 0xae, 0xb6, 0xbe, 0xc6, 0xce, 0xd6, 0xde}
COND = JMP - {0x05}


class Elf:
    def __init__(self, path):
        self.path = path
        b = self.b = open(path, 'rb').read()
        shoff = struct.unpack_from('<Q', b, 0x28)[0]; shnum = struct.unpack_from('<H', b, 0x3c)[0]; shstr = struct.unpack_from('<H', b, 0x3e)[0]
        self.entry = struct.unpack_from('<Q', b, 0x18)[0]
        S = [struct.unpack_from('<IIQQQQIIQQ', b, shoff + i * 64) for i in range(shnum)]
        names = b[S[shstr][4]:S[shstr][4] + S[shstr][5]]
        self.sec = {}
        for s in S:
            n = names[s[0]:names.index(b'\0', s[0])].decode()
            self.sec[n] = dict(addr=s[3], off=s[4], size=s[5], link=s[6], ent=s[9], flags=s[2])
        t = self.sec['.text']; self.ta, self.tn = t['addr'], t['size']; self.text = b[t['off']:t['off'] + t['size']]
        self.sys = {}; self.rel = set(); self.relinfo = {}
        r = self.sec.get('.rel.dyn'); ds = self.sec.get('.dynsym'); dn = self.sec.get('.dynstr')
        if r:
            for i in range(r['size'] // 16):
                off, info = struct.unpack_from('<QQ', b, r['off'] + i * 16)
                ty = info & 0xffffffff
                self.relinfo[off] = info
                if ty == 10 and ds:
                    si = info >> 32; n = struct.unpack_from('<I', b, ds['off'] + si * 24)[0]
                    self.sys[off] = b[dn['off'] + n:b.index(b'\0', dn['off'] + n)].decode()
                elif ty == 8:
                    self.rel.add(off)
        self._ins = None

    def ptr(self, off):
        """Relocated pointer stored in .data.rel.ro: this linker writes the address in the high 4 bytes of the word."""
        d = self.sec['.data.rel.ro']
        lo, hi = struct.unpack_from('<II', self.b, d['off'] + off - d['addr'])
        return hi if lo == 0 else lo | hi << 32

    def section_bytes(self, name):
        s = self.sec[name]
        return self.b[s['off']:s['off'] + s['size']]

    def insns(self):
        if self._ins is None:
            i = 0; out = []; t = self.text
            while i < len(t):
                op = t[i]; n = 16 if op == 0x18 else 8
                out.append((self.ta + i, op, t[i + 1], struct.unpack_from('<h', t, i + 2)[0], struct.unpack_from('<i', t, i + 4)[0], n))
                i += n
            self._ins = out
        return self._ins

    def lddw(self, a):
        o = a - self.ta
        return struct.unpack_from('<I', self.text, o + 4)[0] | struct.unpack_from('<I', self.text, o + 12)[0] << 32

    def call_target(self, a, imm):
        return a + 8 + imm * 8

    def functions(self):
        """Function starts: entry, internal call targets, relocated text pointers, lddw immediates into .text, instruction after
        exit/ja that nothing jumps to, instruction after a call to a noreturn function that nothing jumps to. Returns sorted [(addr,size)]."""
        ins = self.insns(); ta, tn = self.ta, self.tn
        starts = {ta, self.entry}; jt = set(); idx = {x[0]: k for k, x in enumerate(ins)}
        for a, op, regs, o, imm, n in ins:
            if op == 0x85 and (regs >> 4) == 1 and a not in self.sys:
                starts.add(a + 8 + imm * 8)
            elif op in JMP:
                jt.add(a + 8 + o * 8)
            elif op == 0x18:
                v = self.lddw(a)
                if ta <= v < ta + tn:
                    starts.add(v)
        d = self.sec.get('.data.rel.ro')
        if d:
            for off in self.rel:
                if d['addr'] <= off < d['addr'] + d['size']:
                    v = self.ptr(off)
                    if ta <= v < ta + tn:
                        starts.add(v)
        prev = None
        for a, op, regs, o, imm, n in ins:
            if prev is not None and prev in (0x95, 0x05) and a not in jt:
                starts.add(a)
            prev = op
        starts = {s for s in starts if ta <= s < ta + tn}
        # iterate: functions that cannot reach exit are noreturn; the instruction after a call to one is a new function when nothing jumps to it
        for _round in range(8):
            sl = sorted(starts); nr = self._noreturn(sl, jt, idx)
            added = 0
            for k, (a, op, regs, o, imm, n) in enumerate(ins[:-1]):
                if op != 0x85:
                    continue
                nx = ins[k + 1][0]
                if nx in jt or nx in starts or ins[k + 1][1] == 0x95:
                    continue
                if (a in self.sys and self.sys[a] in ('abort', 'sol_panic_')) or (a not in self.sys and (regs >> 4) == 1 and (a + 8 + imm * 8) in nr):
                    starts.add(nx); added += 1
            if not added:
                break
        sl = sorted(starts); ends = sl[1:] + [ta + tn]
        return [(s, e - s) for s, e in zip(sl, ends)]

    def _noreturn(self, sl, jt, idx):
        """Fixed point: a function is noreturn when no path from its entry reaches exit (following jumps, stopping at noreturn calls)."""
        ins = self.insns(); ends = dict(zip(sl, sl[1:] + [self.ta + self.tn])); nr = set()
        changed = True
        while changed:
            changed = False
            for s in sl:
                if s in nr:
                    continue
                seen = set(); st = [s]; ok = False; e = ends[s]
                while st and not ok:
                    a = st.pop()
                    if a in seen or not (s <= a < e) or a not in idx:
                        continue
                    seen.add(a)
                    _, op, regs, o, imm, n = ins[idx[a]]
                    if op == 0x95:
                        ok = True
                    elif op == 0x05:
                        st.append(a + 8 + o * 8)
                    elif op in COND:
                        st.append(a + 8 + o * 8); st.append(a + n)
                    elif op == 0x85 and ((a in self.sys and self.sys[a] in ('abort', 'sol_panic_')) or (a not in self.sys and (regs >> 4) == 1 and (a + 8 + imm * 8) in nr)):
                        pass
                    else:
                        st.append(a + n)
                if not ok:
                    nr.add(s); changed = True
        return nr

    def norm(self, start, size):
        """Scorer normalization: internal call imm and relocated lddw values masked; syscall sites hashed by name. Jump offsets stay.
        Returns (bytes, internal call target list, syscall names, relocated lddw values)."""
        t = self.text; i = start - self.ta; end = i + size; out = bytearray(); calls = []; sysc = []; lds = []
        while i < end:
            op = t[i]; n = 16 if op == 0x18 else 8; a = self.ta + i; raw = bytearray(t[i:i + n])
            if op == 0x85:
                if a in self.sys:
                    raw[1] = 0x10; raw[4:8] = hashlib.sha1(self.sys[a].encode()).digest()[:4]; sysc.append(self.sys[a])
                elif (t[i + 1] >> 4) == 1:
                    raw[4:8] = b'\0\0\0\0'; calls.append(a + 8 + struct.unpack_from('<i', t, i + 4)[0] * 8)
            elif op == 0x18 and a in self.rel:
                lds.append(struct.unpack_from('<I', t, i + 4)[0] | struct.unpack_from('<I', t, i + 12)[0] << 32)
                raw[4:8] = b'\0\0\0\0'; raw[12:16] = b'\0\0\0\0'
            out += raw; i += n
        return bytes(out), calls, sysc, lds


def symbols(path):
    e = Elf(path); b = e.b
    s = e.sec.get('.symtab'); out = {}
    if not s:
        return out
    st = e.sec['.strtab']
    for i in range(s['size'] // 24):
        nm, info, oth, shn, val, sz = struct.unpack_from('<IBBHQQ', b, s['off'] + i * 24)
        if info & 0xf == 2 and sz:
            out[val] = (sz, b[st['off'] + nm:b.index(b'\0', st['off'] + nm)].decode())
    return out


def demangle(s):
    m = re.match(r'^_ZN(.*)E$', s)
    if not m:
        return s
    rest, parts = m.group(1), []
    while rest and rest[0].isdigit():
        n = re.match(r'^(\d+)', rest).group(1); rest = rest[len(n):]
        part = rest[:int(n)]; parts.append(part[1:] if part.startswith('_$') else part); rest = rest[int(n):]
    if parts and re.fullmatch(r'h[0-9a-f]{16}', parts[-1]):
        parts = parts[:-1]
    t = '::'.join(parts)
    for a, c in [('$LT$', '<'), ('$GT$', '>'), ('$RF$', '&'), ('$BP$', '*'), ('$C$', ','), ('$u20$', ' '), ('$u27$', "'"), ('$u5b$', '['), ('$u5d$', ']'),
                 ('$u7b$', '{'), ('$u7d$', '}'), ('$u3b$', ';'), ('$u2b$', '+'), ('$u22$', '"'), ('$LP$', '('), ('$RP$', ')'), ('..', '::'), ('$u7e$', '~')]:
        t = t.replace(a, c)
    return t


def toks(nb):
    out = []; i = 0
    while i < len(nb):
        n = 16 if nb[i] == 0x18 else 8
        out.append(bytes(nb[i:i + n])); i += n
    return out
