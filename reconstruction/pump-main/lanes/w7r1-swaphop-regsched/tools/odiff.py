#!/usr/bin/env python3
# odiff.py NAME [--from 0xORIGOFF --to 0xORIGOFF] [--hunks] : diff oracle output vs original (offsets relative to fn start)
import sys, os, re, subprocess, difflib, argparse
L = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-swaphop-regsched')
ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('--frm', type=lambda x: int(x, 0), default=0)
ap.add_argument('--to', type=lambda x: int(x, 0), default=1 << 30); ap.add_argument('--hunks', action='store_true')
a = ap.parse_args()
import json as _j
CM = _j.load(open(O + '/callmap.json'))
def dm(n): return re.sub(r'17h[0-9a-f]{16}E$', '', n).split('..')[-1][-48:]
def orig():
    out = []
    for l in open(O + '/orig.dis'):
        m = re.match(r'(0x[0-9a-f]+)\s+(.*)', l)
        if m:
            s = m.group(2).strip(); mm = re.match(r'call (-?0x[0-9a-f]+)', s)
            if mm: s = 'call ' + dm(CM.get(hex(int(m.group(1), 16) + 8 + int(mm.group(1), 16) * 8), '?'))
            out.append((int(m.group(1), 16) - 0x5b3b0, s))
    return out
def cand(name):
    d = O + '/orc/' + name
    txt = subprocess.run([L + '/llvm-objdump', '-d', '-r', '--no-show-raw-insn', d + '/m.o'], capture_output=True, text=True).stdout
    out = []; on = False
    for l in txt.splitlines():
        if re.match(r'^[0-9a-f]+ <.*multi_hop_curve8swap_hop17h', l): on = True; continue
        if on and re.match(r'^[0-9a-f]+ <(?!LBB)', l): break
        if not on: continue
        mr = re.match(r'^\s*[0-9a-f]+:\s+R_\w+\s+(\S+)', l)
        if mr:
            if out and out[-1][1].startswith('call'): out[-1] = (out[-1][0], 'call ' + dm(mr.group(1)))
            continue
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
        if m: out.append((int(m.group(1)) * 8, re.sub(r'\s*<[^>]*>', '', m.group(2).strip())))
    return out
def key(s):
    s = re.sub(r'^lddw (r\d+), .*', r'lddw \1', s)
    return s
o = orig(); c = cand(a.name)
sm = difflib.SequenceMatcher(None, [key(x[1]) for x in o], [key(x[1]) for x in c], autojunk=False)
tot = 0
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == 'equal':
        if not a.hunks and i2 > i1 and o[i1][0] <= a.to and o[i2 - 1][0] >= a.frm:
            for k in range(i2 - i1):
                if a.frm <= o[i1 + k][0] <= a.to: print(f'  {o[i1+k][0]:#06x} {c[j1+k][0]:#06x}  {o[i1+k][1]}')
        continue
    tot += max(i2 - i1, j2 - j1)
    lo = o[i1][0] if i1 < len(o) else 1 << 30
    if not (a.frm <= lo <= a.to): continue
    if a.hunks: print(f'{op} orig {lo:#06x} {i2-i1} cand {c[j1][0] if j1 < len(c) else -1:#06x} {j2-j1}'); continue
    for k in range(i1, i2): print(f'- {o[k][0]:#06x}        {o[k][1]}')
    for k in range(j1, j2): print(f'+        {c[k][0]:#06x}  {c[k][1]}')
print('total diff insns', tot, file=sys.stderr)
