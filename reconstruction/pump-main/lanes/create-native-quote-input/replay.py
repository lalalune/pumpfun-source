#!/usr/bin/env python3
"""Replay the existing create-v2 fixtures on a compiled candidate and original."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def canonical(value):
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    if isinstance(value, bytes):
        return value.hex()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, 'to_json'):
        return json.loads(value.to_json())
    return str(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    harness = ROOT / 'tests/test_create_v2_captured.py'
    spec = importlib.util.spec_from_file_location('create_fixtures', harness)
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    original = fixtures.PUMP_ELF
    paths = {'harness': harness, 'candidate': args.candidate,
             **{str(p.relative_to(ROOT)): p for p in fixtures.ELF_SHA256}}
    hashes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()}
    for path, expected in fixtures.ELF_SHA256.items():
        if hashes[str(path.relative_to(ROOT))] != expected:
            raise SystemExit('captured input hash mismatch: ' + str(path.relative_to(ROOT)))
    rows = []
    try:
        for index, case in enumerate(fixtures.fixed_cases() + fixtures.random_cases()):
            fixtures.PUMP_ELF = original
            expected = canonical(fixtures.run_captured(case))
            fixtures.PUMP_ELF = args.candidate
            actual = canonical(fixtures.run_captured(case))
            rows.append({'index': index, 'case': canonical(case), 'original': expected,
                         'candidate': actual, 'diff': [k for k in expected if expected[k] != actual[k]]})
    finally:
        fixtures.PUMP_ELF = original
    if hashes != {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()}:
        raise SystemExit('input changed during replay')
    bad = [r['index'] for r in rows if r['diff']]
    report = {'input_sha256': hashes, 'count': len(rows), 'mismatches': bad, 'cases': rows,
              'scope': 'Existing signed synthetic create-v2 fixtures; compares errors, watched account '
                       'snapshots, events and returned account objects. Not general runtime identity.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(gzip.compress(json.dumps(report).encode(), mtime=0))
    print(json.dumps({'count': len(rows), 'mismatches': bad}))
    return bool(bad)


if __name__ == '__main__':
    raise SystemExit(main())
