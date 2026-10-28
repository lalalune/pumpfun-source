import sys
sys.path.insert(0, '.')
from an import *
C = load_cand(sys.argv[1])
O = load_orig()
M = matches(O, C)
mc = {a: st for st, ms in M.items() for a in ms}
pat = sys.argv[2] if len(sys.argv) > 2 else 'lib.rs'
rows = []
for a, f in C.items():
    for s in f['sites']:
        if pat in s['path']:
            rows.append((s['path'], s['line'] or 0, a, f['bytes'], f['name'], s['code'], mc.get(a)))
rows.sort()
for p, l, a, n, nm, code, m in rows:
    print(f"{p.replace('programs/pump/src/','')}:{l:<5} {a:#8x} {n:6d} code={code} {'MATCHED '+hex(m) if m else '':16s} {nm[:110]}")
