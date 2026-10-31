#!/usr/bin/env python3
"""rec.py <res.jsonl> <main sha7> <main ratio> [hyp-prefix]: record oracle rows into the shared ledger (skips recorded keys)."""
import sys, json, subprocess, os
L = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a60-cto-s1rescan/reconstruction/pump-main/log_attempt.py'
E = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a60-cto-s1rescan/e')
res, sha, mr = sys.argv[1], sys.argv[2], float(sys.argv[3]); pre = sys.argv[4] if len(sys.argv) > 4 else 'sharing CPI structural form'
for l in open(res):
    if not l.startswith('{'): continue
    d = json.loads(l); n = d['name']
    key = f'0x22a10-w14-{sha}-s1rescan-{n}-v1'
    if subprocess.run(['python3', L, 'check', '--dedupe-key', key], capture_output=True).returncode != 0: continue
    try: edits = open(f'{E}/{n}.py').read().strip()[:500]
    except OSError: edits = ''
    err = d.get('error')
    st = 'compile-failed' if err else ('analyzed' if d.get('eq_main') or n == 'm0' else ('rejected' if d['ratio'] <= mr or d['bytes'] != 27400 else 'built'))
    note = f"raw-IR capture + rx opt/llc oracle on main {sha} (m0 reproduces {mr} @27400): " + ('compile error' if err else f"ratio {d['ratio']} bytes {d['bytes']} slots {d['slots_diff']}") + (' ' + d['note'] if d.get('note') else '')
    data = dict(output='oracle', target=dict(ratio=d.get('ratio'), slots_diff=d.get('slots_diff'), cand_bytes=d.get('bytes')), notes=note)
    subprocess.run(['python3', L, 'record', '--lane', 'w14a60-cto-s1rescan', '--approach', 's1rescan', '--target', '0x22a10', '--dedupe-key', key,
                    '--hypothesis', f'{pre} {n}: {edits}', '--status', st, '--data', json.dumps(data)], capture_output=True)
    print('recorded', key, st)
