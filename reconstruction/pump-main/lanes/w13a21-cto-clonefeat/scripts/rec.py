#!/usr/bin/env python3
"""rec.py <base_sha7> <base_ratio> <resultfile> [hypothesis-prefix]: record each trial.sh result line in the shared ledger
(status rejected unless ratio > base at 27,400 B, then partial)."""
import sys, json, re, subprocess
from pathlib import Path
L = Path(__file__).resolve().parents[3] / "log_attempt.py"
base, bratio, rf = sys.argv[1], float(sys.argv[2]), sys.argv[3]; pre = sys.argv[4] if len(sys.argv) > 4 else ''
G = {}
exec(Path(__file__).with_name('var.py').read_text().split('crate = Path')[0].replace('import sys', ''), G)
for line in open(rf):
    m = re.match(r'^(\S+) (\{.*\}) cf=spill/reg = (\d+)/(\d+)', line)
    if not m: continue
    name, met, s, r = m.group(1), json.loads(m.group(2)), m.group(3), m.group(4)
    st = 'partial' if met['bytes'] == 27400 and met['ratio'] > bratio else 'rejected'
    key = f'0x22a10-w13-{base}-clonefeat-{name}-v1'
    if json.loads(subprocess.run(['python3', str(L), 'check', '--dedupe-key', key], capture_output=True, text=True).stdout)['duplicate']:
        continue
    data = {'target': {'ratio': met['ratio'], 'cand_bytes': met['bytes'], 'slots_diff': met.get('slots_diff')},
            'notes': f"capture build (no score); clonefeat {s}/{r}; abs {met['abs_ratio']}; base {base} {bratio}"}
    subprocess.run(['python3', str(L), 'record', '--lane', 'w13a21-cto-clonefeat', '--approach', 'regalloc-clonefeat', '--target', '0x22a10',
                    '--dedupe-key', key, '--hypothesis', f'{pre}{name}', '--status', st, '--data', json.dumps(data)], capture_output=True)
    print('recorded', key, st)
