#!/usr/bin/env python3
import json, subprocess, sys
O = '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a23-cto-s3ovarm'
L = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a23-cto-s3ovarm/reconstruction/pump-main/log_attempt.py'
LANE = 'w16a23-cto-s3ovarm'
rows = json.load(open(O + '/w/table.json'))
only = sys.argv[1:]
for r in rows:
    if only and r['cell'] not in only: continue
    key = f"0x22a10-w16-5998913-s3ovarm-{r['cell']}-v1"
    note = (f"raw-IR oracle (capraw + rx opt/llc) on main 5998913 + e/S3n.py (S3n: 0.59599 @27416, M 1990, Mhc 2296, stacked 2347; main 2251/2302/2339). "
            f"raw {r['ratio']} @{r['bytes']}" + (f"; restored {r.get('ratio_rest')} @{r.get('bytes_rest')} M {r.get('M_raw')}->{r.get('M_rest')}, Mperm {r.get('Mperm_rest')}, Mhc {r.get('Mhc_rest')}, bb56.i live-in fixed by ares: {r.get('restored_livein')}, sharing call {r.get('share_call')}" if 'M_rest' in r else '') +
            f"; true LCS vs main ---{r.get('L---'):+d} r--{r.get('Lr--'):+d} -f-{r.get('L-f-'):+d} rf-{r.get('Lrf-'):+d} rfj{r.get('Lrfj'):+d} (S3n -136/-168/-8/-4/+3)" +
            (f"; byte-identical to {r['fold']}" if r['fold'] else '') + "; below S3n's Mhc and skeleton -> killed (kill test: none stacks above 2347)")
    data = {'output': f"{O}/rx/{r['cell']}", 'target': {'ratio': r['ratio'], 'slots_diff': None, 'cand_bytes': r['bytes']}, 'notes': note}
    cmd = ['python3', L, 'record', '--lane', LANE, '--approach', 's3ovarm', '--target', '0x22a10', '--dedupe-key', key,
           '--hypothesis', f"OV on S3n cell {r['cell']}: {r['desc']}", '--status', 'rejected', '--data', json.dumps(data)]
    p = subprocess.run(cmd, capture_output=True, text=True); print(r['cell'], p.returncode, (p.stdout + p.stderr).strip()[:160])
