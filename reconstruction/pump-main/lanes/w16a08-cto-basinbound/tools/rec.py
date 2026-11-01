#!/usr/bin/env python3
"""rec.py [--dry] [names...]: one ledger row per basin (approach basinbound) from stack/ and cm/ results."""
import json, os, re, subprocess, sys
O = '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound'
L = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a08-cto-basinbound/reconstruction/pump-main/log_attempt.py'
dry = '--dry' in sys.argv
names = [a for a in sys.argv[1:] if not a.startswith('--')] or ['m0', 'F2', 'e1', 'hc', 'X1', 'T289n', 'B2', 'Y2', 'Z2', 'v14', 'v21', 'v26', 'ov1a']
SRC = {'T289n': '289 as if st.holder_reward{if !holder{err}} (w15a25 p289n)', 'X1': 'T289n + sharing_update=Some(new) (w15a25 p289n+sn)',
       'Y2': '298 arm split on a fresh hopt==Some(true) (w15a11 v27, w15a25 Y2)', 'Z2': 'w13a17 multi-way match on new with holder guards (w15a25 zmw)',
       'B2': '296 inside the holder arm + 289 on holder (w15a25 h296in+p289h)', 'F2': 'RAR + validate(..,has:bool,..) BPI-only probe (w15a25 rar+f2has; not landable)',
       'v14': 'holder=matches!(hopt,Some(true)) (and-1 basin, w15a11)', 'v21': '296 !hr&&!he&&holder (and-1 basin, w15a11)',
       'v26': '296 !st.holder_enabled==true (and-1 basin, w15a11)', 'ov1a': 'validate takes shared, non-holder arm yields if shared{st.creator}else{t} (w15a20)',
       'hc': 'w14a142 per-arm holder phi hphi+hcs (post-opt IR edit)', 'e1': 'w14a142/w15a08 e1 = hphi+hcs+hev (post-opt IR edit, keeps %0 live)',
       'm0': 'main 9bd38c7 calibration'}
def j(p):
    try: return json.load(open(p))
    except Exception: return {}
for n in names:
    raw = j(f'{O}/rx/{n}/res.json'); ar = j(f'{O}/stack/{n}.ar.json'); phr = j(f'{O}/stack/{n}.phr.json'); sh = j(f'{O}/stack/{n}.sh.json')
    cl = {}; nf = 0
    try:
        Ls = [json.loads(l) for l in open(f'{O}/cm/{n}.climb.log') if l.startswith('{')]; cl = Ls[-1]; nf = len([x for x in (cl.get('force') or '').split(',') if x])
    except Exception: pass
    jt = j(f'{O}/cm/{n}.joint.json'); jsh = j(f'{O}/cm/{n}.jsh.json')
    p2 = {}
    try:
        Ls = [json.loads(l) for l in open(f'{O}/cm/{n}p2.climb.log') if l.startswith('{')]; p2 = Ls[-1]
    except Exception: pass
    jt2 = j(f'{O}/cm/{n}p2.joint.json'); jsh2 = j(f'{O}/cm/{n}p2.jsh.json')
    ex = [(f['reg'], f['slot']) for jj in ar.get('ares', {}).get('joins', []) for f in jj.get('fix', [])]
    joint = max([x for x in (jt.get('Mhc'), jsh.get('Mshhc'), jt2.get('Mhc'), jsh2.get('Mshhc')) if x] or [0]) or None
    data = {'output': f'{O}/rx/{n}', 'target': {'ratio': raw.get('ratio'), 'slots_diff': raw.get('slots_diff'), 'cand_bytes': raw.get('bytes')},
            'M_raw': j(f'{O}/stack/{n}.ph.json').get('M'), 'restored': {'ratio': ar.get('ratio'), 'bytes': ar.get('bytes'), 'M': ar.get('M'), 'extra_livein': ex},
            'frame': {'Mhc': phr.get('Mhc'), 'Mshhc': sh.get('Mshhc')}, 'ra_pass1': {'ratio': cl.get('ratio'), 'bytes': cl.get('bytes'), 'forces': cl.get('force')},
            'ra_pass2': {'ratio': p2.get('ratio'), 'bytes': p2.get('bytes'), 'forces': p2.get('force')}, 'joint': joint,
            'notes': 'stacked bound: placement restore (ares.py) -> frame (alloca unshift + spill perm) -> sticky RA climb on the restored layout + joint perm; main refs M 2249 / Mhc 2300 / joint 2338'}
    key = f'0x22a10-w16-9bd38c7-basinbound-{n}-v1'
    hyp = f'stacked exact bound of the {n} validate basin: {SRC.get(n, n)}'
    cmd = ['python3', L, 'record', '--lane', 'w16a08-cto-basinbound', '--approach', 'basinbound', '--target', '0x22a10', '--dedupe-key', key,
           '--hypothesis', hyp, '--status', 'analyzed', '--data', json.dumps(data)]
    print(key, json.dumps(data)[:300])
    if not dry:
        r = subprocess.run(cmd, capture_output=True, text=True); print(r.stdout.strip()[-200:], r.stderr.strip()[-300:])
