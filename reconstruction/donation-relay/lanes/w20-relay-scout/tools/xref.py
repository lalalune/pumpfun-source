#!/usr/bin/env python3
"""xref.py <elf> <addr>: internal callers of a function, by function start, with the symbol or DELTA name when known."""
import sys, os, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relaylib import Elf, symbols, demangle
import relay
p, addr = sys.argv[1], int(sys.argv[2], 16)
e = Elf(p); sy = symbols(p); names = relay.delta_names()
fs = sorted(sy) if sy else [a for a, _ in e.functions()]
nm = lambda a: demangle(sy[a][1]) if a in sy else (names.get(a, {}).get('name') or '?')
callers = {}
for a, op, regs, o, imm, n in e.insns():
    if op == 0x85 and (regs >> 4) == 1 and a not in e.sys and a + 8 + imm * 8 == addr:
        f = fs[bisect.bisect_right(fs, a) - 1]; callers[f] = callers.get(f, 0) + 1
print(f'{addr:#x} {nm(addr)[:100]}: {len(callers)} callers')
for f, c in sorted(callers.items()):
    print(f'  {f:#x} x{c} {nm(f)[:120]}')
