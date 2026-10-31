#!/usr/bin/env python3
"""px.py <name> <edits.py> [--base m.ll] : post-opt IR oracle (experiment only). Applies EDITS (exact (old,new) pairs
or callables) to the slimmed post-opt module rx.py wrote (rx/<base>/m.ll), runs llc exactly like rx.py and scores."""
import sys, os, subprocess, runpy, json, re
sys.argv_s = sys.argv; T = os.path.dirname(os.path.abspath(__file__))
src = open(T + '/rx.py').read()
pre = src[:src.index("a=sys.argv[1:]")]          # functions + OUT/SDK
g = {}; sys.argv = ['rx']; exec(compile(pre, 'rx', 'exec'), g); sys.argv = sys.argv_s
a = sys.argv[1:]; name = a.pop(0); edits = a.pop(0) if a and not a[0].startswith('--') else None
base = g['OUT'] + '/rx/m0/m.ll'
while a:
    x = a.pop(0)
    if x == '--base': base = a.pop(0)
d = g['OUT'] + '/px/' + name; os.makedirs(d, exist_ok=True)
t = open(base).read()
if edits:
    for e in runpy.run_path(edits)['EDITS']:
        if callable(e): t = e(t); continue
        x, y = e; c = t.count(x); assert c == 1, (c, x[:200]); t = t.replace(x, y)
open(d + '/m.ll', 'w').write(t)
r = subprocess.run([g['SDK'] + '/llc', '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections', d + '/m.ll', '-filetype=obj', '-o', d + '/m.o'], capture_output=True, text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
cand = g['elf_fn'](d + '/m.o', g['KEEP']); open(d + '/fn.bin', 'wb').write(cand)
rr, sd = g['metric'](cand, g['orig_window']())
res = {'name': name, 'ratio': round(rr, 5), 'bytes': len(cand), 'slots_diff': sd}
bs = os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
res['eq_main'] = g['mask'](g['elf_fn'](bs, g['KEEP'])) == g['mask'](cand)
print(json.dumps(res)); open(d + '/res.json', 'w').write(json.dumps(res))
