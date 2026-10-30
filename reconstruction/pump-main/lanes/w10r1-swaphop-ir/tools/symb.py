#!/usr/bin/env python3
"""symb.py (orig|NAME) [--at 0xoff..] : abstract-interpret swap_hop asm; annotate each insn with symbolic reg values.
Values: 'a','h','sret','sa','ev' args; L(x,off) loads from non-frame memory; x+k; slots via r10."""
import re, sys, os, collections
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-ir')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def load_insns(name):
    if name == 'orig':
        out = []
        for l in open(O + '/orig.dis'):
            m = re.match(r'(0x[0-9a-f]+)\s+(.*)', l)
            if m: out.append((int(m.group(1), 16) - 0x5b3b0, m.group(2).strip()))
        return out
    import odiff_lib
    return odiff_lib.cand(name)
def load_named(name):
    import odiff_lib
    return odiff_lib.orig() if name == 'orig' else odiff_lib.cand(name)
def parse(s):
    m = re.match(r'(\w+)\s*(.*)', s); return m.group(1), [x.strip() for x in m.group(2).split(',')] if m.group(2) else []
def target(off, op, args):
    if op == 'ja' or op.startswith('j'):
        j = args[-1]; return off + 8 + int(j, 16) * 8 if j.startswith(('+', '-')) else None
def ldsz(op): return {'ldxdw': 8, 'ldxw': 4, 'ldxh': 2, 'ldxb': 1}.get(op)
def analyze(ins):
    idx = {o: i for i, (o, _) in enumerate(ins)}
    P = [parse(s) for _, s in ins]
    succ = []
    for i, (o, s) in enumerate(ins):
        op, a = P[i]; n = []
        if op == 'exit': pass
        elif op == 'ja': n = [idx[target(o, op, a)]]
        elif op.startswith('j'): n = [i + 1, idx[target(o, op, a)]]
        else: n = [i + 1] if i + 1 < len(ins) else []
        succ.append(n)
    init = {'r1': 'sret', 'r2': 'a', 'r3': 'ev', 'r4': 'h', 'r5': 'sa'}
    st = [None] * len(ins); st[0] = dict(init)
    def val(S, x):
        if re.match(r'^-?0x[0-9a-f]+$|^-?\d+$', x): return '#' + str(int(x, 0))
        return S.get(x, '?')
    def addk(v, k):
        if re.match(r'^#-?\d+$', v): return '#' + str(int(v[1:]) + k)
        if v.startswith('#'): return '?'
        m = re.match(r'^(.*)\+(-?\d+)$', v)
        if m: b, kk = m.group(1), int(m.group(2)) + k; return b if kk == 0 else f'{b}+{kk}'
        return v if k == 0 else f'{v}+{k}'
    def fr(v):  # frame slot?
        m = re.match(r'^fp([+-]\d+)?$', v); return (int(m.group(1) or 0)) if m else None
    work = [0]; seen = collections.Counter()
    while work:
        i = work.pop(); S = dict(st[i]); op, a = P[i]
        if op in ('mov64', 'mov32'):
            S[a[0]] = 'fp' if a[1] == 'r10' else val(S, a[1])
        elif op == 'add64':
            v = S.get(a[0], '?'); w = val(S, a[1])
            if re.match(r'^#-?\d+$', w) and v != '?': S[a[0]] = addk(v, int(w[1:])) if not v.startswith('fp') else f'fp{(fr(v) or 0) + int(w[1:]):+d}'
            else: S[a[0]] = f'({v})+({w})' if v != '?' and w != '?' else '?'
        elif ldsz(op):
            m = re.match(r'\[(r\d+) ([+-]) (0x[0-9a-f]+)\]', a[1]); base = m.group(1); off = int(m.group(3), 16) * (1 if m.group(2) == '+' else -1)
            bv = 'fp' if base == 'r10' else S.get(base, '?')
            if fr(bv) is not None: S[a[0]] = S.get(f'[{fr(bv)+off}]', '?')
            elif bv == '?': S[a[0]] = '?'
            else: S[a[0]] = f'L({bv},{off})' if ldsz(op) == 8 else f'L{ldsz(op)}({bv},{off})'
        elif op.startswith('stx') or op.startswith('st'):
            m = re.match(r'\[(r\d+) ([+-]) (0x[0-9a-f]+)\]', a[0]); base = m.group(1); off = int(m.group(3), 16) * (1 if m.group(2) == '+' else -1)
            bv = 'fp' if base == 'r10' else S.get(base, '?')
            if fr(bv) is not None and op in ('stxdw', 'stdw'):
                S[f'[{fr(bv)+off}]'] = val(S, a[1])
        elif op == 'call' and False:
            for r in ('r0', 'r1', 'r2', 'r3', 'r4', 'r5'): S[r] = '?'
            S['r0'] = f'ret@{ins[i][0]:#x}'
        elif op == 'call':
            for r in ('r0', 'r1', 'r2', 'r3', 'r4', 'r5'): S[r] = '?'
            S['r0'] = f'ret@{ins[i][0]:#x}'
        elif op == 'lddw': S[a[0]] = '#lddw'
        elif op in ('exit',) or op.startswith('j'): pass
        else:
            if a: S[a[0]] = '?'
        for n in succ[i]:
            if st[n] is None: st[n] = S; work.append(n)
            else:
                old = st[n]; new = {k: v for k, v in old.items() if S.get(k) == v}
                if len(new) != len(old):
                    st[n] = new; seen[n] += 1
                    if seen[n] < 50: work.append(n)
    return ins, P, st
if __name__ == '__main__':
    name = sys.argv[1]; lo, hi = (int(x, 0) for x in sys.argv[2].split('..')) if len(sys.argv) > 2 else (0, 1 << 30)
    ins, P, st = analyze(load_named(name))
    for i, (o, s) in enumerate(ins):
        if not lo <= o <= hi: continue
        S = st[i] or {}
        op, a = P[i]
        regs = sorted(set(re.findall(r'r\d+', s)) - {'r10'})
        ann = ' '.join(f'{r}={S.get(r,"?")}' for r in regs)
        print(f'{o:#06x}  {s:<34} ; {ann}')
