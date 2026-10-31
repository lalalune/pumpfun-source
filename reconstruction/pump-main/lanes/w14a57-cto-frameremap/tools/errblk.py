#!/usr/bin/env python3
"""errblk.py <lst> <dis> : per anchor error site (PumpError::name call), the name String slot, the to_string buf slot,
the formatter slot and the error code stored after it. lst = lst.py output, dis = odis.py output (same function)."""
import sys, re
lst = {int(l.split()[0], 16): l for l in open(sys.argv[1])}
dis = [(int(l[:4], 16), l[5:].strip()) for l in open(sys.argv[2])]
idx = {o: i for i, (o, _) in enumerate(dis)}
for o, l in sorted(lst.items()):
    if 'PumpError::name' not in l: continue
    i = idx[o]; name = None
    for j in range(i - 1, i - 6, -1):
        m = re.match(r'add64 r1, (-0x[0-9a-f]+)', dis[j][1])
        if m: name = m.group(1); break
    buf = fmt = code = None
    for j in range(i + 1, min(i + 80, len(dis))):
        t = dis[j][1]
        if buf is None and re.match(r'stdw \[r10 - (0x[0-9a-f]+)\], 0x1$', t): buf = '-' + hex(int(re.match(r'stdw \[r10 - (0x[0-9a-f]+)', t).group(1), 16) + 8)
        if 'Display' in lst.get(dis[j][0], '') and fmt is None: fmt = j
        m = re.match(r'stw \[r10 - 0x[0-9a-f]+\], (0x1[78][0-9a-f]{2})', t)
        if m and code is None: code = int(m.group(1), 16)
    print(f'{o:#06x} name {name} buf {buf} code {code}')
