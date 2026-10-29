#!/usr/bin/env python3
"""Classify collected sources: cashback fn text, outside-cashback equality with pristine, built-before."""
import hashlib, json, re, sys
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
SWARM = LANE.parent.parent
PRIS = (SWARM / 'baselines/pristine-ws/programs/pump-amm/src/instructions/swap/sell.rs').read_text()


def split(t):
    i = t.find('fn cashback')
    if i < 0:
        return None, None
    # function starts at line start
    s = t.rfind('\n', 0, i) + 1
    # find end: first line that is exactly '}' after s
    m = re.search(r'\n}\n', t[s:])
    e = s + m.end() if m else len(t)
    return t[s:e], t[:s] + '@@CASHBACK@@' + t[e:]


pc, po = split(PRIS)
built = set()
for l in (SWARM / 'ATTEMPTS.jsonl').read_text().splitlines():
    e = json.loads(l)
    if e.get('schema') == 'amm-sell-attempt-v1':
        built.add(e['inputs']['sell'])
man = json.loads((LANE / 'work/manifest.json').read_text())
rows = []
for h, origins in man.items():
    t = (LANE / 'src' / f'{h}.rs').read_text(errors='replace')
    c, o = split(t)
    rows.append({'sha': h, 'outside_eq': o == po, 'cb_sha': hashlib.sha256(c.encode()).hexdigest()[:16] if c else None,
                 'cb_lines_eq': c is not None and c.count('\n') == pc.count('\n'),
                 'built': h in built, 'swarm_origin': all('amm-sell-swarm' in x for x in origins),
                 'origin': origins[0]})
(LANE / 'work/classify.json').write_text(json.dumps(rows, indent=1))
import collections
print('total', len(rows))
print('outside_eq', sum(r['outside_eq'] for r in rows))
print('built', sum(r['built'] for r in rows), 'swarm-only origin', sum(r['swarm_origin'] for r in rows))
print('distinct cashback', len({r['cb_sha'] for r in rows}))
nb = [r for r in rows if not r['built'] and not r['swarm_origin']]
print('non-swarm, unbuilt', len(nb), 'of which outside_eq', sum(r['outside_eq'] for r in nb), 'distinct cb', len({r['cb_sha'] for r in nb}))
