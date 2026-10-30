#!/usr/bin/env python3
"""Rank the size-changing diff sites of an equal-size candidate by how many slots they misalign.

For every difflib hunk whose byte length differs between original and candidate (a "site"), and
for every pair of sites, recompute how many equal instructions would sit at the original offset
if those sites had equal length. Prints the best single sites and pairs: what a fix there is worth
in slots_diff, all else unchanged. Input: a win.py-show-like diff (win.py show --full, orcshow.py).
usage: shift_sites.py <show.txt> [--top N]"""
import re, sys, difflib, itertools
o, c = [], []
for ln in open(sys.argv[1]).read().splitlines():
    m = re.match(r'^([-+ ]) (0x[0-9a-f]+)? +(0x[0-9a-f]+)? +(.*)$', ln)
    if not m or not (m.group(2) or m.group(3)): continue
    tag, oa, ca, ins = m.groups(); ins = re.sub(r'\s*<[^>]*>$', '', ins).strip()
    if tag in ' -': o.append((int(oa, 16), ins))
    if tag in ' +': c.append((int(ca, 16), ins))
top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 12
sz = lambda i: 2 if i.startswith('lddw') else 1
sm = difflib.SequenceMatcher(None, [x[1] for x in o], [x[1] for x in c], autojunk=False)
runs, sites, cum = [], [], 0   # runs: (site_count_before, cum_shift, slots)
for t, i1, i2, j1, j2 in sm.get_opcodes():
    if t == 'equal':
        runs.append((len(sites), cum, sum(sz(o[k][1]) for k in range(i1, i2))))
    else:
        d = sum(sz(c[k][1]) for k in range(j1, j2)) - sum(sz(o[k][1]) for k in range(i1, i2))
        if d:
            sites.append((o[i1][0] - o[0][0] if i1 < len(o) else -1, d, i2 - i1, j2 - j1)); cum += d
def aligned(zero):
    tot = 0
    for nb, s, n in runs:
        s2 = s - sum(sites[k][1] for k in zero if k < nb)
        if s2 == 0: tot += n
    return tot
base = aligned(())
print(f'aligned equal slots now: {base}; sites with a length change: {len(sites)}')
single = sorted(((aligned((k,)) - base, k) for k in range(len(sites))), reverse=True)[:top]
print('best single sites (orig offset, slot delta cand-orig, -orig/+cand insns): gain')
for g, k in single: print(f'  {sites[k][0]:#7x} {sites[k][1]:+3d} -{sites[k][2]}/+{sites[k][3]}: {g:+d}')
pairs = sorted(((aligned((a, b)) - base, a, b) for a, b in itertools.combinations(range(len(sites)), 2)), reverse=True)[:top]
print('best pairs: gain')
for g, a, b in pairs: print(f'  {sites[a][0]:#7x}({sites[a][1]:+d}) + {sites[b][0]:#7x}({sites[b][1]:+d}): {g:+d}')
