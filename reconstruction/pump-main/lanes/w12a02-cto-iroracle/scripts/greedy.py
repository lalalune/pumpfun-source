#!/usr/bin/env python3
"""greedy.py <module.ll> <outdir> <basespec> <items_file> <rounds> [-j N] [--size 27400]
Greedy forward selection over iredit items: each round runs base+item for every unused item,
adds the best item if it raises the ratio, and logs the round (individual and cumulative gain).
--size restricts acceptance to items keeping the function at that byte size (optional)."""
import json, os, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import iredit, ctoracle  # noqa: E402

mod_path, out, base, items_file, rounds = sys.argv[1:6]
j = int(sys.argv[sys.argv.index('-j') + 1]) if '-j' in sys.argv else 6
size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else None
out = Path(out); out.mkdir(parents=True, exist_ok=True)
iredit.ORIG = ctoracle.orig_tokens()
mod = Path(mod_path).read_text()
items = [l.strip() for l in open(items_file) if l.strip()]
cur = iredit.run_spec(mod, out / 'base', base)
log = open(out / 'greedy.jsonl', 'a')
log.write(json.dumps({'round': 0, 'spec': base, **cur}) + '\n'); log.flush()
used = set()
for r in range(1, int(rounds) + 1):
    cand = [it for it in items if it not in used]
    def one(k_it):
        k, it = k_it
        spec = ','.join(x for x in (base, it) if x)
        try:
            return it, iredit.run_spec(mod, out / f'w{threading.get_ident()}', spec)
        except Exception as e:  # noqa
            return it, {'error': repr(e)[:200]}
    res = []
    with ThreadPoolExecutor(j) as ex:
        for it, m in ex.map(one, list(enumerate(cand))):
            if 'ratio' in m:
                res.append((it, m))
    (out / f'round{r}.json').write_text(json.dumps({it: m for it, m in res}))
    ok = [(it, m) for it, m in res if size is None or m['bytes'] == size]
    if not ok:
        break
    K = 'pf_ratio' if os.environ.get('PF') else 'ratio'
    it, m = max(ok, key=lambda x: (x[1][K], x[1]['ratio']))
    if m[K] <= cur[K]:
        log.write(json.dumps({'round': r, 'stop': True, 'best': it, **m}) + '\n'); break
    gain = round(m[K] - cur[K], 5)
    base = ','.join(x for x in (base, it) if x); used.add(it); cur = m
    top = sorted(res, key=lambda x: -x[1][K])[:8]
    log.write(json.dumps({'round': r, 'added': it, 'gain': gain, 'spec': base, **m,
                          'runners_up': [(a, b[K]) for a, b in top[1:]]}) + '\n'); log.flush()
