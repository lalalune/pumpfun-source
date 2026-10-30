#!/usr/bin/env python3
"""od.py NAME [--ctx N]: diff oracle orc/NAME/m.o swap_hop vs original (orig.txt); calls masked. Offsets relative to fn start."""
import sys, os, re, subprocess, difflib
L = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-hillclimb')
name = sys.argv[1]; ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 2
def norm(s):
    s = re.sub(r'\s+<[^>]*>', '', s.strip())
    s = re.sub(r'^call .*', 'call', s)
    s = re.sub(r'^lddw (r\d+), .*', r'lddw \1', s)
    return s
o = []
for l in open(O + '/orig.txt'):
    m = re.match(r'(0x[0-9a-f]+)\s+(.*)', l)
    if m: o.append((int(m.group(1), 16) - 0x5b3b0, norm(m.group(2))))
secs = subprocess.run([L + '/llvm-objdump', '-h', f'{O}/orc/{name}/m.o'], capture_output=True, text=True).stdout
sec = next(l.split()[1] for l in secs.splitlines() if 'multi_hop_curve8swap_hop17h' in l and '.rel' not in l)
d = subprocess.run([L + '/llvm-objdump', '-d', '--no-show-raw-insn', '-j', sec, f'{O}/orc/{name}/m.o'], capture_output=True, text=True).stdout
c = []
for l in d.splitlines():
    m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
    if m: c.append((int(m.group(1), 16) * 8 if not re.search('[a-f]', m.group(1)) else int(m.group(1), 16), norm(m.group(2))))
sm = difflib.SequenceMatcher(None, [x[1] for x in o], [x[1] for x in c], autojunk=False)
n = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal': continue
    n += max(i2 - i1, j2 - j1)
    print(f'@ orig {o[i1][0] if i1 < len(o) else -1:#x} cand {c[j1][0] if j1 < len(c) else -1:#x} {tag}')
    for k in range(max(0, i1 - ctx), i1): print('    ', o[k][1])
    for k in range(i1, i2): print('  - ', o[k][1])
    for k in range(j1, j2): print('  + ', c[k][1])
print('ratio', round(sm.ratio(), 5), 'diff', n)
