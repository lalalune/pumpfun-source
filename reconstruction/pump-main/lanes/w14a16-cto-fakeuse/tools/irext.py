#!/usr/bin/env python3
"""irext.py <m.ll> <out.jsonl> [--mode start|end|calib] [--depth K] [--only V,..] [--jobs N] [--limit N]
LIVE-RANGE-EXTENSION oracle for admin_cto::execute (experiment only; never a source proposal).

For each SSA value V of execute (scalar: iN / ptr; not allocas), and each block B that V's def strictly dominates and
where V is NOT live-in, insert a zero-instruction use  `call void asm sideeffect "", "r"(T V)`  at the start of B
(after phis; --mode end: before B's terminator). That lengthens V's live range over every path def->B without adding
machine instructions. Candidate blocks are the extension frontier (dead successors of blocks where V is live-out or
defined) and blocks up to --depth further successor steps inside V's dominance region.
--mode calib: one variant per V with the asm right after V's last existing non-phi use in its last-use block
(must be byte-identical; anything else is asm perturbation, not extension).
llc only (the m.ll from rx.py is post-opt), score with rx tokens. LLVM 18 has no llvm.fake.use, hence the asm."""
import sys, os, re, json, difflib, tempfile, subprocess, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from irre_lib import mask, orig, split_fn, elf_fn, SDK

TOKRX = re.compile(r'%(?:"[^"]+"|[\w.$-]+)')
LBL = re.compile(r'^("[^"]+"|[\w.$-]+):')
TERM = ('br ', 'switch ', 'ret ', 'ret\n', 'unreachable', 'resume ', 'indirectbr ')


def parse(fn):
    L = fn.split('\n')
    # header args
    hdr = L[0]
    blocks = []  # (name, start_line, end_line_excl)
    cur = None
    for i, l in enumerate(L[1:], 1):
        m = LBL.match(l)
        if m:
            if cur: blocks.append(cur)
            cur = [m.group(1), i, None]
        elif cur is None and l.strip():
            cur = ['%entry', i - 0, None]
    blocks.append(cur)
    for k in range(len(blocks) - 1): blocks[k][2] = blocks[k + 1][1]
    blocks[-1][2] = len(L) - 1
    # instructions per block (join multi-line switch)
    B = {}
    order = []
    for name, a, b in blocks:
        insts = []; j = a + (1 if LBL.match(L[a]) else 0)
        while j < b:
            t = L[j]
            if not t.strip() or t.strip().startswith(';') or t.strip() == '}':
                j += 1; continue
            st = j; txt = t
            if t.strip().startswith('switch ') or ' = switch' in t:
                while not L[j].strip().endswith(']'): j += 1; txt += ' ' + L[j].strip()
            insts.append((st, j, txt)); j += 1
        B[name] = insts; order.append(name)
    return L, hdr, B, order


def ty_of(txt):
    m = re.match(r'^\s*(%(?:"[^"]+"|[\w.$-]+)) = (.*)$', txt)
    if not m: return None, None
    v, r = m.groups()
    r = re.sub(r'^(tail |musttail |notail )', '', r)
    t = None
    mm = re.match(r'^(load|phi|freeze) (?:volatile )?(\S+)', r)
    if mm: t = mm.group(2).rstrip(',')
    elif re.match(r'^(icmp|fcmp) ', r): t = 'i1'
    elif re.match(r'^getelementptr ', r): t = 'ptr'
    elif re.match(r'^(alloca) ', r): return v, None
    elif re.match(r'^(zext|sext|trunc|ptrtoint|inttoptr|bitcast) ', r):
        mm = re.search(r' to (\S+)', r); t = mm.group(1) if mm else None
    elif re.match(r'^select ', r):
        mm = re.match(r'^select (?:\w+ )*i1 [^,]+, (\S+) ', r); t = mm.group(1) if mm else None
    elif re.match(r'^(add|sub|mul|udiv|sdiv|urem|srem|and|or|xor|shl|lshr|ashr)\b', r):
        mm = re.match(r'^\w+(?: (?:nuw|nsw|exact|disjoint))* (\S+) ', r); t = mm.group(1) if mm else None
    elif re.match(r'^call ', r):
        mm = re.match(r'^call (?:[\w()]+ )*?(i\d+|ptr) (?:@|asm)', r); t = mm.group(1) if mm else None
    elif re.match(r'^extractvalue ', r):
        mm = re.match(r'^extractvalue \{ ([^}]*) \} %\S+, (\d+)$', r)
        if mm:
            el = [x.strip() for x in mm.group(1).split(',')]
            k = int(mm.group(2)); t = el[k] if k < len(el) else None
    if t and re.fullmatch(r'i\d+|ptr', t): return v, t
    return v, None


def succs(txt):
    if txt.strip().startswith(('br ', 'switch ')):
        return [x for x in re.findall(r'label (%(?:"[^"]+"|[\w.$-]+))', txt)]
    return []


def analyse(fn):
    L, hdr, B, order = parse(fn)
    names = {n: ('%' + n if not n.startswith('%') else n) for n in order}
    lab2b = {('%' + n if not n.startswith('%') else n): n for n in order}
    S = {n: [lab2b[s] for s in succs(B[n][-1][2])] for n in order}
    P = {n: [] for n in order}
    for n in order:
        for s in S[n]: P[s].append(n)
    # defs and types
    defb = {}; types = {}; defidx = {}
    args = re.findall(r'(i\d+|ptr)\b[^,]*? (%[\w.$-]+)(?=[,)])', hdr[hdr.index('('):])
    for t, v in args: defb[v] = order[0]; types[v] = t; defidx[v] = -1
    for n in order:
        for k, (a, b, txt) in enumerate(B[n]):
            v, t = ty_of(txt)
            if v: defb[v] = n; defidx[v] = k
            if v and t: types[v] = t
    # uses: upward-exposed per block; phi uses go to predecessor end
    vid = {v: i for i, v in enumerate(defb)}
    use = {n: 0 for n in order}; dfs = {n: 0 for n in order}; phiuse = {n: 0 for n in order}
    lastuse = {}  # v -> (block, inst k) of last non-phi use, by block order heuristic
    for n in order:
        for k, (a, b, txt) in enumerate(B[n]):
            m = re.match(r'^\s*(%(?:"[^"]+"|[\w.$-]+)) = phi (\S+) (.*)$', txt)
            if m:
                for val, pr in re.findall(r'\[ ([^,]+), (%[^\s\]]+) \]', m.group(3)):
                    val = val.strip()
                    if val in vid: phiuse[lab2b[pr]] |= 1 << vid[val]
                dfs[n] |= 1 << vid[m.group(1)]
                continue
            dv = re.match(r'^\s*(%(?:"[^"]+"|[\w.$-]+)) = ', txt)
            body = txt[dv.end():] if dv else txt
            for u in set(TOKRX.findall(body)):
                if u in vid:
                    bit = 1 << vid[u]
                    if not (dfs[n] & bit): use[n] |= bit
                    lastuse[u] = (n, k)
            if dv and dv.group(1) in vid: dfs[n] |= 1 << vid[dv.group(1)]
    # liveness
    lin = {n: 0 for n in order}; lout = {n: 0 for n in order}
    ch = True
    while ch:
        ch = False
        for n in reversed(order):
            o = phiuse[n]
            for s in S[n]: o |= lin[s] & ~0  # phi defs of s are in dfs[s], removed from lin[s]
            i = use[n] | (o & ~dfs[n])
            if o != lout[n] or i != lin[n]: lout[n] = o; lin[n] = i; ch = True
    # dominators (iterative, RPO)
    rpo = []; seen = set()
    def dfs_(n):
        st = [(n, iter(S[n]))]; seen.add(n)
        while st:
            x, it = st[-1]
            nx = next(it, None)
            if nx is None: rpo.append(x); st.pop()
            elif nx not in seen: seen.add(nx); st.append((nx, iter(S[nx])))
    dfs_(order[0]); rpo.reverse()
    idx = {n: i for i, n in enumerate(rpo)}
    idom = {rpo[0]: rpo[0]}
    def inter(a, b):
        while a != b:
            while idx[a] > idx[b]: a = idom[a]
            while idx[b] > idx[a]: b = idom[b]
        return a
    ch = True
    while ch:
        ch = False
        for n in rpo[1:]:
            ps = [p for p in P[n] if p in idom]
            nd = ps[0]
            for p in ps[1:]: nd = inter(p, nd)
            if idom.get(n) != nd: idom[n] = nd; ch = True
    def dominates(a, b):
        while True:
            if a == b: return True
            if b == rpo[0]: return False
            b = idom[b]
    return dict(L=L, B=B, order=order, rpo=rpo, S=S, P=P, defb=defb, types=types, vid=vid, lin=lin, lout=lout,
                dfs=dfs, dominates=dominates, lastuse=lastuse, idom=idom)


def skip_value(A, v, txt):
    if v not in A['types']: return True
    # constant-offset GEP of an alloca: frame index, rematerialised
    m = re.search(r'getelementptr (?:inbounds )?(?:nuw )?i8, ptr (%[\w.$-]+), i64 -?\d+$', txt or '')
    if m and m.group(1) in A['defb'] and m.group(1) not in A['types']: return True
    return False


def candidates(A, depth=1, only=None):
    out = []
    B, S = A['B'], A['S']
    deftxt = {}
    for n in A['order']:
        for (a, b, txt) in B[n]:
            m = re.match(r'^\s*(%(?:"[^"]+"|[\w.$-]+)) = ', txt)
            if m: deftxt[m.group(1)] = txt
    for v, i in A['vid'].items():
        if only and v not in only: continue
        if skip_value(A, v, deftxt.get(v)): continue
        bit = 1 << i; d = A['defb'][v]
        # blocks where V is present at end: live-out or (defined here and ... always present at end of def block)
        pres = [n for n in A['order'] if (A['lout'][n] & bit) or n == d or (A['lin'][n] & bit and A['lout'][n] & bit)]
        front = set()
        for p in pres:
            for s in S[p]:
                if not (A['lin'][s] & bit) and s != d and A['dominates'](d, s): front.add(s)
        cand = set(front); lvl = set(front)
        for _ in range(depth - 1):
            nl = set()
            for x in lvl:
                for s in S[x]:
                    if s not in cand and not (A['lin'][s] & bit) and s != d and A['dominates'](d, s): nl.add(s)
            cand |= nl; lvl = nl
        for blk in sorted(cand, key=A['rpo'].index):
            out.append((v, blk, 1 if blk in front else 2))
    return out


def asm(v, t): return '  call void asm sideeffect "", "r"(%s %s)' % (t, v)


def make(A, v, blk, mode):
    L = list(A['L']); t = A['types'][v]
    insts = A['B'][blk]
    if mode == 'end':
        a = insts[-1][0]; L[a] = asm(v, t) + '\n' + L[a]
    else:
        k = 0
        while k < len(insts) and ' = phi ' in insts[k][2]: k += 1
        a = insts[k][0]; L[a] = asm(v, t) + '\n' + L[a]
    return '\n'.join(L)


def make_impl(A, v, blk, op):
    L = list(A['L']); a, b, txt = A['B'][blk][-1]
    m = re.match(r'^(\s*)br i1 (%(?:"[^"]+"|[\w.$-]+)), (.*)$', L[a])
    L[a] = '%s%%fk.x = %s i1 %s, %s\n%sbr i1 %%fk.x, %s' % (m.group(1), op, m.group(2), v, m.group(1), m.group(3))
    return '\n'.join(L)


def make_calib(A, v):
    if v not in A['lastuse']: return None
    blk, k = A['lastuse'][v]; L = list(A['L'])
    a, b, txt = A['B'][blk][k]
    if k == len(A['B'][blk]) - 1:  # terminator: put before it
        L[a] = asm(v, A['types'][v]) + '\n' + L[a]
    else:
        L[b] = L[b] + '\n' + asm(v, A['types'][v])
    return '\n'.join(L)


def run(pre, fn, post, O, d, keep=False):
    os.makedirs(d, exist_ok=True)
    open(d + '/m.ll', 'w').write(pre + fn + post)
    r = subprocess.run([SDK + '/llc', '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections',
                        d + '/m.ll', '-filetype=obj', '-o', d + '/m.o'], capture_output=True, text=True)
    if r.returncode: return {'error': r.stderr[-300:]}
    raw = elf_fn(d + '/m.o'); c = mask(raw)
    res = {'bytes': len(raw)}
    res['_toks'] = c
    if abs(len(raw) - 27400) > int(os.environ.get('IREXT_WIN', '1000000')):
        for f in ('m.ll', 'm.o'):
            try: os.remove(d + '/' + f)
            except OSError: pass
        return res
    rr = difflib.SequenceMatcher(None, O, c, autojunk=False).ratio(); res['ratio'] = round(rr, 5)
    ob = b''.join(O); cb = b''.join(c)
    if len(ob) == len(cb): res['slots'] = sum(1 for q in range(0, len(ob), 8) if ob[q:q + 8] != cb[q:q + 8])
    if keep: open(d + '/fn.bin', 'wb').write(raw); os.replace(d + '/m.o', d + '/keep.o')
    for f in ('m.ll', 'm.o'):
        try: os.remove(d + '/' + f)
        except OSError: pass
    return res


def main():
    a = sys.argv[1:]; m = a.pop(0); outp = a.pop(0); mode = 'start'; depth = 1; only = None; jobs = 6; limit = None
    while a:
        x = a.pop(0)
        if x == '--mode': mode = a.pop(0)
        elif x == '--depth': depth = int(a.pop(0))
        elif x == '--only': only = set(a.pop(0).split(','))
        elif x == '--jobs': jobs = int(a.pop(0))
        elif x == '--limit': limit = int(a.pop(0))
    text = open(m).read(); pre, fn, post = split_fn(text); O = orig()
    A = analyse(fn)
    work = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a16-cto-fakeuse/var/irext/%d' % os.getpid())
    base = run(pre, fn, post, O, work + '/base'); bt = base.pop('_toks')
    if mode == 'calib':
        vs = [(v, None, 0) for v in A['vid'] if v in A['types'] and v in A['lastuse']]
    elif mode == 'calib2':  # asm at start of every block where V is already live-in (no liveness change)
        vs = []
        for v, i in A['vid'].items():
            if v not in A['types'] or (only and v not in only): continue
            for n in A['order']:
                if (A['lin'][n] >> i) & 1 and n != A['defb'][v]: vs.append((v, n, 0))
    elif mode == 'impl':  # real implied use: br i1 %c -> br i1 (and|or %c, V) for i1 V dominating, dead at B
        dead = {n for n in A['order'] if 'unreachable' in A['B'][n][-1][2]}
        vs = []
        for n in A['rpo']:
            if n in dead: continue
            t_ = A['B'][n][-1][2]
            mm = re.match(r'^\s*br i1 (%(?:"[^"]+"|[\w.$-]+)), ', t_)
            if not mm: continue
            for v, i in A['vid'].items():
                if A['types'].get(v) != 'i1' or (only and v not in only) or v == mm.group(1): continue
                d = A['defb'][v]
                if (A['lin'][n] >> i) & 1 or not (d == n or A['dominates'](d, n)): continue
                if d == n:  # must be defined before the terminator: always true for non-terminators
                    pass
                for op in ('and', 'or'): vs.append((v, n, op))
        mode = 'impl'
    elif mode == 'all':  # every dominated dead non-panic block, start mode; --types filter
        types = set(os.environ.get('IREXT_TYPES', 'i1,i8,i32,i64').split(','))
        dead = {n for n in A['order'] if 'unreachable' in A['B'][n][-1][2]}
        deftxt = {}
        for n in A['order']:
            for (a_, b_, t_) in A['B'][n]:
                mm = re.match(r'^\s*(%(?:"[^"]+"|[\w.$-]+)) = ', t_)
                if mm: deftxt[mm.group(1)] = t_
        vs = []
        for v, i in A['vid'].items():
            if (only and v not in only) or skip_value(A, v, deftxt.get(v)) or A['types'][v] not in types: continue
            d = A['defb'][v]
            for n in A['rpo']:
                if n in dead or n == d or (A['lin'][n] >> i) & 1: continue
                if A['dominates'](d, n): vs.append((v, n, 9))
        if os.environ.get('IREXT_CONDONLY'):
            vs = [x for x in vs if A['B'][x[1]][-1][2].strip().startswith(('br i1', 'switch '))]
        mode = os.environ.get('IREXT_POS', 'start')
    else:
        vs = candidates(A, depth, only)
    if limit: vs = vs[:limit]
    print('base', base, 'values', len(A['types']), 'variants', len(vs), flush=True)
    global G
    G = (A, pre, fn, post, O, work, bt, mode)
    with open(outp, 'w') as f, cf.ProcessPoolExecutor(jobs, mp_context=__import__('multiprocessing').get_context('fork')) as ex:
        for r in ex.map(job, vs, chunksize=4):
            r['d'] = round(r['ratio'] - base['ratio'], 5) if 'ratio' in r else None
            if 'ratio' not in r and 'error' not in r: r['d'] = None
            f.write(json.dumps(r) + '\n'); f.flush()
            if r.get('d') and r['d'] > 0 and r.get('bytes') == 27400: print('GAIN', json.dumps(r), flush=True)


G = None


def job(x):
        A, pre, fn, post, O, work, bt, mode = G
        v, blk, lvl = x
        d = work + '/' + re.sub(r'[^\w]', '_', v + '__' + str(blk))
        f2 = make_calib(A, v) if mode == 'calib' else (make_impl(A, v, blk, lvl) if mode == 'impl' else make(A, v, blk, 'start' if mode == 'calib2' else mode))
        r = run(pre, f2, post, O, d)
        same = r.pop('_toks', None) == bt
        r.update({'v': v, 'blk': blk, 'lvl': lvl, 'ty': A['types'][v], 'def': A['defb'][v], 'same': same})
        try: os.rmdir(d)
        except OSError: pass
        return r


if __name__ == '__main__':
    main()
