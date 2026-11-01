#!/usr/bin/env python3
"""relay.py: per-function comparison of a Donation Relay candidate with the live deployed ELF. No JVM, no build.

  relay.py measure <unstripped.so> [--json out.json] [--baseline functions.json]   one JSON line, per-function table in --json
  relay.py list    <unstripped.so> [--unmatched] [--re REGEX]                      target table with match status and names
  relay.py diff    <unstripped.so> <target_addr> [--sym REGEX | --caddr ADDR] [-c N] [--full] [--mask jumps,frame,regs]
  relay.py fn      <target_addr> [--cand unstripped.so] [--caddr ADDR]             annotated disassembly of one function
  relay.py sym     <unstripped.so> REGEX                                           candidate symbols (addr, size, name)

Normalization is the scorer's: internal call immediates and relocated lddw values are masked, syscall sites are named, and jump
offsets, frame offsets, registers and other immediates (line numbers!) stay. `strict` additionally resolves what the masked operands
point at: callee identity through the matched pairs, and rodata/.data.rel.ro contents (strings, Location line/col).
"""
import argparse, bisect, collections, difflib, hashlib, json, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relaylib import Elf, symbols, demangle, toks, JMP

R = os.path.expanduser('~/.cache/pumpfun-reconstruction/relay')
TARGET = os.environ.get('RELAY_TARGET', R + '/live/deployed.elf')
DELTA = R + '/DELTA.json'
TABLE_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'target-table.json')


def target_table(t):
    sha = hashlib.sha256(t.b).hexdigest()
    try:
        d = json.load(open(TABLE_CACHE))
        if d['sha256'] == sha:
            return [tuple(x) for x in d['functions']]
    except Exception:
        pass
    f = t.functions()
    try:
        json.dump({'sha256': sha, 'functions': f}, open(TABLE_CACHE, 'w'))
    except OSError:
        pass
    return f


def delta_names():
    try:
        return {int(r['addr'], 16): r for r in json.load(open(DELTA))['functions']}
    except Exception:
        return {}


class Ro:
    """Resolve a pointer value into its section content, bounded by the next referenced address."""

    def __init__(self, e):
        self.e = e; refs = set()
        for a, op, regs, o, imm, n in e.insns():
            if op == 0x18 and a in e.rel:
                refs.add(e.lddw(a))
        d = e.sec.get('.data.rel.ro')
        self.d = d
        if d:
            for off in e.rel:
                if d['addr'] <= off < d['addr'] + d['size']:
                    refs.add(e.ptr(off))
        self.ro = e.sec.get('.rodata'); self.refs = sorted(refs)

    def where(self, v):
        for k, s in (('ro', self.ro), ('d', self.d)):
            if s and s['addr'] <= v < s['addr'] + s['size']:
                return k
        return None

    def span(self, v, maxn=4096):
        k = self.where(v)
        if k is None:
            return b''
        s = self.ro if k == 'ro' else self.d
        j = bisect.bisect_right(self.refs, v)
        end = self.refs[j] if j < len(self.refs) else s['addr'] + s['size']
        end = min(end, s['addr'] + s['size'], v + maxn)
        return self.e.b[s['off'] + v - s['addr']:s['off'] + end - s['addr']]

    def text(self, v, maxn=64):
        b = self.span(v, maxn)
        m = re.match(rb'[\x20-\x7e]{2,}', b)
        return m.group().decode() if m else None


def content_equal(ta, va, tc, vc, depth=0):
    """True when the data at va (target) and vc (candidate) agree, comparing relocated words by what they point at."""
    ka, kc = ta.where(va), tc.where(vc)
    if ka != kc:
        return False
    if ka is None:
        return True
    a = ta.span(va);
    if ka == 'ro':
        b = tc.e.b[tc.ro['off'] + vc - tc.ro['addr']:tc.ro['off'] + vc - tc.ro['addr'] + len(a)]
        return a == b
    # .data.rel.ro: 8 B words, a relocated word is compared by content
    sc = tc.d; o = 0
    b = tc.e.b[sc['off'] + vc - sc['addr']:sc['off'] + vc - sc['addr'] + len(a)]
    if len(b) != len(a):
        return False
    while o < len(a):
        wa = a[o:o + 8]; wb = b[o:o + 8]
        ra, rb = (va + o) in ta.e.rel, (vc + o) in tc.e.rel
        if ra != rb:
            return False
        if ra and len(wa) == 8:
            pa, pb = ta.e.ptr(va + o), tc.e.ptr(vc + o)
            if depth < 1 and ta.where(pa) == 'ro' and not content_equal(ta, pa, tc, pb, depth + 1):
                return False
            if ta.where(pa) is None and tc.where(pb) is not None:
                return False
        elif wa != wb:
            return False
        o += 8
    return True


def compare(cand_path):
    t = Elf(TARGET); c = Elf(cand_path); sy = symbols(cand_path)
    if not sy:
        raise SystemExit('candidate has no symbols: pass the unstripped ELF')
    tf = target_table(t)
    cn = {a: c.norm(a, s[0]) for a, s in sy.items()}
    idx = collections.defaultdict(list)
    for a, s in sorted(sy.items()):
        idx[(s[0], hashlib.sha1(cn[a][0]).digest())].append(a)
    tn = {a: t.norm(a, sz) for a, sz in tf}
    pair = {}; used = collections.Counter()
    # same address first, so a matched layout pairs exact duplicates with themselves
    for a, sz in tf:
        k = (sz, hashlib.sha1(tn[a][0]).digest())
        if a in idx.get(k, ()):
            pair[a] = a; used[a] += 1
    for a, sz in tf:
        if a in pair:
            continue
        k = (sz, hashlib.sha1(tn[a][0]).digest())
        free = [x for x in idx.get(k, ()) if not used[x]]
        if free:
            pair[a] = free[0]; used[free[0]] += 1
    return t, c, sy, tf, tn, cn, pair, idx


def measure(cand_path, json_path=None, baseline=None):
    t, c, sy, tf, tn, cn, pair, idx = compare(cand_path)
    rt, rc = Ro(t), Ro(c)
    rows = []; names = delta_names()
    strict_bad = {}
    for a, sz in tf:
        b = pair.get(a)
        if b is None:
            continue
        why = []
        ca, cb = tn[a][1], cn[b][1]
        for x, y in zip(ca, cb):
            if x in pair and pair[x] != y:
                why.append(f'call {x:#x}->{y:#x}')
                break
        if tn[a][2] != cn[b][2]:
            why.append('syscall order')
        for x, y in zip(tn[a][3], cn[b][3]):
            if not content_equal(rt, x, rc, y):
                why.append(f'data {x:#x}/{y:#x} {rt.text(x, 40)!r}')
                break
        if why:
            strict_bad[a] = why
    matched = sum(1 for a, _ in tf if a in pair); mb = sum(s for a, s in tf if a in pair)
    same_addr = sum(1 for a, _ in tf if pair.get(a) == a)
    raw_same = sum(1 for a, s in tf if a in sy and c.b[c.sec['.text']['off'] + a - c.ta:c.sec['.text']['off'] + a - c.ta + s] == t.text[a - t.ta:a - t.ta + s])
    for a, sz in tf:
        b = pair.get(a); n = names.get(a, {})
        rows.append({'addr': hex(a), 'size': sz, 'match': b is not None, 'cand': hex(b) if b is not None else None,
                     'sym': demangle(sy[b][1]) if b is not None else None, 'strict': (a not in strict_bad) if b is not None else None,
                     'why': strict_bad.get(a), 'name': n.get('name'), 'cluster': n.get('cluster')})
    extra = [(a, sy[a][0], demangle(sy[a][1])) for a in sy if a not in set(pair.values())]
    extra.sort(key=lambda x: -x[1])
    secs = {}
    for s in ('.text', '.rodata', '.data.rel.ro', '.dynsym', '.dynstr', '.rel.dyn'):
        st, sc = t.sec.get(s), c.sec.get(s)
        secs[s] = {'target': st['size'] if st else None, 'cand': sc['size'] if sc else None,
                   'equal': bool(st and sc and t.b[st['off']:st['off'] + st['size']] == c.b[sc['off']:sc['off'] + sc['size']])}
    gains = losses = None
    if baseline and os.path.exists(baseline):
        b0 = {r['addr'] for r in json.load(open(baseline))['functions'] if r['match']}
        now = {r['addr'] for r in rows if r['match']}
        gains, losses = sorted(now - b0, key=lambda x: int(x, 16)), sorted(b0 - now, key=lambda x: int(x, 16))
    un = sorted((r for r in rows if not r['match']), key=lambda r: -r['size'])
    res = {'ok': True, 'functions_total': len(tf), 'functions_matched': matched, 'bytes_total': sum(s for _, s in tf), 'bytes_matched': mb,
           'ratio': round(mb / max(1, sum(s for _, s in tf)), 5), 'strict_matched': matched - len(strict_bad),
           'same_address': same_addr, 'raw_same_address': raw_same, 'candidate_extra_functions': len(extra), 'candidate_extra_bytes': sum(x[1] for x in extra),
           'sections': secs, 'gains': gains, 'losses': losses,
           'unmatched_top': [[r['addr'], r['size'], r['name'] or '?'] for r in un[:12]],
           'extra_top': [[hex(x[0]), x[1], x[2][:80]] for x in extra[:8]]}
    if json_path:
        json.dump({'summary': res, 'functions': rows, 'extra': [{'addr': hex(a), 'size': s, 'name': n} for a, s, n in extra]}, open(json_path, 'w'), indent=0)
    return res


REG = lambda r: 'r%d' % r
ALU = {0x0: 'add', 0x1: 'sub', 0x2: 'mul', 0x3: 'div', 0x4: 'or', 0x5: 'and', 0x6: 'lsh', 0x7: 'rsh', 0x8: 'neg', 0x9: 'mod', 0xa: 'xor', 0xb: 'mov', 0xc: 'arsh', 0xd: 'end'}
J = {0x1: 'jeq', 0x2: 'jgt', 0x3: 'jge', 0x4: 'jset', 0x5: 'jne', 0x6: 'jsgt', 0x7: 'jsge', 0xa: 'jlt', 0xb: 'jle', 0xc: 'jslt', 0xd: 'jsle'}
SZ = {0x18: 'dw', 0x00: 'w', 0x08: 'h', 0x10: 'b'}


def fmt(op, regs, off, imm, a, e, start, namer=None, ro=None):
    d, s = regs & 15, regs >> 4; cl = op & 7; sign = lambda v: ('+%#x' % v) if v >= 0 else ('-%#x' % -v)
    if op == 0x18:
        v = e.lddw(a); note = ''
        if a in e.rel:
            tx = ro.text(v) if ro else None
            note = '  ; ' + (repr(tx) if tx else ('data %#x' % v))
        return 'lddw r%d, %#x%s' % (d, v, note)
    if cl in (4, 7):
        nm = ALU.get(op >> 4, 'alu?%x' % op); w = '64' if cl == 7 else '32'
        if op >> 4 == 0xd:
            return 'be%d r%d' % (imm, d)
        if op >> 4 == 8:
            return 'neg%s r%d' % (w, d)
        return '%s%s r%d, %s' % (nm, w, d, ('r%d' % s) if op & 8 else (hex(imm) if imm >= 0 else '-' + hex(-imm)))
    if op == 0x95:
        return 'exit'
    if op == 0x85:
        if a in e.sys:
            return 'syscall ' + e.sys[a]
        if s == 1:
            tg = a + 8 + imm * 8
            return 'call %s' % (namer(tg) if namer else hex(tg))
        return 'call imm %#x' % imm
    if op == 0x8d:
        return 'callx r%d' % (imm if imm else s)
    if op == 0x05:
        return 'ja %s' % hex(a + 8 + off * 8 - start)
    if cl == 5:
        nm = J.get(op >> 4, 'j?%x' % op)
        return '%s r%d, %s, %s' % (nm, d, ('r%d' % s) if op & 8 else (hex(imm) if imm >= 0 else '-' + hex(-imm)), hex(a + 8 + off * 8 - start))
    if cl == 1:
        return 'ldx%s r%d, [r%d%s]' % (SZ.get(op & 0x18, '?'), d, s, sign(off))
    if cl == 3:
        return 'stx%s [r%d%s], r%d' % (SZ.get(op & 0x18, '?'), d, sign(off), s)
    if cl == 2:
        return 'st%s [r%d%s], %s' % (SZ.get(op & 0x18, '?'), d, sign(off), hex(imm) if imm >= 0 else '-' + hex(-imm))
    return 'op%02x r%d r%d %d %d' % (op, d, s, off, imm)


def listing(e, start, size, namer=None, ro=None):
    t = e.text; i = start - e.ta; end = i + size; out = []
    while i < end:
        op = t[i]; n = 16 if op == 0x18 else 8; a = e.ta + i
        regs = t[i + 1]; off = struct.unpack_from('<h', t, i + 2)[0]; imm = struct.unpack_from('<i', t, i + 4)[0]
        out.append((a - start, fmt(op, regs, off, imm, a, e, start, namer, ro)))
        i += n
    return out


def masked_tokens(e, start, size, mask):
    nb = e.norm(start, size)[0]; out = []
    for tk in toks(nb):
        b = bytearray(tk); op = b[0]
        if 'jumps' in mask and op in JMP:
            b[2:4] = b'\0\0'
        if 'frame' in mask and (op & 7) in (1, 2, 3):
            base = (b[1] >> 4) if (op & 7) == 1 else (b[1] & 15)
            if base == 10:
                b[2:4] = b'\0\0'
        if 'regs' in mask:
            b[1] = 0
        out.append(bytes(b))
    return out


def best_candidates(t, c, sy, a, sz, exclude=(), top=3):
    ta = masked_tokens(t, a, sz, ())
    ops = [x[:2] for x in ta]; g = {tuple(ops[i:i + 5]) for i in range(max(0, len(ops) - 4))} or {tuple(ops)}
    sc = []
    for b, (s, n) in sy.items():
        if b in exclude or not (0.3 * sz <= s <= 3 * sz):
            continue
        tb = masked_tokens(c, b, s, ())
        o2 = [x[:2] for x in tb]; g2 = {tuple(o2[i:i + 5]) for i in range(max(0, len(o2) - 4))} or {tuple(o2)}
        j = len(g & g2) / max(1, len(g | g2))
        sc.append((j, b))
    sc.sort(reverse=True)
    res = []
    for j, b in sc[:12]:
        tb = masked_tokens(c, b, sy[b][0], ())
        res.append((difflib.SequenceMatcher(None, ta, tb, autojunk=False).ratio(), b))
    res.sort(reverse=True)
    return res[:top]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    m = sp.add_parser('measure'); m.add_argument('cand'); m.add_argument('--json'); m.add_argument('--baseline')
    li = sp.add_parser('list'); li.add_argument('cand'); li.add_argument('--unmatched', action='store_true'); li.add_argument('--re')
    d = sp.add_parser('diff'); d.add_argument('cand'); d.add_argument('addr'); d.add_argument('--sym'); d.add_argument('--caddr'); d.add_argument('-c', type=int, default=3); d.add_argument('--full', action='store_true'); d.add_argument('--mask', default='')
    f = sp.add_parser('fn'); f.add_argument('addr'); f.add_argument('--cand'); f.add_argument('--caddr')
    s = sp.add_parser('sym'); s.add_argument('cand'); s.add_argument('regex')
    a = ap.parse_args()
    names = delta_names()
    if a.cmd == 'measure':
        print(json.dumps(measure(a.cand, a.json, a.baseline)))
    elif a.cmd == 'list':
        t, c, sy, tf, tn, cn, pair, idx = compare(a.cand)
        for x, sz in tf:
            b = pair.get(x); nm = demangle(sy[b][1]) if b is not None else (names.get(x, {}).get('name') or '?')
            if a.unmatched and b is not None:
                continue
            if a.re and not re.search(a.re, nm):
                continue
            print(f"{x:#8x} {sz:6d} {'M' if b is not None else '-'} {b if b is None else hex(b)} {nm[:140]}")
    elif a.cmd == 'sym':
        for x, (sz, n) in sorted(symbols(a.cand).items()):
            dn = demangle(n)
            if re.search(a.regex, dn):
                print(f'{x:#8x} {sz:6d} {dn}')
    elif a.cmd == 'fn':
        t = Elf(TARGET); tf = dict(target_table(t)); rt = Ro(t)
        if a.cand and a.caddr:
            c = Elf(a.cand); sy = symbols(a.cand); x = int(a.caddr, 16)
            nm = lambda v: demangle(sy[v][1])[:70] if v in sy else hex(v)
            print(f'{x:#x} size {sy[x][0]} {demangle(sy[x][1])}')
            for o, tx in listing(c, x, sy[x][0], nm, Ro(c)):
                print(f'{o:#7x}  {tx}')
            return
        x = int(a.addr, 16)
        nm = lambda v: f"{v:#x} {(names.get(v, {}).get('name') or '?')[:70]}"
        print(f"{x:#x} size {tf[x]} {names.get(x, {}).get('name') or '?'}")
        for o, tx in listing(t, x, tf[x], nm, rt):
            print(f'{o:#7x}  {tx}')
    elif a.cmd == 'diff':
        t, c, sy, tf, tn, cn, pair, idx = compare(a.cand); x = int(a.addr, 16); tfd = dict(tf); sz = tfd[x]
        mask = tuple(y for y in a.mask.split(',') if y)
        if a.caddr:
            b = int(a.caddr, 16)
        elif a.sym:
            ms = [v for v, (s0, n) in sy.items() if re.search(a.sym, demangle(n))]
            if not ms:
                raise SystemExit('no candidate symbol matches ' + a.sym)
            tt = masked_tokens(t, x, sz, mask)
            b = max(ms, key=lambda v: difflib.SequenceMatcher(None, tt, masked_tokens(c, v, sy[v][0], mask), autojunk=False).ratio())
        elif x in pair:
            b = pair[x]
        else:
            r = best_candidates(t, c, sy, x, sz, exclude=set(pair.values()))
            r2 = best_candidates(t, c, sy, x, sz) if not r or r[0][0] < 0.5 else []
            r = sorted(r + r2, reverse=True)
            print('best candidates:', [(round(q, 3), hex(v), demangle(sy[v][1])[:60]) for q, v in r[:3]])
            if not r:
                raise SystemExit('no similar candidate function')
            b = r[0][1]
        tt, tc = masked_tokens(t, x, sz, mask), masked_tokens(c, b, sy[b][0], mask)
        rt, rc = Ro(t), Ro(c)
        la = listing(t, x, sz, lambda v: (names.get(v, {}).get('name') or hex(v))[:64], rt)
        lb = listing(c, b, sy[b][0], lambda v: (demangle(sy[v][1])[:64] if v in sy else hex(v)), rc)
        sm = difflib.SequenceMatcher(None, tt, tc, autojunk=False)
        print(f"target {x:#x} size {sz} tokens {len(tt)} | cand {b:#x} size {sy[b][0]} tokens {len(tc)} {demangle(sy[b][1])[:80]} | ratio {sm.ratio():.4f} matching {sum(m.size for m in sm.get_matching_blocks())}")
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                if a.full:
                    for k in range(i2 - i1):
                        print(f'  {la[i1 + k][0]:#7x} {lb[j1 + k][0]:#7x}  {la[i1 + k][1]}')
                elif a.c:
                    n = i2 - i1
                    if n <= 2 * a.c:
                        rng = range(n)
                    else:
                        rng = list(range(a.c)) + [-1] + list(range(n - a.c, n))
                    for k in rng:
                        if k == -1:
                            print('      ...')
                        else:
                            print(f'  {la[i1 + k][0]:#7x} {lb[j1 + k][0]:#7x}  {la[i1 + k][1]}')
                continue
            for k in range(i1, i2):
                print(f'- {la[k][0]:#7x}          {la[k][1]}')
            for k in range(j1, j2):
                print(f'+         {lb[k][0]:#7x}  {lb[k][1]}')


if __name__ == '__main__':
    main()
