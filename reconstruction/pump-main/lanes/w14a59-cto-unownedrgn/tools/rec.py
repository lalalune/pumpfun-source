#!/usr/bin/env python3
"""rec.py <res.jsonl> <main sha7> : record oracle rows into the shared ledger (skips already recorded keys)."""
import sys, json, subprocess, os
L = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a59-cto-unownedrgn/reconstruction/pump-main/log_attempt.py'
E = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a59-cto-unownedrgn/e')
res, sha = sys.argv[1], sys.argv[2]
BASE = float(sys.argv[3]) if len(sys.argv) > 3 else 0.65698
for l in open(res):
    if not l.startswith('{'): continue
    d = json.loads(l); n = d['name']
    key = f'0x22a10-w14-{sha}-unownedrgn-{n}-v1'
    if subprocess.run(['python3', L, 'check', '--dedupe-key', key], capture_output=True).returncode != 0: continue
    try: edits = open(f'{E}/{n}.py').read().strip()[:600]
    except OSError: edits = ''
    err = d.get('error')
    st = 'compile-failed' if err else ('analyzed' if d.get('eq_main') or n == 'm0' else ('rejected' if d["ratio"] <= BASE or d['bytes'] != 27400 else 'built'))
    note = f"raw-IR capture + rx opt/llc oracle on main {sha} (m0 reproduces main @27400): " + ('compile error' if err else f"ratio {d['ratio']} bytes {d['bytes']} slots {d['slots_diff']}")
    data = dict(output='oracle', target=dict(ratio=d.get('ratio'), slots_diff=d.get('slots_diff'), cand_bytes=d.get('bytes')), notes=note)
    subprocess.run(['python3', L, 'record', '--lane', 'w14a59-cto-unownedrgn', '--approach', 'unownedrgn', '--target', '0x22a10', '--dedupe-key', key,
                    '--hypothesis', f'unownedrgn region-local spelling {n}: {edits}', '--status', st, '--data', json.dumps(data)], capture_output=True)
    print('recorded', key, st)
