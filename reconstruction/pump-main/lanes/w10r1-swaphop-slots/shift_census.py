#!/usr/bin/env python3
"""Explain slots_diff of an equal-size candidate: how many differing slots come from equal
instructions that sit at a shifted position (cumulative insert/delete offset != 0) versus
genuinely different instructions. Uses win.py `show --full` output; lddw counts as 2 slots.
usage: shift_census.py <show.txt>"""
import re, sys, difflib
o, c = [], []
for ln in open(sys.argv[1]).read().splitlines():
    m = re.match(r'^([-+ ]) (0x[0-9a-f]+)? +(0x[0-9a-f]+)? +(.*)$', ln)
    if not m or not (m.group(2) or m.group(3)): continue
    tag, oa, ca, ins = m.groups(); ins = re.sub(r'\s*<[^>]*>$', '', ins).strip()
    if tag in ' -': o.append((int(oa, 16), ins))
    if tag in ' +': c.append((int(ca, 16), ins))
o0, c0 = o[0][0], c[0][0]
sm = difflib.SequenceMatcher(None, [x[1] for x in o], [x[1] for x in c], autojunk=False)
shifted = 0; aligned_eq = 0; runs = []
for t, i1, i2, j1, j2 in sm.get_opcodes():
    if t != 'equal': continue
    for k in range(i2 - i1):
        so = o[i1 + k][0] - o0; sc = c[j1 + k][0] - c0
        n = 2 if o[i1 + k][1].startswith('lddw') else 1
        if so != sc: shifted += n
        else: aligned_eq += n
    d = (c[j1][0] - c0) - (o[i1][0] - o0)
    if d: runs.append((hex(o[i1][0] - o0), i2 - i1, d))
total = (o[-1][0] - o0) // 8 + (2 if o[-1][1].startswith('lddw') else 1)
print(f'total slots {total}; equal insns at same offset {aligned_eq}; equal insns shifted {shifted}; differing insns {total - aligned_eq - shifted}')
big = sorted(runs, key=lambda r: -r[1])[:15]
print('largest shifted equal runs (orig offset, insns, shift bytes):')
for r in big: print('  ', r)
