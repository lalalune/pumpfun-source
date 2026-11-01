#!/usr/bin/env python3
"""accreg.py <name|fn.bin|main>... [--lo 0x3000 --hi 0x3800]: for every original instruction in [lo,hi) that uses r8 as a
load/store base (the accounts pointer in the original's sweep CPI clone chunk), find the skeleton-aligned candidate
instruction and report the candidate's base register. Also prints chunk M (masked tokens matched, difflib as scorer).
Experiment only."""
import sys, os, re, difflib, collections
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import sbpfdis as D, oracle
def blob(n):
    if n == 'orig': return oracle.orig_window()
    if n == 'main': return oracle.elf_fn(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'), oracle.KEEP)
    return open(n if os.path.exists(n) else T + '/../rx/' + n + '/fn.bin', 'rb').read()
def sk(s): return re.sub(r'r\d+', 'r', re.sub(r'0x[0-9a-f]+|-?\d+', 'N', s))
def base(s):
    m = re.search(r'\[r(\d+)([+-]0x[0-9a-f]+)\]', s)
    return (int(m.group(1)), m.group(2)) if m else None
a = sys.argv[1:]; lo, hi = 0x3000, 0x3800
if '--lo' in a: i = a.index('--lo'); lo = int(a[i + 1], 16); del a[i:i + 2]
if '--hi' in a: i = a.index('--hi'); hi = int(a[i + 1], 16); del a[i:i + 2]
O = D.d(blob('orig')); OK = [sk(x[1]) for x in O]
OT = oracle.mask(blob('orig'))
for n in a:
    C = D.d(blob(n)); CK = [sk(x[1]) for x in C]
    sm = difflib.SequenceMatcher(None, OK, CK, autojunk=False)
    amap = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('equal', 'replace') and i2 - i1 == j2 - j1:
            for k in range(i2 - i1): amap[i1 + k] = j1 + k
    cnt = collections.Counter(); tot = 0; unal = 0; ex = []
    for i, (off, s) in enumerate(O):
        if not (lo <= off < hi): continue
        b = base(s)
        if not b or b[0] != 8: continue
        tot += 1
        j = amap.get(i)
        if j is None: unal += 1; continue
        cb = base(C[j][1]); r = cb[0] if cb else None
        cnt[r] += 1
        if len(ex) < 6 and r != 8: ex.append(f'{off:x}:{s} ~ {C[j][0]:x}:{C[j][1]}')
    # chunk M (scorer tokens) in [lo,hi)
    CT = oracle.mask(blob(n)); sm2 = difflib.SequenceMatcher(None, OT, CT, autojunk=False)
    offs = []; acc = 0
    for x in OT: offs.append(acc); acc += len(x)
    chM = 0
    for blk in sm2.get_matching_blocks():
        for k in range(blk.size):
            if lo <= offs[blk.a + k] < hi: chM += 1
    print(f'{os.path.basename(n):14s} chunkM[{lo:x},{hi:x})={chM:4d} r8-base uses={tot} unaligned={unal} cand base regs: ' +
          ' '.join(f'r{k}:{v}' for k, v in cnt.most_common()) + ('  e.g. ' + ' | '.join(ex[:3]) if ex else ''))
