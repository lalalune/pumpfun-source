#!/usr/bin/env python3
"""Hunk census of a win.py `show --full` diff: classify each replace/insert/delete hunk.

usage: census.py <show.txt> [--verbose]
Classes: jump-offset (only branch displacement differs), stack-slot (only [r10 - X] differs),
register (same opcodes, only register names differ), const (only immediates differ),
order (same multiset of instructions, different order), structure (anything else).
"""
import re, sys, collections
lines = open(sys.argv[1]).read().splitlines()
verbose = '--verbose' in sys.argv
hunks = []; cur = None
for ln in lines:
    m = re.match(r'^([-+ ]) (0x[0-9a-f]+)? +(0x[0-9a-f]+)? +(.*)$', ln)
    if not m or not (m.group(2) or m.group(3)):
        continue
    tag, oa, ca, ins = m.groups()
    ins = re.sub(r'\s*<[^>]*>$', '', ins).strip()
    if tag == ' ':
        if cur: hunks.append(cur); cur = None
        continue
    if cur is None: cur = {'o': [], 'c': [], 'oa': None, 'ca': None}
    if tag == '-':
        cur['o'].append(ins); cur['oa'] = cur['oa'] or oa
    else:
        cur['c'].append(ins); cur['ca'] = cur['ca'] or ca
if cur: hunks.append(cur)
def op(i): return i.split()[0]
def strip_regs(i): return re.sub(r'\br\d+\b', 'R', i)
def strip_stack(i): return re.sub(r'\[r10 - 0x[0-9a-f]+\]', '[r10-S]', i)
def strip_imm(i): return re.sub(r'(?<![r\w])-?0x[0-9a-f]+|(?<=, )-?\d+\b', 'I', i)
def classify(h):
    o, c = h['o'], h['c']
    if len(o) == len(c):
        if all(op(a) == op(b) for a, b in zip(o, c)):
            if all(op(a) in ('ja','jeq','jne','jgt','jge','jlt','jle','jsgt','jsge','jslt','jsle','jset') and re.sub(r'[+-]0x[0-9a-f]+$','',a)==re.sub(r'[+-]0x[0-9a-f]+$','',b) for a,b in zip(o,c)):
                return 'jump-offset'
            if all(strip_stack(a) == strip_stack(b) for a, b in zip(o, c)):
                return 'stack-slot'
            if all(strip_regs(a) == strip_regs(b) for a, b in zip(o, c)):
                return 'register'
            if all(strip_regs(strip_stack(a)) == strip_regs(strip_stack(b)) for a, b in zip(o, c)):
                return 'register+stack'
            if all(strip_imm(a) == strip_imm(b) for a, b in zip(o, c)):
                return 'const'
    if sorted(o) == sorted(c): return 'order'
    if sorted(map(strip_regs, o)) == sorted(map(strip_regs, c)): return 'order+register'
    if not o: return 'insert'
    if not c: return 'delete'
    return 'structure'
cnt = collections.Counter(); ins = collections.Counter()
for h in hunks:
    k = classify(h); h['k'] = k
    cnt[k] += 1; ins[k] += max(len(h['o']), len(h['c']))
print('hunks', len(hunks))
for k, v in cnt.most_common():
    print(f'{k:16s} hunks={v:4d} insns={ins[k]:5d}')
if verbose:
    for h in hunks:
        if h['k'] in ('jump-offset',): continue
        print(f"\n## {h['k']} orig {h['oa']} cand {h['ca']} -{len(h['o'])} +{len(h['c'])}")
        for i in h['o']: print('   -', i)
        for i in h['c']: print('   +', i)
