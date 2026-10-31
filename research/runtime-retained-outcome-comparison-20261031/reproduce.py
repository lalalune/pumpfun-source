#!/usr/bin/env python3
"""Generate an ordinary local receipt and exercise its production consumer."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True, help='new evidence directory')
    args = parser.parse_args()
    root, output = args.repo.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    receipt = output / 'administration.json'
    original = root / 'evidence/original/pump/deployed.so'
    command = [sys.executable, '-B', str(root / 'scripts/pump_validate_admin.py'),
               '--candidate', str(original), '--output', str(receipt)]
    run = subprocess.run(command, cwd=root, capture_output=True, text=True, check=True, timeout=60)
    report = json.loads(receipt.read_bytes())
    sys.path.insert(0, str(root / 'scripts'))
    import pump_validate_parallel as validator

    outcomes = []
    for field in ('control', 'error', 'lamports', 'data_hex', 'missing-both', 'diagnostics'):
        changed = copy.deepcopy(report)
        row = changed['cases'][0]
        if field == 'error':
            row['candidate'][field] = 'unexpected failure'
        elif field == 'lamports':
            row['candidate'][field] += 1
        elif field == 'data_hex':
            row['candidate'][field] = 'ff' + row['candidate'][field][2:]
        elif field == 'missing-both':
            for side in ('original', 'candidate'):
                del row[side]['error']
        elif field == 'diagnostics':
            row['candidate']['logs'].append('Program log: incidental diagnostic')
            row['original']['compute_units'] = 1
            row['candidate']['compute_units'] = 2
        try:
            count = validator.validate_result('administration', changed, original, original)
            result = {'accepted': True, 'admitted_cases': count}
        except AssertionError as error:
            result = {'accepted': False, 'reason': str(error)}
        outcomes.append({'change': field, **result})
    sources = ('scripts/pump_validate_admin.py', 'scripts/pump_validate_all.py',
               'scripts/pump_validate_parallel.py', 'evidence/original/pump/deployed.so')
    result = {'scope': 'Local producer and production receipt-consumer functions; no full aggregate build or corpus run.',
              'producer_stdout': run.stdout.strip(), 'producer_cases': report['case_count'],
              'producer_mismatches': report['mismatches'],
              'receipt_sha256': hashlib.sha256(receipt.read_bytes()).hexdigest(),
              'input_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources},
              'outcomes': outcomes}
    (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
