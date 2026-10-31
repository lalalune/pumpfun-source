#!/usr/bin/env python3
"""bwgreedy.py <ex.ll> <sweep.jsonl> <out.jsonl> [base]: size-pinned greedy over single-edit winners (experiment only)."""
import sys, json, os
sys.path.insert(0, os.path.dirname(__file__)); import bwx
from concurrent.futures import ThreadPoolExecutor
mod = open(sys.argv[1]).read(); o = bwx.orig_toks(); out = open(sys.argv[3], 'a')
cur = sys.argv[4] if len(sys.argv) > 4 else ''
b0 = bwx.run(mod, cur, o)['ratio']
single = [json.loads(l) for l in open(sys.argv[2])]
cands = sorted({r['item'] for r in single if r.get('ratio', 0) > b0 - 0.002})
while True:
    used = {c.split(':')[1] for c in cur.split(',') if c}
    todo = [c for c in cands if c.split(':')[1] not in used]
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda it: (it, bwx.run(mod, (cur+',' if cur else '')+it, o)), todo))
    res = [(it, r) for it, r in res if r.get('bytes') == 27400 and r['ratio'] > b0]
    if not res: break
    it, r = max(res, key=lambda x: x[1]['ratio'])
    cur = (cur+',' if cur else '')+it; b0 = r['ratio']
    out.write(json.dumps({'spec': cur, 'ratio': b0, 'slots': r['slots']})+'\n'); out.flush()
    print(b0, it, flush=True)
