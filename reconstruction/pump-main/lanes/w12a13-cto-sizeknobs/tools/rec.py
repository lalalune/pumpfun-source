#!/usr/bin/env python3
"""rec.py: record finished trials (res/*.json) in the shared ledger once each."""
import json, os, subprocess, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import knobs, genes
LANE = 'w12a13-cto-sizeknobs'
OUT = os.path.expanduser(f'~/.cache/pumpfun-reconstruction/lanes/{LANE}')
L = f'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/{LANE}/reconstruction/pump-main/log_attempt.py'
BASE = {'main': (27400, 0.43919, '8cd7695c3fc638fc'), 'k4': (27384, 0.4525, '07c7e215dbe32e7b'), 'j3': (27312, 0.45251, 'a0a2d2146fd9b1b8'), 'L1': (27400, 0.45147, '784bea21ed580b15'), 'L2': (27400, 0.45177, '6892c2a15de3ba6a'), 'C2': (27392, 0.45213, 'af95f0c58856b50c'), 'C3': (27384, 0.47618, 'cabdd7a55d964b6a'), 'Av': (27392, 0.48569, None), 'A2': (27384, 0.48607, None), 'D': (27400, 0.48652, None), 'M2': (27400, 0.48742, None)}
done = set(open(f'{OUT}/res/recorded.txt').read().split()) if os.path.exists(f'{OUT}/res/recorded.txt') else set()
MAIN7 = '20a1ae9'


def desc(n):
    if n in knobs.K:
        a, b = knobs.K[n][0]
        return f'{n}: {a[:90]} -> {b[:90]}'
    return n


for f in sorted(glob.glob(f'{OUT}/res/*.json')):
    r = json.load(open(f))
    name = r['name']
    if name in done or 'ok' not in r:
        continue
    base = r['base'] if r['base'] in BASE else ('Av' if r['base'].endswith('Av_b53cbd.rs') else 'A2' if r['base'].endswith('A2_6f262f.rs') else 'D' if r['base'].endswith('D_d7acbb.rs') else 'M2' if r['base'].endswith('main_now.rs') else 'custom')
    key = f"0x22a10-w12-{MAIN7}-sizeknob-{base}-{'+'.join(r['knobs']) or 'base'}-v1"
    hyp = (f"size-knob catalog: {base} + " + '; '.join(desc(n) for n in r['knobs'])) if r['knobs'] else f'size-knob catalog base {base} on main {MAIN7}'
    if r.get('ok'):
        bb, br, bsha = BASE.get(base, (None, None, None))
        same = ((r.get('sha') == bsha) if bsha else (r.get('bytes') == bb and r.get('ratio') == br)) and bool(r['knobs'])
        if same:
            status = 'rejected'
        elif r['bytes'] == 27400 and br is not None and r['ratio'] > 0.43919 and not r['losses'] and r['raw_losses_n'] == 0:
            status = 'partial'
        else:
            status = 'built'
        notes = f"admin_cto {r['bytes']} B ({r['bytes']-bb:+d} vs {base}) ratio {r['ratio']} ({r['ratio']-br:+.5f}); frame {r.get('frame')}; hop {r.get('hop_ratio')}/{r.get('hop_slots')}" if bb else f"admin_cto {r['bytes']} B ratio {r['ratio']}"
        data = {'output': r.get('out'), 'normalized': r['normalized'], 'raw': r['raw'], 'losses': r['losses'],
                'raw_losses_count': r['raw_losses_n'], 'target': {'ratio': r['ratio'], 'slots_diff': r.get('slots'), 'cand_bytes': r['bytes']},
                'notes': notes}
    else:
        status = 'compile-failed' if 'error' in r and 'apply' not in str(r.get('error')) else 'analyzed'
        data = {'notes': str(r.get('error'))[:400]}
    cmd = ['python3', L, 'record', '--lane', LANE, '--approach', 'size-knob-catalog', '--target', '0x22a10', '--dedupe-key', key,
           '--hypothesis', hyp, '--status', status, '--data', json.dumps(data)]
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode == 0 or 'duplicate' in (p.stdout + p.stderr).lower():
        open(f'{OUT}/res/recorded.txt', 'a').write(name + '\n')
    else:
        print('record failed', name, (p.stdout + p.stderr)[-300:])
print('recorded through', len(done))
