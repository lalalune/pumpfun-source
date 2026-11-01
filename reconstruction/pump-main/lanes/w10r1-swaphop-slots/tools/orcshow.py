#!/usr/bin/env python3
"""orcshow.py <orc-name|path.o|unstripped.so>: emit a win.py-show-like diff (orig vs candidate) for census tools."""
import sys, os, re, subprocess, difflib
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-slots')
L = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
arg = sys.argv[1]
def norm(i):
    i = re.sub(r'\s*<[^>]*>$', '', i).strip()
    i = re.sub(r'^call -?0x[0-9a-f]+', 'call X', i)
    i = re.sub(r'^(lddw r\d+), 0x[0-9a-f]+', r'\1, X', i)
    return i
orig = [(int(a, 16), norm(i)) for a, i in (l.split(None, 1) for l in open(O + '/orig.txt') if l.startswith('0x'))]
if arg.endswith('.so'):
    out = subprocess.run(['python3', './worktrees/w10r1-swaphop-slots/reconstruction/harness/win.py', 'show', '0x5b3b0', '--cand', arg, '--sym', 'multi_hop_curve::swap_hop$', '--full'], capture_output=True, text=True).stdout
    cand = []
    for ln in out.splitlines():
        m = re.match(r'^([-+ ]) (0x[0-9a-f]+)? +(0x[0-9a-f]+)? +(.*)$', ln)
        if m and m.group(3) and m.group(1) in ' +': cand.append((int(m.group(3), 16), norm(m.group(4))))
else:
    o = arg if arg.endswith('.o') else O + '/orc/' + arg + '/m.o'
    secs = subprocess.run([L + '/llvm-objdump', '-h', o], capture_output=True, text=True).stdout
    sec = next(l.split()[1] for l in secs.splitlines() if 'multi_hop_curve8swap_hop17h' in l and '.rel' not in l)
    dis = subprocess.run([L + '/llvm-objdump', '-d', '--no-show-raw-insn', '-j', sec, o], capture_output=True, text=True).stdout
    cand = []
    for ln in dis.splitlines():
        m = re.match(r"^\s*([0-9]+):\t(\S.*)$", ln)
        if m: cand.append((int(m.group(1), 10) * 8, norm(m.group(2))))
sm = difflib.SequenceMatcher(None, [x[1] for x in orig], [x[1] for x in cand], autojunk=False)
print(f'ratio {sm.ratio():.5f}')
for t, i1, i2, j1, j2 in sm.get_opcodes():
    if t == 'equal':
        for k in range(i2 - i1): print(f'  {orig[i1+k][0]:#x} {cand[j1+k][0]:#x}  {orig[i1+k][1]}')
    else:
        for k in range(i1, i2): print(f'- {orig[k][0]:#x}          {orig[k][1]}')
        for k in range(j1, j2): print(f'+          {cand[k][0]:#x}  {cand[k][1]}')
