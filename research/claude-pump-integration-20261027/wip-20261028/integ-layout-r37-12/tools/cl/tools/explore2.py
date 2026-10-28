import sys, json
sys.path.insert(0, '.')
from an import *
from cmap import build
O = load_orig()
C = load_cand(sys.argv[1])
M = matches(O, C)
cp = build(O, C, M)
d = json.load(open(SC / 'shared/original-source-sites.json'))
ws = sorted(set(int(x['window'], 16) for x in d if x['path'].endswith('src/lib.rs')))
for w in ws:
    W = O[w]
    if w in cp:
        a, how = cp[w]
        f = C[a]
        print(f"{w:#x} {W['bytes']:6d} -> {a:#x} {f['bytes']:6d} {f['name'][:90]}  [{how}]")
        print(f"      orig sites {[(s['line'], s['code']) for s in W['sites']]}  cand sites {[(s['path'].replace('programs/pump/src/',''), s['line'], s['code']) for s in f['sites']]}")
    else:
        print(f"{w:#x} {W['bytes']:6d} -> ??")
