#!/usr/bin/env python3
"""lst.py <unstripped.so> {orig|cand} : admin_cto::execute listing, window-relative offsets, calls named via the
candidate's symbol table (layout outside the window is identical, so original call targets resolve the same way).
Also marks error-code immediates (mov/st imm 6000..6200 or anchor 2000..2100) as 'E<code>'."""
import sys, struct, re, subprocess, os
from pathlib import Path
H = Path(__file__).resolve().parents[4] / 'harness'
sys.path.insert(0, str(H))
from score import original_windows  # noqa
from win import Cand, demangle  # noqa
W = 0x22a10
so, which = sys.argv[1], sys.argv[2]
c = Cand(so)
syms = {s: demangle(nm) for s, n, nm in c.funcs}
def short(nm):
    nm = re.sub(r'::h[0-9a-f]{16}$', '', nm)
    parts = nm.split('::')
    return '::'.join(parts[-3:])[:70]
if which == 'orig':
    raw = {x['start']: x for x in original_windows()}[W]['raw']; base = W
else:
    picks = [(s, n) for s, n, nm in c.funcs if re.search(r'admin_cto.*execute', demangle(nm))]
    base, n = picks[0]; raw = c.fn(base, n)
SDK = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump')
i = 0
while i < len(raw):
    op = raw[i]; ln = 16 if op == 0x18 else 8
    _, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
    txt = None
    if op == 0x85:
        if regs >> 4 == 1 or True:
            tgt = base + i + 8 + imm * 8
            txt = 'call ' + short(syms.get(tgt, hex(tgt) if regs >> 4 == 1 else 'sys:%x' % (imm & 0xffffffff)))
    print('%04x %02x %d %d %d %d%s' % (i, op, regs & 15, regs >> 4, off, imm, (' ; ' + txt) if txt else ''))
    i += ln
