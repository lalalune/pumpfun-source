#!/usr/bin/env python3
"""Make hybrids: BASE sell.rs + one historical hunk each. Usage: mkhybrid.py BASE.rs TAG OUTQUEUE.json [--all]"""
import json, hashlib, sys, re
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
base_path, tag, outq = sys.argv[1], sys.argv[2], sys.argv[3]
BASE = Path(base_path).read_text().split('\n')
P = (LANE.parent.parent / 'baselines/pristine-ws/programs/pump-amm/src/instructions/swap/sell.rs').read_text().split('\n')
H = json.loads((LANE / 'work/hunks.json').read_text())
BAD = ['try_from_unchecked(user_volume_accumulator', '&user_volume_accumulator.key()', 'authority: user_volume_accumulator',
       'core::intrinsics']
d = LANE / 'hyb' / tag
d.mkdir(parents=True, exist_ok=True)
q = []
seen = set()
skipped = {'base-conflict': 0, 'bad': 0, 'macro-move': 0, 'noop': 0}
for h in H:
    s, e = h['start'] - 1, h['end']
    # base must equal pristine on hunk lines (otherwise conflicts with the base's own edit)
    if BASE[s:e] != P[s:e]:
        skipped['base-conflict'] += 1
        continue
    txt = '\n'.join(h['new'])
    if any(b in txt for b in BAD):
        skipped['bad'] += 1
        continue
    if h['mac_old'] != h['mac_new']:
        skipped['macro-move'] += 1
        continue
    new = BASE[:s] + h['new'] + BASE[e:]
    b = '\n'.join(new).encode()
    sh = hashlib.sha256(b).hexdigest()
    if sh in seen:
        skipped['noop'] += 1
        continue
    seen.add(sh)
    f = d / f'{h["start"]}-{h["end"]}-{sh[:12]}.rs'
    f.write_bytes(b)
    q.append({'file': str(f), 'hypothesis': f'{tag} + historical hunk L{h["start"]}-{h["end"]} (seen in {h["n"]} prior sources): '
              + ' | '.join(x.strip() for x in h['new'])[:300]})
Path(outq).write_text(json.dumps(q, indent=0))
print(len(q), skipped)
