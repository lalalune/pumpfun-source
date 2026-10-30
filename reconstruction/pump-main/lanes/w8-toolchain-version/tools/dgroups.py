#!/usr/bin/env python3
"""Per-crate hash-group order agreement (w8-toolchain-version).
Inside one dependency object, rustc orders mono items by symbol name, so instances of one generic
(same base name, different 17h<hash>) appear in hash order. That order depends only on that crate's
own -C metadata and its dependencies' (host, rustflags, profile, features, versions), not on the root crate.
usage: dgroups.py <unstripped.so> <refined.json> <target deps dir> [--verbose]
"""
import sys, re, json, subprocess, glob, os
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'layout-order-census/tools'))
import census as C
cand, refp, deps = sys.argv[1], sys.argv[2], sys.argv[3]
verbose = '--verbose' in sys.argv
RE = Path.home() / '.cache/solana/v1.44/platform-tools/llvm/bin/llvm-readelf'
owner = {}
for rl in sorted(glob.glob(os.path.join(deps, '*.rlib'))):
    crate = os.path.basename(rl)[3:].rsplit('-', 1)[0]
    out = subprocess.run([str(RE), '-s', '-W', rl], capture_output=True, text=True).stdout
    for line in out.splitlines():
        p = line.split()
        if len(p) >= 8 and p[3] == 'FUNC' and p[6] != 'UND':
            owner.setdefault(p[7], crate)
d = json.load(open(refp)); pair = {int(k, 16): int(v, 16) for k, v in d['pair'].items()}; inv = {v: k for k, v in pair.items()}
units = {}
for a, s, n in C.candidate_functions(cand): units.setdefault(a, n)
groups = defaultdict(list)
for a in sorted(units):
    n = units[a]
    if a in inv and n in owner:
        groups[(owner[n], re.sub(r'17h[0-9a-f]{16}E$', '', n))].append(a)
tot = ok = pt = pk = 0
per = defaultdict(lambda: [0, 0])
for (cr, b), m in sorted(groups.items()):
    if len(m) < 2: continue
    o = [inv[a] for a in m]
    good = o == sorted(o)
    tot += 1; ok += good; per[cr][0] += 1; per[cr][1] += good
    for i in range(len(o)):
        for j in range(i + 1, len(o)): pt += 1; pk += o[i] < o[j]
    if verbose and (not good or '--all' in sys.argv): print('  ', 'ok ' if good else 'BAD', cr, len(m), b[:90])
print(f'groups {tot} exact {ok} pairwise {pk}/{pt}')
print(' '.join(f'{c}:{v[1]}/{v[0]}' for c, v in sorted(per.items())))
