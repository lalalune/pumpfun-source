#!/usr/bin/env python3
"""fieldscan.py <mod.ll> <outdir> [--pairs N]: (--pairs N: also every pair of the N best singles with every single) llc oracle for hand-written AccountInfo clone field orders, per inlined clone in execute:
  K<line>  key load after both Rc increments;
  O<line>  owner load (with its GEP) before the lamports Rc;  R<line> rent_epoch before;  F<line> is_signer before;
  A<line>  owner+rent_epoch+flags all before the lamports Rc (literal order key,owner,rent_epoch,flags,lamports,data).
Prints the best at 27,400 B and overall; rows in <outdir>.jsonl."""
import sys, os, re, subprocess, json
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co
H = os.path.dirname(os.path.abspath(__file__))
mod, out = sys.argv[1], sys.argv[2]
txt = open(mod).read(); sym = co.SYMRE.search(txt).group(0); i, j = co.fn_bounds(txt, sym); L = txt[i:j].split('\n')
def dname(n): return re.match(r'  %(\S+) = ', L[n]).group(1)
cands = {}
for k, l in enumerate(L):
    m = re.match(r'  %(_2\.i[\d.i]*) = load ptr, ptr %([\w.]+), align 8', l)
    if not m: continue
    key, X = m.group(1), m.group(2)
    geps = {}
    for n in range(k, min(k + 60, len(L))):
        g = re.match(r'  %(\S+) = getelementptr inbounds i8, ptr %' + re.escape(X) + r', i64 (\d+)$', L[n])
        if g: geps[int(g.group(2))] = (g.group(1), dname(n + 1) if re.match(r'  %\S+ = load ', L[n + 1]) else None)
    if 8 not in geps or 24 not in geps: continue
    g8 = geps[8][0]
    def early(offs):
        return ';'.join(f"{geps[o][0]}@x@before:{g8};{geps[o][1]}@x@before:{g8}" for o in offs if o in geps and geps[o][1])
    cands[f'K{k}'] = f"{key}@x@before:{geps[24][0]}"
    cands[f'O{k}'] = early([24]); cands[f'R{k}'] = early([32]); cands[f'F{k}'] = early([40]); cands[f'A{k}'] = early([24, 32, 40, 41, 42])
def one(lab):
    env = dict(os.environ, MOVE=cands[lab])
    r = subprocess.run([sys.executable, H + '/ctoracle.py', 'run', mod, f'{out}/{lab}', '--edit', H + '/edit_move.py'], env=env, capture_output=True, text=True)
    m = json.loads(r.stdout.strip().split('\n')[-1]) if r.returncode == 0 else {'err': r.stderr[-200:]}
    subprocess.run(['rm', '-rf', f'{out}/{lab}']); return lab, m
res = []
with ThreadPoolExecutor(4) as ex, open(out + '.jsonl', 'w') as f:
    for lab, m in ex.map(one, sorted(cands)):
        f.write(json.dumps({'lab': lab, **m}) + '\n'); res.append((lab, m))
ok = [(l, m) for l, m in res if 'ratio' in m]; print('runs', len(res), 'ok', len(ok))
if '--pairs' in sys.argv:
    N = int(sys.argv[sys.argv.index('--pairs') + 1])
    top = [l for l, m in sorted(ok, key=lambda x: -x[1]['ratio'])[:N]]
    pairs = sorted({tuple(sorted((a, b))) for a in top for b in cands if a != b and a[1:] != b[1:]})
    for a, b in pairs: cands[a + '+' + b] = cands[a] + ';' + cands[b]
    with ThreadPoolExecutor(4) as ex, open(out + '.pairs.jsonl', 'w') as f:
        for lab, m in ex.map(one, [a + '+' + b for a, b in pairs]):
            f.write(json.dumps({'lab': lab, **m}) + '\n'); res.append((lab, m))
    ok = [(l, m) for l, m in res if 'ratio' in m]; print('pairs', len(pairs))
print('--- 27400'); [print(l, m) for l, m in sorted([x for x in ok if x[1]['bytes'] == 27400], key=lambda x: -x[1]['ratio'])[:10]]
print('--- all'); [print(l, m) for l, m in sorted(ok, key=lambda x: -x[1]['ratio'])[:8]]
