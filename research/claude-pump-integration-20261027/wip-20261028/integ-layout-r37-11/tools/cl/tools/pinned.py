import sys
sys.path.insert(0, '.')
from an import *
C = load_cand(sys.argv[1])
O = load_orig()
M = matches(O, C)
for st, ms in sorted(M.items()):
    if O[st]['sites']:
        print(hex(st), O[st]['bytes'], [(s['path'].split('src/')[-1], s['line']) for s in O[st]['sites']], [(hex(a), C[a]['name'][:70], [(s['path'].split('src/')[-1], s['line']) for s in C[a]['sites']]) for a in ms])
