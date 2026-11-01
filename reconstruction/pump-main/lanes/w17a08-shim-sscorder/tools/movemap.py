#!/usr/bin/env python3
"""movemap.py <ssc-dir> <out.jsonl> [jobs] [base-order.json]: every single 'move interval s to rank j' of the colour
processing order, scored exactly with sscsim (colouring dedupe: unchanged colouring = base M). Experiment only."""
import sys, os, json
from multiprocessing import Pool
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import sscsim
S = None; BASEK = None; BASE_ORDER = None
def init(d, bo):
    global S, BASEK, BASE_ORDER
    S = sscsim.Sim(d); BASE_ORDER = json.load(open(bo)) if bo else S.order; BASEK = S.colour(BASE_ORDER)
def job(i):
    o0 = BASE_ORDER; s = o0[i]; res = []; seen = {}
    for j in range(len(o0)):
        if j == i: continue
        o = list(o0); o.pop(i); o.insert(j, s)
        k = S.colour(o)
        if k == BASEK: continue
        key = tuple(sorted(k.items()))
        if key in seen: res.append((s, j, seen[key])); continue
        m, r = S.M(S.relabel(k)); seen[key] = m; res.append((s, j, m))
    return res
if __name__ == '__main__':
    d, out = sys.argv[1], sys.argv[2]; jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    bo = sys.argv[4] if len(sys.argv) > 4 else None
    init(d, bo); n = len(BASE_ORDER)
    with Pool(jobs, initializer=init, initargs=(d, bo)) as p, open(out, 'w') as f:
        for res in p.imap_unordered(job, range(n)):
            for s, j, m in res: f.write(json.dumps([s, j, m]) + '\n')
