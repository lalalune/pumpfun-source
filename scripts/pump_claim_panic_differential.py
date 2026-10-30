#!/usr/bin/env python3
"""Signed claim overflow diagnostics with full captured VM logs.

Uses the unchanged historical invocation and fixture. Only the returned log
capture is widened; source locations are recorded separately from panic messages.
No transaction is broadcast. This is a two-case diagnostic regression, not an
exhaustive claim or whole-contract proof.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import base64
import gzip
import hashlib
import inspect
import json
from pathlib import Path

import pump_claim_token_incentives_differential as fixture
from solders.transaction import Transaction

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('error', 'before', 'after', 'event_data_base64', 'inner')


def full_capture():
    source = inspect.getsource(fixture.run_case)
    old = '''[line for line in logs if "Instruction:" in line or
                              "AnchorError" in line or "Program data:" in line or
                              "failed" in line]'''
    assert source.count(old) == 1, 'Historical log filter changed; review capture adapter'
    source = source.replace(old, 'logs')
    namespace = fixture.__dict__.copy()
    exec(compile(source, str(Path(__file__).resolve()) + ':capture', 'exec'), namespace)
    return namespace['run_case'], source


def panic(result):
    lines = [line for line in result['relevant_logs'] if line.startswith('Program log: panicked at ')]
    assert len(lines) == 1, lines
    source, message = lines[0].removeprefix('Program log: panicked at ').split('\n', 1)
    return {'source': source, 'message': message}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # exists() follows links: a dangling symlink would pass it and the write
    # would create a file wherever the link points.
    if args.output.is_symlink() or args.output.exists():
        raise SystemExit('Retain prior diagnostic receipts')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    paths = [Path(__file__).resolve(), Path(fixture.__file__).resolve(),
             ROOT/'evidence/original/pump/deployed.so', args.candidate, fixture.FIXTURE, fixture.IDL,
             ROOT/'evidence/dependencies/spl_token_2022/deployed.so',
             ROOT/'evidence/dependencies/associated_token/deployed.so']
    inputs = {str(p.resolve()): sha(p) for p in paths}
    run, source = full_capture()
    rows = []
    for case, message in (
        ({'name': 'accrual-add-overflow', 'unclaimed': 2**64-1, 'volume': 1}, 'Unexpected overflow'),
        ({'name': 'claimed-add-overflow', 'claimed': 2**64-1, 'volume': 1}, 'called `Option::unwrap()` on a `None` value'),
    ):
        original = run(ROOT/'evidence/original/pump/deployed.so', case)
        candidate = run(args.candidate, case)
        assert original['transaction_base64'] == candidate['transaction_base64']
        Transaction.from_bytes(base64.b64decode(original['transaction_base64'])).verify()
        before, after = panic(original), panic(candidate)
        assert before['message'] == message
        differences = [k for k in FIELDS if original[k] != candidate[k]]
        if before['message'] != after['message']:
            differences.append('panic_message')
        rows.append({'case': case, 'original': original, 'candidate': candidate,
                     'original_panic': before, 'candidate_panic': after,
                     'expected_message': message, 'differences': differences})
    assert inputs == {str(p.resolve()): sha(p) for p in paths}
    report = {'scope': __doc__, 'original_sha256': sha(ROOT/'evidence/original/pump/deployed.so'),
              'candidate_sha256': sha(args.candidate), 'inputs_sha256': inputs,
              'capture_source': source, 'case_count': len(rows),
              'mismatches': [row['case']['name'] for row in rows if row['differences']], 'cases': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(report, separators=(',', ':')).encode()
    payload = gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw
    # 'xb' keeps the receipt fresh if another writer creates the path after the
    # preflight check, and refuses a symlink that appeared in between.
    with args.output.open('xb') as stream:
        stream.write(payload)
    print(json.dumps({'cases': len(rows), 'mismatches': report['mismatches']}))
    if report['mismatches']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
