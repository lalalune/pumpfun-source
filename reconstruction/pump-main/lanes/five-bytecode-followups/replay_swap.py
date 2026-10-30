#!/usr/bin/env python3
"""Compare a compiled Pump candidate on the existing 120 single-hop fixtures."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    harness = ROOT / 'tests/test_multi_hop_hop_captured.py'
    spec = importlib.util.spec_from_file_location('captured_hop', harness)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = module.PUMP_ELF
    paths = {'harness': harness, 'original': original, 'candidate': args.candidate}
    hashes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()}
    if hashes['original'] != module.ELF_SHA256[original]:
        raise SystemExit('captured original hash mismatch')
    rows = []
    try:
        for index, case in enumerate(module.fixed_cases() + module.random_cases()):
            module.PUMP_ELF = original
            expected = module.run_captured(case, index)
            module.PUMP_ELF = args.candidate
            actual = module.run_captured(case, index)
            rows.append({'index': index, 'case': case, 'match': expected == actual,
                         'original': expected, 'candidate': actual})
    finally:
        module.PUMP_ELF = original
    if hashes != {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()}:
        raise SystemExit('input changed during replay')
    mismatches = [row['index'] for row in rows if not row['match']]
    report = {'input_sha256': hashes, 'case_count': len(rows), 'mismatches': mismatches,
              'scope': 'Synthetic one-hop fixtures; signature verification disabled for AMM PDA. '
                       'Compares errors, curve bytes, curve quote change, user base change and '
                       'buyback receipt only. No post-complete fill, two-hop or Token-2022 coverage.',
              'cases': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(report, indent=2,
                                default=lambda value: value.hex() if isinstance(value, bytes) else str(value)) + '\n')
    print(json.dumps({'case_count': len(rows), 'mismatches': mismatches}))
    return bool(mismatches)


if __name__ == '__main__':
    raise SystemExit(main())
