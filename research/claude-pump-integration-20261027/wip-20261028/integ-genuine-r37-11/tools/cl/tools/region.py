import sys
sys.path.insert(0, '.')
from an import *
from cmap import build
C = load_cand(sys.argv[1])
O = load_orig()
M = matches(O, C)
cp = build(O, C, M)
lo, hi = int(sys.argv[2], 0), int(sys.argv[3], 0)
for st in sorted(O):
    if lo <= st < hi:
        W = O[st]
        if st in M:
            tag = 'M  ' + C[M[st][0]]['name'][:100] + (f' (+{len(M[st])-1})' if len(M[st]) > 1 else '')
        elif st in cp:
            tag = 'cp ' + C[cp[st][0]]['name'][:100] + f" [{cp[st][1]}]"
        else:
            tag = '?'
        print(f"{st:#8x} {W['bytes']:6d} {[(s['path'].split('src/')[-1], s['line'], s['code']) for s in W['sites']]!s:50.50} {tag}")
