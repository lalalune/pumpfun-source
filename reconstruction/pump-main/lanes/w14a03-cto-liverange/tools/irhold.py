#!/usr/bin/env python3
"""irhold.py <m.ll> <out.jsonl> [--jobs N]: hold oracle (experiment only), the inverse of irre.py.

For every pair of loads (L1, L2) of the same pointer SSA value and type where L1's block strictly dominates L2's
block, replace L2 by L1 (source analogue: bind the field once and hold the local instead of reading it again).
Also a per-pointer 'all' variant (every dominated reload of that pointer folded into its dominating first load).
Ignores memory semantics: screening only."""
import sys, os, re, json, tempfile, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location('irre_mod', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'irre_lib.py'))
irre = importlib.util.module_from_spec(spec); spec.loader.exec_module(irre)

TOK = r'(?![\w.$])'


def cfg(L, blk):
    order = []; succ = {}; cur = None
    for k, l in enumerate(L):
        b = blk[k]
        if b not in succ: succ[b] = []; order.append(b)
        s = l.strip()
        if s.startswith('br ') or s.startswith('switch ') or s.startswith('invoke ') or ('label %' in s and not s.startswith(';')):
            for t in re.findall(r'label %("[^"]+"|[\w.$-]+)', s): succ[b].append(t.strip('"') if False else t)
    order=[b for b in order if b!='entry']; succ.pop('entry',None)
    return order, succ


def doms(order, succ):
    pred = {b: [] for b in order}
    for b in order:
        for t in succ[b]:
            if t in pred: pred[t].append(b)
    entry = order[0]; allb = set(order); D = {b: set(allb) for b in order}; D[entry] = {entry}
    ch = True
    while ch:
        ch = False
        for b in order[1:]:
            ps = [D[p] for p in pred[b]]
            n = set.intersection(*ps) | {b} if ps else {b}
            if n != D[b]: D[b] = n; ch = True
    return D


def main():
    a = sys.argv[1:]; m = a.pop(0); outp = a.pop(0); jobs = 4
    if '--jobs' in a: jobs = int(a[a.index('--jobs') + 1])
    text = open(m).read(); pre, fn, post = irre.split_fn(text); O = irre.orig()
    L, blk = irre.parse(fn)
    # function's first block has label 'start' in these modules
    order, succ = cfg(L, blk); D = doms(order, succ)
    loads = []
    for i, l in enumerate(L):
        mm = re.match(r'^\s+(%[\w.$]+) = load (\S+), ptr (%[\w.$]+|@[\w.$]+)(.*)$', l)
        if mm: loads.append((i, mm.group(1), mm.group(2), mm.group(3)))
    gep = {}
    for l in L:
        g = re.match(r'^\s+(%[\w.$]+) = getelementptr inbounds i8, ptr (%[\w.$]+), i64 (-?\d+)$', l)
        if g: gep[g.group(1)] = (g.group(2), int(g.group(3)))
    def canon(p):
        o = 0
        while p in gep: b, c = gep[p]; o += c; p = b
        return (p, o)
    by = {}
    for x in loads: by.setdefault((canon(x[3]), x[2]), []).append(x)
    vs = []
    for key, xs in by.items():
        if len(xs) < 2: continue
        allpairs = []
        for x1 in xs:
            for x2 in xs:
                if x1 is x2: continue
                b1, b2 = blk[x1[0]], blk[x2[0]]
                if b1 != b2 and b1 in D.get(b2, ()):
                    vs.append(('%s<-%s' % (x2[1], x1[1]), [(x2, x1)])); allpairs.append((x2, x1))
        if len(allpairs) > 1:
            first = {}
            for x2, x1 in allpairs:
                # fold into the most dominating source
                if x2[1] not in first or blk[first[x2[1]][1][0]] in D[blk[x1[0]]]: first[x2[1]] = (x2, x1)
            vs.append(('ALL:%s+%d' % key[0], list(first.values())))
    base = irre.run(pre, fn, post, O, tempfile.mkdtemp(prefix='irh'))
    print('base', base, 'variants', len(vs), flush=True)
    work = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a03-cto-liverange/var/irhold')

    def job(v):
        name, pairs = v; N = list(L); drop = set()
        srcmap = {}
        for x2, x1 in pairs:
            s = x1[1]
            while s in srcmap: s = srcmap[s]
            srcmap[x2[1]] = s
        for x2, x1 in pairs:
            s = srcmap[x2[1]]; drop.add(x2[0]); rx = re.compile(re.escape(x2[1]) + TOK)
            N = [rx.sub(s, l) if k not in drop else l for k, l in enumerate(N)]
        N = [l for k, l in enumerate(N) if k not in drop]
        d = work + '/' + re.sub(r'[^\w]', '_', name)[:80]
        r = irre.run(pre, '\n'.join(N), post, O, d)
        for f in ('m.ll', 'm.o'):
            try: os.remove(d + '/' + f)
            except OSError: pass
        r.update({'v': name, 'n': len(pairs)}); return r
    with open(outp, 'w') as f, cf.ThreadPoolExecutor(jobs) as ex:
        for r in ex.map(job, vs):
            r['d'] = round(r['ratio'] - base['ratio'], 5) if 'ratio' in r else None
            f.write(json.dumps(r) + '\n'); f.flush()
            if r.get('d') and r['d'] > 0: print('GAIN', r, flush=True)


main()
