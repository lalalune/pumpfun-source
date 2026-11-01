#!/usr/bin/env python3
"""combo.py <m.ll> <bp.txt> <outdir> [jobs] [N2] [N3]  (experiment only)
Branch-weight combinations on admin_cto::execute's post-opt IR, scored exactly (private llc = SDK llc bytes, fastbuild flags).
Edits: per conditional br, explicit branch_weights near the natural BPI probability:
  trap-like edge (rare < 1e-4): rare-edge p in P_TRAP (models rcincp/expect_p on an Rc/overflow trap)
  other: true-edge probability x (1+eps), eps in EPS (models expect_p(c, v, p) on a source condition)
Stage 1 singles; stage 2 pairs of the N2 best colour-changing singles at 27,400 B; stage 3 adds a third edit to the N3 best pairs."""
import sys, os, re, json, subprocess, tempfile, hashlib, itertools
from multiprocessing import Pool
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import dvec, ordor
P_TRAP = [2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4, 5e-4]
EPS = [-0.05, -0.01, -0.001, 0.001, 0.01, 0.05]
G = {}
def setup(mll, bp):
    t = open(mll).read(); pre, body, post = dvec.split_module(t); L = body.split('\n'); B = dvec.blocks_of(L); P = dvec.probs(bp)
    md = max([int(x) for x in re.findall(r'^!(\d+) = ', t, re.M)] + [0]) + 1
    E = []
    for k, l in enumerate(L):
        m = dvec.BR.match(l)
        if not m or m.group(2) == m.group(3): continue
        pT = P.get((B[k], m.group(2)))
        if pT is None: continue
        if min(pT, 1 - pT) < 1e-4:
            for p in P_TRAP: E.append((k, p if pT < 0.5 else 1 - p, f't{p:g}'))
        else:
            for e in EPS:
                q = pT * (1 + e)
                if 0 < q < 1: E.append((k, q, f'e{e:g}'))
    G.update(pre=pre, L=L, post=post, md=md, E=E)
    return E
def text(edits):
    L = list(G['L']); md = G['md']; meta = []
    for i, (k, q, _) in enumerate(edits):
        m = dvec.BR.match(L[k]); wa = max(1, round(q * 2**31)); wb = max(1, 2**31 - wa)
        L[k] = m.group(1) + f', !prof !{md + i}' + m.group(5)
        meta.append(f'!{md + i} = !{{!"branch_weights", i32 {wa}, i32 {wb}}}')
    return G['pre'] + '\n'.join(L) + G['post'] + '\n' + '\n'.join(meta) + '\n'
def init(mll, bp): setup(mll, bp)
def run(edits):
    fd, p = tempfile.mkstemp(suffix='.ll'); os.close(fd); open(p, 'w').write(text(edits)); fo = p[:-3] + '.o'
    try:
        r = subprocess.run([T + '/llcp.sh', p, '-filetype=obj', '-o', fo], capture_output=True, text=True)
        if r.returncode: return {'e': edits, 'err': r.stderr[-200:]}
        b = dvec.sscsim.oracle.elf_fn(fo, dvec.sscsim.oracle.KEEP); M, ratio = ordor.M(b)
        return {'e': edits, 'M': M, 'ratio': ratio, 'bytes': len(b), 'sig': hashlib.sha1(b).hexdigest()[:10]}
    finally:
        os.remove(p)
        if os.path.exists(fo): os.remove(fo)
if __name__ == '__main__':
    mll, bp, od = sys.argv[1:4]; jobs = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    N2 = int(sys.argv[5]) if len(sys.argv) > 5 else 60; N3 = int(sys.argv[6]) if len(sys.argv) > 6 else 15
    os.makedirs(od, exist_ok=True); E = setup(mll, bp)
    with Pool(jobs, initializer=init, initargs=(mll, bp)) as pool:
        base = run([]); print('base', base, len(E), 'edits', file=sys.stderr, flush=True)
        S1 = list(pool.imap_unordered(run, [[e] for e in E], chunksize=4))
        json.dump({'base': base, 'S1': S1}, open(od + '/s1.json', 'w'))
        ch = [r for r in S1 if 'err' not in r and r['bytes'] == 27400 and r['sig'] != base['sig']]
        ch.sort(key=lambda r: -r['M']); print('S1 best', [(r['e'], r['M']) for r in ch[:8]], 'changed@27400', len(ch), file=sys.stderr, flush=True)
        # dedupe by sig: keep the best-ranked edit per distinct outcome, up to N2
        top = []; seen = set()
        for r in ch:
            if r['sig'] in seen: continue
            seen.add(r['sig']); top.append(r['e'][0])
            if len(top) >= N2: break
        pairs = [[a, b] for a, b in itertools.combinations(top, 2) if a[0] != b[0]]
        S2 = list(pool.imap_unordered(run, pairs, chunksize=4))
        json.dump(S2, open(od + '/s2.json', 'w'))
        ok2 = sorted([r for r in S2 if 'err' not in r and r['bytes'] == 27400], key=lambda r: -r['M'])
        print('S2 best', [(r['e'], r['M']) for r in ok2[:8]], file=sys.stderr, flush=True)
        trip = []
        for r in ok2[:N3]:
            ls = {e[0] for e in r['e']}
            for e in top:
                if e[0] not in ls: trip.append(r['e'] + [e])
        S3 = list(pool.imap_unordered(run, [list(x) for x in trip], chunksize=4))
        json.dump(S3, open(od + '/s3.json', 'w'))
        ok3 = sorted([r for r in S3 if 'err' not in r and r['bytes'] == 27400], key=lambda r: -r['M'])
        print('S3 best', [(r['e'], r['M']) for r in ok3[:8]], file=sys.stderr, flush=True)
