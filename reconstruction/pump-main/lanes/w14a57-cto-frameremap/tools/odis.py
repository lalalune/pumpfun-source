#!/usr/bin/env python3
"""odis.py <so> {orig|cand} : plain window-relative disassembly of admin_cto::execute (0x22a10) for orig or a candidate."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'harness'))
from win import objdump_text, Cand, demangle
W = 0x22a10
if sys.argv[2] == 'orig':
    p = str(Path(__file__).resolve().parents[5] / 'evidence/original/pump/deployed.so'); s, n = W, 27400
    txt = objdump_text(p, s, s + n)
else:
    c = Cand(sys.argv[1]); s, n = [(s, n) for s, n, nm in c.funcs if re.search(r'admin_cto.*execute', demangle(nm))][0]
    txt = objdump_text(c.path, s, s + n)
for a, t in sorted(txt.items()):
    print('%04x %s' % (a - s, t))
