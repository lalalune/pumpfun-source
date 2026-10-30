#!/usr/bin/env python3
"""Record every hill-climb result row in the shared ledger (skips keys already recorded)."""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[4]
L = WT / 'reconstruction/pump-main/log_attempt.py'
sys.path.insert(0, str(HERE))
import hc, mutgen  # noqa: E402

BASE_SHA = 'd73adf73aff7ddce'
DONE = hc.HC / 'ledger_done.txt'


def desc(key):
    cfg = mutgen.parse(key)
    diffs = [f'{d}={cfg[d]}' for d in 'FTABNQO' if cfg[d] != mutgen.BASE[d]]
    return ','.join(diffs) or 'base'


def main():
    done = set(DONE.read_text().split()) if DONE.exists() else set()
    for key, r in hc.load().items():
        if key in done:
            continue
        dk = f'0x80df8-main-2162b3b-hc-{key}-v1'
        if r['status'] != 'ok':
            status, note = 'compile-failed', r.get('err', '')[:300]
            tgt = {}
        else:
            same = r['fn_sha'] == BASE_SHA
            status = 'rejected' if same or r['ratio'] <= 0.92 else 'partial'
            note = ('byte-identical function to base 2162b3b' if same else
                    f"{r['cand_bytes']} B ratio {r['ratio']} slots_diff {r.get('slots_diff')} calls {r['calls_candidate']} fn {r['fn_sha']}")
            tgt = {'slots_diff': r.get('slots_diff'), 'ratio': r['ratio'], 'cand_bytes': r['cand_bytes']}
        data = {'output': str(hc.HC / 'out' / key), 'target': tgt, 'notes': f'hill-climb config {key} ({desc(key)}): {note}',
                'tools': 'reconstruction/pump-main/lanes/w7r1-v3buycosts-hillclimb/tools/mutgen.py'}
        cmd = [sys.executable, str(L), 'record', '--lane', 'w7r1-v3buycosts-hillclimb', '--approach', 'mutation-hillclimb',
               '--target', '0x80df8', '--dedupe-key', dk, '--hypothesis',
               f'Spelling mutation {desc(key)} of v3_buy_costs moves the sret register-allocation tie', '--status', status,
               '--data', json.dumps(data)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode == 0 or 'already' in (p.stderr + p.stdout).lower() or 'duplicate' in (p.stderr + p.stdout).lower():
            done.add(key)
        else:
            print('record failed', key, p.stderr[-300:])
    DONE.write_text('\n'.join(sorted(done)) + '\n')
    print(len(done), 'recorded')


if __name__ == '__main__':
    main()
