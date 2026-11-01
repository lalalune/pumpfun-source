#!/usr/bin/env python3
"""dvec.py <m.ll> <bp.txt> <ssc-dir> <out.jsonl> [jobs]  (experiment only)
Per conditional branch of admin_cto::execute in the post-opt module, set explicit branch weights near the natural
probability (trap-like edges: rare edge p in {2e-5, 5e-4}; others: x0.98 / x1.02), run the private llc with
-debug-only=stack-slot-coloring, and record:
  ra_same : the spill intervals (segments) equal the base's, i.e. RA unchanged, only SSC weights moved
  dw      : {SS#: new weight - base weight} for intervals whose weight moved
  M/bytes : the real result of that IR edit.
The dw vectors of ra_same edits combine (small p: linear) in sscsim's colour simulator."""
import sys, os, re, json, subprocess, tempfile
from multiprocessing import Pool
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import sscsim, ordor
LAB = r'%("[^"]+"|[\w.\-$]+)'
BR = re.compile(r'^(\s+br i1 %[\w.\-]+, label ' + LAB + r', label ' + LAB + r')(, !prof ![0-9]+)?(.*)$')

def split_module(t):
    m = None
    for mm in re.finditer(r'\ndefine [^\n]*admin_cto7execute[^\n]*\{', t): m = mm
    i = m.start(); j = t.index('\n}\n', i)
    return t[:i], t[i:j], t[j:]

def blocks_of(L):
    cur = 'start'; bl = []
    for l in L:
        m = re.match(r'^("[^"]+"|[\w.\-$]+):', l)
        if m: cur = m.group(1)
        bl.append(cur)
    return bl

def probs(bp):
    t = open(bp).read()
    i = t.index("admin_cto7execute"); j = t.find("Printing analysis", i + 10); t = t[i:j if j > 0 else None]
    P = {}
    for m in re.finditer(r'edge %("[^"]+"|[\w.\-$]+) -> %("[^"]+"|[\w.\-$]+) probability is 0x([0-9a-f]+) / 0x80000000', t):
        P[(m.group(1), m.group(2))] = int(m.group(3), 16) / 2**31
    return P

def variants(mll, bp):
    t = open(mll).read(); pre, body, post = split_module(t); L = body.split('\n'); B = blocks_of(L); P = probs(bp)
    md = max([int(x) for x in re.findall(r'^!(\d+) = ', t, re.M)] + [0]) + 1
    out = []
    for k, l in enumerate(L):
        m = BR.match(l)
        if not m: continue
        a, b = m.group(2), m.group(3)
        if a == b: continue
        pT = P.get((B[k], a))
        if pT is None: continue
        rare = min(pT, 1 - pT)
        if rare < 1e-4:
            ps = [('t2e5', 2e-5), ('t5e4', 5e-4)]
            vs = [(n, p if pT < 0.5 else 1 - p) for n, p in ps]
        else:
            vs = [('m98', pT * 0.98), ('p102', min(pT * 1.02, 1 - 1e-6))]
        for n, q in vs:
            wa = max(1, round(q * 2**31)); wb = max(1, 2**31 - wa)
            L2 = list(L); L2[k] = m.group(1) + f', !prof !{md}' + m.group(5)
            out.append({'name': f'{n}:{k}', 'line': k, 'pT': pT, 'q': q, 'blk': B[k][:60],
                        'text': pre + '\n'.join(L2) + post + f'\n!{md} = !{{!"branch_weights", i32 {wa}, i32 {wb}}}\n'})
    return out

BASE = None
def init(d):
    global BASE
    BASE = sscsim.parse(d + '/ssc.log')[0]

def run(v):
    fd, p = tempfile.mkstemp(suffix='.ll'); os.close(fd); open(p, 'w').write(v['text'])
    fo = p[:-3] + '.o'
    try:
        r = subprocess.run([T + '/llcp.sh', p, '-filetype=obj', '-o', fo, '-debug-only=stack-slot-coloring'], capture_output=True, text=True)
        if r.returncode: return {'name': v['name'], 'err': r.stderr[-300:]}
        lg = fo + '.log'; open(lg, 'w').write(r.stderr)
        try: iv, asg = sscsim.parse(lg)
        finally: os.remove(lg)
        same = set(iv) == set(BASE) and all(iv[s][0] == BASE[s][0] for s in iv)
        dw = {s: iv[s][1] - BASE[s][1] for s in iv if s in BASE and iv[s][1] != BASE[s][1]} if same else {}
        b = sscsim.oracle.elf_fn(fo, sscsim.oracle.KEEP); M, ratio = ordor.M(b)
        return {'name': v['name'], 'line': v['line'], 'pT': v['pT'], 'q': v['q'], 'blk': v['blk'], 'ra_same': same,
                'n_iv': len(iv), 'dw': dw, 'M': M, 'ratio': ratio, 'bytes': len(b)}
    finally:
        os.remove(p)
        if os.path.exists(fo): os.remove(fo)

if __name__ == '__main__':
    mll, bp, d, out = sys.argv[1:5]; jobs = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    V = variants(mll, bp); print(len(V), 'variants', file=sys.stderr)
    with Pool(jobs, initializer=init, initargs=(d,)) as pool, open(out, 'w') as f:
        for r in pool.imap_unordered(run, V):
            f.write(json.dumps(r) + '\n'); f.flush()
