#!/usr/bin/env python3
"""irdiff.py A.ll B.ll [fnsubstr]: diff one function's IR after canonical renaming of %values/labels and metadata ids."""
import re, sys, difflib
fn = sys.argv[3] if len(sys.argv) > 3 else 'multi_hop_curve8swap_hop17h'
def body(p):
    t = open(p).read()
    m = re.search(r'^define[^\n]*' + fn + r'[^\n]*$', t, re.M); s = m.start(); e = t.index('\n}\n', s)
    return t[s:e + 2]
def canon(b):
    names = {}
    def nm(m):
        k = m.group(0)
        if k not in names: names[k] = '%%v%d' % len(names)
        return names[k]
    lines = []
    for l in b.split('\n'):
        l = re.sub(r'^("?[\w.$-]+"?):', lambda m: nm(re.match(r'.*', '%' + m.group(1).strip('"'))) + ':', l)
        l = re.sub(r'%("[^"]+"|[\w.$-]+)', nm, l)
        l = re.sub(r'!(\d+)\b', '!M', l)
        l = re.sub(r'#\d+\b', '#A', l)
        l = re.sub(r';\s*preds = .*$', '', l)
        lines.append(l.rstrip())
    return lines
a, b = canon(body(sys.argv[1])), canon(body(sys.argv[2]))
d = list(difflib.unified_diff(a, b, 'A', 'B', n=2, lineterm=''))
print('\n'.join(d) if d else 'IDENTICAL (canonical)')
