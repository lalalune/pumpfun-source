#!/usr/bin/env python3
"""keypairs.py <mod.ll> <outdir> [maxk]: like keycombo.py but over EVERY inlined AccountInfo::clone in execute (sweep
transfer CPI, sharing CPI, ...): all singles, pairs and triples (maxk, default 2) of key-after-Rc moves. Labels are
`<line of key load>`. Prints the best at 27,400 B and overall; full rows in <outdir>.jsonl."""
import sys, os, re, subprocess, json, itertools
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co
H = os.path.dirname(os.path.abspath(__file__))
mod, out = sys.argv[1], sys.argv[2]; maxk = int(sys.argv[3]) if len(sys.argv) > 3 else 2
txt = open(mod).read(); sym = co.SYMRE.search(txt).group(0); i, j = co.fn_bounds(txt, sym); L = txt[i:j].split('\n')
mv = {}
for k, l in enumerate(L):
    m = re.match(r'  %(_2\.i[\d.i]*) = load ptr, ptr %([\w.]+), align 8', l)
    if not m: continue
    key, X = m.group(1), m.group(2)
    g = [n for n in range(k, min(k + 60, len(L))) if re.match(r'  %(\S+) = getelementptr inbounds i8, ptr %' + re.escape(X) + r', i64 24$', L[n])]
    if g: mv[f'L{k}'] = f"{key}@x@before:{re.match(r'  %(\S+) = ', L[g[0]]).group(1)}"
names = sorted(mv, key=lambda s: int(s[1:])); print('moves', len(mv), flush=True)
def one(sub):
    lab = '+'.join(sub)
    env = dict(os.environ, MOVE=';'.join(mv[s] for s in sub))
    r = subprocess.run([sys.executable, H + '/ctoracle.py', 'run', mod, f'{out}/{lab}', '--edit', H + '/edit_move.py'], env=env, capture_output=True, text=True)
    m = json.loads(r.stdout.strip().split('\n')[-1]) if r.returncode == 0 else {'err': r.stderr[-200:]}
    subprocess.run(['rm', '-rf', f'{out}/{lab}'])
    return lab, m
subs = [s for n in range(1, maxk + 1) for s in itertools.combinations(names, n)]
res = []
with ThreadPoolExecutor(4) as ex, open(out + '.jsonl', 'w') as f:
    for lab, m in ex.map(one, subs):
        f.write(json.dumps({'lab': lab, **m}) + '\n'); res.append((lab, m))
ok = [(l, m) for l, m in res if 'ratio' in m]
print('--- 27400'); [print(l, m) for l, m in sorted([x for x in ok if x[1]['bytes'] == 27400], key=lambda x: -x[1]['ratio'])[:12]]
print('--- all'); [print(l, m) for l, m in sorted(ok, key=lambda x: -x[1]['ratio'])[:8]]
