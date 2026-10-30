#!/usr/bin/env python3
"""keycombo.py <mod.ll> <outdir>: llc oracle over every subset of the key-late moves keyscan.py finds (sharing-CPI clones),
optionally with the cashback-and sink (cb). Prints the best results at 27,400 B and overall."""
import sys, os, re, subprocess, json, itertools
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co
H = os.path.dirname(os.path.abspath(__file__))
mod, out = sys.argv[1], sys.argv[2]
txt = open(mod).read(); sym = co.SYMRE.search(txt).group(0); i, j = co.fn_bounds(txt, sym); L = txt[i:j].split('\n')
mv = {}
for k, l in enumerate(L):
    m = re.match(r'  %(_2\.i\d+) = load ptr, ptr %([\w.]+), align 8', l)
    if not m: continue
    key, X = m.group(1), m.group(2)
    g = [n for n in range(k, min(k + 60, len(L))) if re.match(r'  %(\S+) = getelementptr inbounds i8, ptr %' + re.escape(X) + r', i64 24$', L[n])]
    st = [x for x in L if re.search(r'store ptr %' + re.escape(key) + r', ptr %(\S+),', x)]
    if not g or not st or '_1' not in st[0]: continue
    slot = re.search(r'sroa\.(\d+)\.0\.\.sroa_idx', st[0]); slot = slot.group(1) if slot else 'pa'
    mv['k' + slot] = f"{key}@x@before:{re.match(r'  %(\S+) = ', L[g[0]]).group(1)}"
names = sorted(mv); print('moves', mv, flush=True)
def one(sub):
    lab = '+'.join(sub) or 'base'
    env = dict(os.environ, MOVE=';'.join(mv[s] for s in sub))
    if not sub: env['MOVE'] = ''
    args = [sys.executable, H + '/ctoracle.py', 'run', mod, f'{out}/{lab}'] + (['--edit', H + '/edit_move.py'] if sub else [])
    r = subprocess.run(args, env=env, capture_output=True, text=True)
    m = json.loads(r.stdout.strip().split('\n')[-1]) if r.returncode == 0 else {'err': r.stderr[-200:]}
    subprocess.run(['rm', '-rf', f'{out}/{lab}'])
    return lab, m
subs = [s for n in range(0, len(names) + 1) for s in itertools.combinations(names, n)]
res = []
with ThreadPoolExecutor(4) as ex, open(out + '.jsonl', 'w') as f:
    for lab, m in ex.map(one, subs):
        f.write(json.dumps({'lab': lab, **m}) + '\n'); res.append((lab, m))
ok = [(l, m) for l, m in res if 'ratio' in m]
print('--- 27400'); [print(l, m) for l, m in sorted([x for x in ok if x[1]['bytes'] == 27400], key=lambda x: -x[1]['ratio'])[:10]]
print('--- all'); [print(l, m) for l, m in sorted(ok, key=lambda x: -x[1]['ratio'])[:10]]
