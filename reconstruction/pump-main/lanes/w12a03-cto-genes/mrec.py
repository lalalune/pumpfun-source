#!/usr/bin/env python3
"""Record multi-copy screen rows (multi.jsonl) in the shared ledger, once each.

  mrec.py <multi.jsonl>
Key: 0x22a10-w12-<main7>-screen-<name>-v1 (main7 = b5975fa for base tag nm2749). Status `analyzed`
(screen, not a landable build); data carries bytes/ratio of the copy.
"""
import json, subprocess, sys
from pathlib import Path

LEDGER = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a03-cto-genes/reconstruction/pump-main/log_attempt.py'
BASES = {'nm2749': 'b5975fa'}
seen = set()
for l in Path(sys.argv[1]).read_text().splitlines():
    r = json.loads(l)
    if r.get('bytes') is None or r['name'] in ('main', 'real_admin_cto') or r.get('base') not in BASES:
        continue
    key = f"0x22a10-w12-{BASES[r['base']]}-screen-{r['name']}-v1"
    if key in seen:
        continue
    seen.add(key)
    c = subprocess.run(['python3', LEDGER, 'check', '--dedupe-key', key], capture_output=True, text=True)
    try:
        if json.loads(c.stdout.strip().splitlines()[-1]).get('duplicate'):
            continue
    except Exception:
        pass
    data = {'output': f"multi.py batch {r['tag']} copy {r['module']}", 'target': {'ratio': r['ratio'], 'slots_diff': r.get('slots'), 'cand_bytes': r['bytes']},
            'notes': f"multi-copy screen on main {BASES[r['base']]} (0.45147/27400): genes {'+'.join(r['genes'])}; d_bytes {r.get('d_bytes')} d_ratio {r.get('d_ratio')}; frame_first {r.get('frame_first')}"}
    subprocess.run(['python3', LEDGER, 'record', '--lane', 'w12a03-cto-genes', '--approach', 'gene-harvest-screen', '--target', '0x22a10', '--dedupe-key', key,
                    '--hypothesis', f"gene set {'+'.join(r['genes'])} on main {BASES[r['base']]} (multi-copy screen)", '--status', 'analyzed', '--data', json.dumps(data)],
                   capture_output=True, text=True)
    print('recorded', key)
