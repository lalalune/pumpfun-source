#!/usr/bin/env python3
"""Layered diff of a win.py `show --full` output.

Level 0: raw normalized tokens (as win.py). Level 1: registers abstracted. Level 2: registers and
r10 stack offsets abstracted. Level 3: also branch displacements and immediates abstracted.
For each level, prints the number of differing instructions (difflib opcodes), so the census says
how much residual is explained by register choice, by stack-slot choice, and by everything else.
usage: abstract_diff.py <show.txt> [--level N --hunks]
"""
import re, sys, difflib
o, c = [], []
for ln in open(sys.argv[1]).read().splitlines():
    m = re.match(r'^([-+ ]) (0x[0-9a-f]+)? +(0x[0-9a-f]+)? +(.*)$', ln)
    if not m or not (m.group(2) or m.group(3)): continue
    tag, oa, ca, ins = m.groups()
    ins = re.sub(r'\s*<[^>]*>$', '', ins).strip()
    if tag in ' -': o.append((oa, ins))
    if tag in ' +': c.append((ca, ins))
def ab(i, lv):
    if lv >= 1: i = re.sub(r'\br\d+\b', 'R', i)
    if lv >= 2: i = re.sub(r'\[R - 0x[0-9a-f]+\]', '[S]', i)
    if lv >= 3:
        i = re.sub(r'([+-])0x[0-9a-f]+$', 'D', i) if i.split()[0].startswith('j') else i
        i = re.sub(r'call .*', 'call', i)
    return i
for lv in range(4):
    a = [ab(x[1], lv) for x in o]; b = [ab(x[1], lv) for x in c]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    nd = sum(max(i2-i1, j2-j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != 'equal')
    print(f'level {lv}: differing insns {nd}  ratio {sm.ratio():.5f}')
if '--hunks' in sys.argv:
    lv = int(sys.argv[sys.argv.index('--level')+1])
    a = [ab(x[1], lv) for x in o]; b = [ab(x[1], lv) for x in c]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for t, i1, i2, j1, j2 in sm.get_opcodes():
        if t == 'equal': continue
        print(f'\n## {t} orig {o[i1][0] if i1<len(o) else "end"} -{i2-i1} cand {c[j1][0] if j1<len(c) else "end"} +{j2-j1}')
        for k in range(i1, i2): print('  -', o[k][0], o[k][1])
        for k in range(j1, j2): print('  +', c[k][0], c[k][1])
