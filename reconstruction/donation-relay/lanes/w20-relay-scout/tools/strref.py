#!/usr/bin/env python3
"""strref.py <elf> <substring>: every code and data reference to rodata strings containing <substring>, with function and the next line-number store."""
import sys, os, re, struct, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relaylib import Elf
import relay
p, sub = sys.argv[1], sys.argv[2].encode()
e = Elf(p); ro = e.sec['.rodata']; b = e.b[ro['off']:ro['off'] + ro['size']]
hits = [ro['addr'] + m.start() for m in re.finditer(re.escape(sub), b)]
fs = e.functions(); starts = [a for a, _ in fs]
for h in hits:
    print(f'string at {h:#x}: {b[h - ro["addr"] - 10:h - ro["addr"] + len(sub) + 10]!r}')
    ins = e.insns(); idx = {x[0]: k for k, x in enumerate(ins)}
    for k, (a, op, regs, o, imm, n) in enumerate(ins):
        if op == 0x18 and a in e.rel and e.lddw(a) == h:
            f = starts[bisect.bisect_right(starts, a) - 1]
            near = []
            for j in range(max(0, k - 14), min(len(ins), k + 14)):
                x = ins[j]
                if (x[1] in (0xb7, 0x62, 0x7a)) and 1 <= x[4] <= 400:
                    near.append((hex(x[0]), hex(x[1]), x[3], x[4]))
            print(f'  lddw at {a:#x} in fn {f:#x}: small imms near {near[:8]}')
    d = e.sec['.data.rel.ro']
    for off in sorted(e.rel):
        if d['addr'] <= off < d['addr'] + d['size'] and e.ptr(off) == h:
            ln, col = struct.unpack_from('<II', e.b, d['off'] + off - d['addr'] + 16)
            print(f'  data ref at {off:#x}: len {struct.unpack_from("<Q", e.b, d["off"] + off - d["addr"] + 8)[0]} line {ln} col {col}')
