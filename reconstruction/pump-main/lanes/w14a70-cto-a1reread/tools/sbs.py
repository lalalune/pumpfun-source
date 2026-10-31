#!/usr/bin/env python3
"""sbs.py <unstripped.so> lo hi [--masked]: side-by-side aligned disassembly of orig vs candidate admin_cto::execute
over window offsets [lo,hi) (frame/regs/jumps optionally masked for alignment). Calls named."""
import sys, re, difflib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'harness'))
from win import objdump_text, Cand, demangle
c = Cand(sys.argv[1]); lo = int(sys.argv[2], 16); hi = int(sys.argv[3], 16)
ORIG = Path(__file__).resolve().parents[4].parent / 'evidence/original/pump/deployed.so'
s, n = [(s, n) for s, n, nm in c.funcs if re.search(r'admin_cto.*execute', demangle(nm))][0]
names = {a: re.sub(r'::h[0-9a-f]{16}$', '', demangle(nm)).split('::')[-2:] for a, _, nm in c.funcs}
def dis(path):
    out = []
    for a, t in sorted(objdump_text(path, s + lo, s + hi).items()):
        m = re.match(r'call (-?0x[0-9a-f]+|-?\d+)$', t.split(' <')[0])
        if m:
            tgt = a + 8 + int(m.group(1), 0) * 8
            if tgt in names: t = 'call ' + '::'.join(names[tgt])
        t = re.sub(r'\s*<[^>]*>', '', t)
        out.append((a - s, t))
    return out
o = dis(ORIG); k = dis(c.path)
def key(t, lvl):
    if lvl >= 1: t = re.sub(r'r10 ?([+-]) ?0x[0-9a-f]+', 'r10+F', t)
    if lvl >= 2: t = re.sub(r'\br\d\b', 'R', t)
    if lvl >= 3: t = re.sub(r'[+-]0x[0-9a-f]+$', 'J', t)
    return t
lvl = 3
sm = difflib.SequenceMatcher(None, [key(t, lvl) for _, t in o], [key(t, lvl) for _, t in k], autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    for d in range(max(i2 - i1, j2 - j1)):
        a = o[i1 + d] if i1 + d < i2 else None; b = k[j1 + d] if j1 + d < j2 else None
        at = '%04x %-44s' % (a[0], a[1][:44]) if a else ' ' * 49
        bt = '%04x %s' % (b[0], b[1][:50]) if b else ''
        mark = '  ' if tag == 'equal' and a[1] == b[1] else ('~ ' if tag == 'equal' else '! ')
        print(mark + at + ' | ' + bt)
