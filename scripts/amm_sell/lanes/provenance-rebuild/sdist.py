#!/usr/bin/env python3
"""Structural distance: like align_distance but masks lddw immediates and call targets (size-shift insensitive).
Usage: sdist.py OUT_DIR [OUT_DIR...]"""
import sys, difflib
from pathlib import Path
sys.path.insert(0, '/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm/harness')
import sell_score as S
import elf_reader

orig = elf_reader.Elf(S.ORIGINAL)
o_rows = S.listing(orig, S.SELL_START, S.SELL_SIZE)


def toks(rows):
    t = S.normalized_tokens(rows)
    out = []
    for x in t:
        if x.startswith('lddw'):
            out.append(' '.join(x.split()[:2]) + ' IMM')
        elif x.startswith('call'):
            out.append('call')
        else:
            out.append(x)
    return out


OT = toks(o_rows)


def sdist(d):
    sym = elf_reader.Elf(Path(d) / 'symbols.so')
    cand = elf_reader.Elf(Path(d) / 'candidate.so')
    s = S.find_sell(sym)
    ct = toks(S.listing(cand, s['start'], s['size']))
    m = difflib.SequenceMatcher(None, OT, ct, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in m.get_opcodes() if tag != 'equal'), s['size']


def show(d, ctx=0):
    sym = elf_reader.Elf(Path(d) / 'symbols.so'); cand = elf_reader.Elf(Path(d) / 'candidate.so')
    s = S.find_sell(sym); cr = S.listing(cand, s['start'], s['size']); ct = toks(cr)
    m = difflib.SequenceMatcher(None, OT, ct, autojunk=False)
    for tag, i1, i2, j1, j2 in m.get_opcodes():
        if tag == 'equal':
            continue
        print(f'--- {tag} orig[{o_rows[i1]["off"] if i1 < len(o_rows) else -1:#x}] x{i2-i1}  cand[{cr[j1]["off"] if j1 < len(cr) else -1:#x}] x{j2-j1}')
        for i in range(i1, i2): print('  -', f'{o_rows[i]["off"]:#06x}', o_rows[i]['text'])
        for j in range(j1, j2): print('  +', f'{cr[j]["off"]:#06x}', cr[j]['text'])


if __name__ == '__main__':
    if sys.argv[1] == "--show":
        show(sys.argv[2]); sys.exit()
    for d in sys.argv[1:]:
        try:
            print(*sdist(d), d)
        except Exception as e:
            print('ERR', e, d)


