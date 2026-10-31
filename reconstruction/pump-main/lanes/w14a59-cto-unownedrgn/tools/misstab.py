#!/usr/bin/env python3
"""misstab.py <sbs full listing> lo:hi[:label] ... : per-region miss classification of a whole-function sbs.py/osbs.py
alignment (frame/regs/jumps masked). Classes: eq; frame (only r10 displacement differs); reg (only registers);
jump (only jump offset); call (only call target imm, i.e. layout shift); mixed; extra (cand-only insn); missing (orig-only)."""
import sys, re, collections
rows = []
last = 0
for l in open(sys.argv[1]):
    m, rest = l[:2], l[2:].rstrip('\n')
    a, b = rest.split(' | ', 1)
    ao = a[:4].strip(); bo = b[:4].strip()
    at = a[5:].strip(); bt = b[5:].strip()
    if ao: last = int(ao, 16)
    rows.append((m, last, at if ao else None, bt if bo else None))
def cls(a, b):
    if a is None: return 'extra'
    if b is None: return 'missing'
    if a == b: return 'eq'
    ka = re.sub(r'\[r10 - 0x[0-9a-f]+\]', 'F', a); kb = re.sub(r'\[r10 - 0x[0-9a-f]+\]', 'F', b)
    if ka == kb: return 'frame'
    ra = re.sub(r'\br\d\b', 'R', a); rb = re.sub(r'\br\d\b', 'R', b)
    if ra == rb: return 'reg'
    ja = re.sub(r'[+-]0x[0-9a-f]+$', 'J', a); jb = re.sub(r'[+-]0x[0-9a-f]+$', 'J', b)
    if ja == jb: return 'jump' if not a.startswith('call') else 'call'
    return 'mixed'
K = ['eq', 'frame', 'reg', 'jump', 'call', 'mixed', 'extra', 'missing']
print('| orig region | what | ' + ' | '.join(K) + ' |'); print('| --- | --- |' + ' ---: |' * len(K))
for spec in sys.argv[2:]:
    p = spec.split(':'); lo, hi = int(p[0], 16), int(p[1], 16); lab = p[2] if len(p) > 2 else ''
    c = collections.Counter(cls(a, b) for m, o, a, b in rows if lo <= o < hi)
    print(f'| {lo:#x}-{hi:#x} | {lab} | ' + ' | '.join(str(c[k]) for k in K) + ' |')
