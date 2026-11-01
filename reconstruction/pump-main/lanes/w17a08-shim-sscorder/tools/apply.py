#!/usr/bin/env python3
"""apply.py <file> <edits.py>: edits.py defines E=[(old,new),...]; each old must occur exactly once; line count must not change."""
import sys
f, e = sys.argv[1], sys.argv[2]; g = {}; exec(open(e).read(), g)
t = open(f).read(); n0 = t.count('\n')
for o, n in g['E']:
    c = t.count(o)
    if c != 1: raise SystemExit(f'edit occurs {c} times: {o[:80]}')
    t = t.replace(o, n)
if t.count('\n') != n0: raise SystemExit('line count changed')
open(f, 'w').write(t); print('applied', len(g['E']))
