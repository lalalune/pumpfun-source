import sys, json
sys.path.insert(0, '.')
from an import *
O = load_orig()
C = load_cand(sys.argv[1])
M = matches(O, C)
oc = callers(O)
d = json.load(open(SC / 'shared/original-source-sites.json'))
ws = sorted(set(int(x['window'], 16) for x in d if x['path'].endswith('src/lib.rs')))
def nm(st):
    if st in M:
        return 'M:' + C[M[st][0]]['name'][:100] + (f' (+{len(M[st])-1})' if len(M[st]) > 1 else '')
    return 'unmatched'
for w in ws:
    W = O[w]
    print(f"== {w:#x} {W['bytes']}B sites={[(s['path'].split('/')[-1], s['line'], s['code']) for s in W['sites']]}")
    for (p, off) in oc.get(w, []):
        print(f"     caller {p:#x}+{off:#x} {O[p]['bytes']}B {nm(p)}  sites={[(s['path'].split('/')[-1], s['line']) for s in O[p]['sites']][:6]}")
