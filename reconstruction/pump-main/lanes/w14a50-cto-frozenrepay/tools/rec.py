#!/usr/bin/env python3
"""rec.py <res.jsonl> <main sha7> <main ratio> <desc>: bulk-record oracle rows into the shared ledger."""
import sys, json, subprocess, os
L = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a50-cto-frozenrepay/reconstruction/pump-main/log_attempt.py'
E = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a50-cto-frozenrepay/e')
res, sha, mr, desc = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
n_ok=0
for l in open(res):
    if not l.startswith('{'): continue
    d = json.loads(l); n = d['name']
    key = f'0x22a10-w14-{sha}-frozenrepay-{n}-v1'
    if subprocess.run(['python3', L, 'check', '--dedupe-key', key], capture_output=True).returncode != 0: continue
    try: edits = open(f'{E}/{n}.py').read().strip()[-500:]
    except OSError: edits = ''
    err = d.get('error')
    st = 'compile-failed' if err else ('analyzed' if d.get('eq_main') else ('rejected' if d['ratio'] <= mr or d['bytes'] != 27400 else 'partial'))
    note = f"raw-IR capture + opt/llc oracle on main {sha} ({mr}): " + ('compile error' if err else f"ratio {d['ratio']} bytes {d['bytes']} slots {d['slots_diff']}")
    data = dict(output='oracle', target=dict(ratio=d.get('ratio'), slots_diff=d.get('slots_diff'), cand_bytes=d.get('bytes')), notes=note)
    subprocess.run(['python3', L, 'record', '--lane', 'w14a50-cto-frozenrepay', '--approach', 'frozenrepay', '--target', '0x22a10', '--dedupe-key', key,
                    '--hypothesis', f'{desc} {n}: ...{edits}', '--status', st, '--data', json.dumps(data)], capture_output=True)
    n_ok+=1
print('recorded',n_ok)
