#!/usr/bin/env python3
"""nosc.py: per-alloca implied original slot table from a -no-stack-coloring llc run.
usage: nosc.py <module.ll> <sym-regex> [name] [--mir mir --mir-fn rx]"""
import sys, re, collections, runpy, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / 'w4-frame-oracle'))
sys.argv_saved = sys.argv[:]
import frameoracle as fo
args = sys.argv_saved[1:]
ir, symrx = args[0], args[1]
name = args[2] if len(args) > 2 else 'nosc'
OUT = Path.home()/'.cache/pumpfun-reconstruction/lanes/w12a01-cto-frame/nosc'/name
OUT.mkdir(parents=True, exist_ok=True)
mod = Path(ir).read_text()
m = re.search(r'^define [^\n]*@(' + symrx + r')\(', mod, flags=re.M)
sym = m.group(1)
text, cand = fo.run_llc(Path(ir), sym, OUT, ['-no-stack-coloring'])
dumps = fo.split_dumps(text)
before = dumps[('Before', 'stack-coloring')]
fin = fo.frame_objects(dumps[('After', 'prologepilog')])
names, lt = fo.names_and_marks(before)
sc = fo.load_score()
W = {x['start']: x for x in sc.original_windows()}
orig = W[0x22a10]['raw']
class A: minv = 2
r = fo.analyze(orig, cand, fin, names, lt, {}, OUT, A)
print(f'# nosc abstracted ratio {r["ratio"]:.4f} pairs {r["pairs"]}')
rows = []
for x in r['rows']:
    print(f'{x["fi"]:>4} T={x["T"]:#6x} orig={str(x["orig"]) if x["orig"] is None else hex(x["orig"]):>7} '
          f'd={str(x["delta"]) if x["delta"] is not None else "?":>6} sz={x["size"]:<4} al={x["align"]} lt={x["lt"]} v={x["votes"]}/{x["tot"]} {x["name"]} alt={x["alt"]}')
    rows.append({k: x[k] for k in ('fi','T','orig','delta','size','align','lt','votes','tot','name')})
(OUT/'rows.json').write_text(json.dumps(rows, indent=0))
