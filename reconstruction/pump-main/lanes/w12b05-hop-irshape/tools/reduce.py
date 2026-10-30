#!/usr/bin/env python3
"""reduce.py IN.ll OUT.ll [fnsubstr]: keep only the swap_hop define; other defines become declares."""
import re, sys
src, dst = sys.argv[1], sys.argv[2]
keep = sys.argv[3] if len(sys.argv) > 3 else 'multi_hop_curve8swap_hop17h'
t = open(src).read()
out = []
i = 0
n = len(t)
pat = re.compile(r'^define ([^\n]*)\{\n', re.M)
pos = 0
for m in pat.finditer(t):
    if m.start() < pos:
        continue
    out.append(t[pos:m.start()])
    end = t.index('\n}\n', m.end()) + 3
    hdr = m.group(1)
    if keep in hdr:
        out.append(t[m.start():end])
    else:
        h = hdr
        h = re.sub(r'\s+personality\s+ptr\s+@[\w.$]+', '', h)
        h = re.sub(r'\s+comdat(\([^)]*\))?', '', h)
        h = re.sub(r'\s+section\s+"[^"]*"', '', h)
        h = re.sub(r'\s+align\s+\d+', '', h)
        h = re.sub(r'\b(internal|private|linkonce_odr|weak_odr|hidden|dso_local|unnamed_addr|local_unnamed_addr)\s+', '', h)
        out.append('declare ' + h.rstrip() + '\n')
    pos = end
out.append(t[pos:])
r = ''.join(out)
r = re.sub(r'(?m)^@[^\n]* alias [^\n]*\n', '', r)
open(dst, 'w').write(r)
print(len(t), '->', len(r))
