import sys, json
sys.path.insert(0, '.')
from an import *
from cmap import build
O = load_orig()
C = load_cand(sys.argv[1])
M = matches(O, C)
cp = build(O, C, M)
oc = callers(O)
for w in [int(x, 0) for x in sys.argv[2:]]:
    W = O[w]
    a = cp.get(w)
    print(f"== {w:#x} {W['bytes']}B sites={[(s['path'].split('src/')[-1], s['line'], s['code']) for s in W['sites']]} cp={(hex(a[0]), C[a[0]]['name'][:80], a[1]) if a else None}")
    for (p, off) in oc.get(w, []):
        pa = cp.get(p)
        print(f"   caller {p:#x}+{off:#x} {O[p]['bytes']}B  cp={(hex(pa[0]), C[pa[0]]['name'][:80]) if pa else None} sites={[(s['path'].split('src/')[-1], s['line']) for s in O[p]['sites']][:6]}")
    for (off, t) in W['calls']:
        ta = cp.get(t)
        print(f"   callee +{off:#x} {t:#x} {O[t]['bytes'] if t in O else '?'}B cp={(hex(ta[0]), C[ta[0]]['name'][:80]) if ta else None} sites={[(s['path'].split('src/')[-1], s['line']) for s in O[t]['sites']][:6] if t in O else ''}")
