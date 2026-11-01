#!/usr/bin/env python3
"""winmove.py <mn.ll> <lo> <hi> <out.jsonl> [jobs]  (experiment only; instnamer'd module)
L5713 generalised: each load in execute lines [lo,hi) (with its private GEP) moved, volatile, into every LATER Rc count
window (right after `%x = load i64, ptr %rc` whose `store i64 .., ptr %rc` follows within 8 lines) that precedes the
load's first use. Scored with the private llc (= SDK bytes)."""
import sys, os, re, json
from multiprocessing import Pool
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import mvload
def windows(L):
    W = []
    for k, l in enumerate(L):
        m = re.match(r'\s+(%[\w.\-]+) = load i64, ptr (%[\w.\-]+), align 8', l)
        if not m: continue
        for j in range(k + 1, min(k + 9, len(L))):
            if re.match(r'\s+store i64 %[\w.\-]+, ptr ' + re.escape(m.group(2)) + r', align 8', L[j]): W.append(k + 1); break
    return W
def cands(lo, hi):
    L = mvload.G["L"]; W = windows(L); out = []; hi = min(hi, len(L))
    for i in range(lo, hi):
        m = re.match(r'\s+(%[\w.\-]+) = load (?!volatile)(\S+), ptr (%[\w.\-]+)', L[i])
        if not m: continue
        v, ptr = m.group(1), m.group(3); first = mvload.uses(L, v, i + 1)
        if first is None: continue
        gi = i - 1 if re.match(r'\s+' + re.escape(ptr) + r' = getelementptr', L[i - 1]) and mvload.uses(L, ptr, i + 1) is None else None
        moved = [gi, i] if gi is not None else [i]
        for w in W:
            if i < w <= first: out.append({'mv': moved, 'to': w, 'vol': 1, 'name': f'{i}->W{w}'})
    return out
if __name__ == '__main__':
    mll, lo, hi, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    jobs = int(sys.argv[5]) if len(sys.argv) > 5 else 5
    mvload.setup(mll); C = cands(lo, hi); print(len(C), 'candidates', len(windows(mvload.G['L'])), 'windows', file=sys.stderr, flush=True)
    with Pool(jobs, initializer=mvload.init, initargs=(mll,)) as pool, open(out, 'w') as f:
        for r in pool.imap_unordered(mvload.run, C, chunksize=4):
            f.write(json.dumps(r) + '\n'); f.flush()
