import sys
sys.path.insert(0, '.')
from an import *
from cmap import aligned_calls
C = load_cand(sys.argv[1])
O = load_orig()
o = int(sys.argv[2], 0); c = int(sys.argv[3], 0)
pairs, r = aligned_calls(O[o], C[c])
print('ratio', r)
for t_o, t_c, tag in pairs:
    print(f"  {t_o:#x} ({O[t_o]['bytes'] if t_o in O else '?'}B {[(s['path'].split('src/')[-1], s['line']) for s in O[t_o]['sites']] if t_o in O else ''}) -> {t_c:#x} {C[t_c]['bytes'] if t_c in C else '?'}B {C[t_c]['name'][:90] if t_c in C else ''} {tag}")
