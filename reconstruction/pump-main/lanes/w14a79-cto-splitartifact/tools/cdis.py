#!/usr/bin/env python3
"""cdis.py <unstripped.so> : admin_cto::execute disassembly with window-relative offsets (calls named)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'harness'))
from win import objdump_text, Cand, demangle
c = Cand(sys.argv[1])
s, n = [(s, n) for s, n, nm in c.funcs if re.search(r'admin_cto.*execute', demangle(nm))][0]
names = {}
for l in open(sys.argv[2]) if len(sys.argv) > 2 else []:
    if '; call' in l: names[int(l.split()[0], 16)] = l.split('; call ')[1].strip()
for a, t in sorted(objdump_text(c.path, s, s + n).items()):
    o = a - s
    if o in names: t = 'call ' + names[o]
    print('%04x %s' % (o, t))
