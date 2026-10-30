import sys, runpy
f, edits = sys.argv[1], sys.argv[2]
E = runpy.run_path(edits)['EDITS']
t = open(f).read()
for a, b in E:
    n = t.count(a)
    if n != 1: sys.exit(f'edit anchor count {n}: {a[:80]}')
    t = t.replace(a, b)
open(f, 'w').write(t)
