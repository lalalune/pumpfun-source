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

from pump_differential_output import PumpReport
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


def panic(result, *, required=True):
    lines = [line for line in result['relevant_logs'] if line.startswith('Program log: panicked at ')]
    if len(lines) != 1:
        assert not required, lines
        return None
    parts = lines[0].removeprefix('Program log: panicked at ').split('\n', 1)
    if len(parts) != 2:
        assert not required, lines
        return None
    source, message = parts
    return {'source': source, 'message': message}


def report_output(candidate, output, extra_inputs=()):
    return PumpReport(output, ROOT, candidate, __file__,
                      extra_inputs=[*extra_inputs,
                                    Path(fixture.__file__).resolve(),
                                    ROOT / 'evidence/original/pump/deployed.so',
                                    fixture.FIXTURE, fixture.IDL,
                                    ROOT / 'evidence/dependencies/spl_token_2022/deployed.so',
                                    ROOT / 'evidence/dependencies/associated_token/deployed.so'],
                      overwrite=False)


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
             Path(PumpReport.write.__code__.co_filename).resolve(),
             Path(fixture.pin_program.__code__.co_filename).resolve(),
             ROOT/'evidence/original/pump/deployed.so', args.candidate, fixture.FIXTURE, fixture.IDL,
             ROOT/'evidence/dependencies/spl_token_2022/deployed.so',
             ROOT/'evidence/dependencies/associated_token/deployed.so']
    publisher = report_output(args.candidate, args.output, extra_inputs=paths)
    inputs = {str(p.resolve()): sha(p) for p in paths}
    original_binary = fixture.pin_program(ROOT/'evidence/original/pump/deployed.so')
    candidate_binary = fixture.pin_program(args.candidate)
    original_sha256, candidate_sha256 = sha(original_binary), sha(candidate_binary)
    assert original_sha256 == inputs[str((ROOT/'evidence/original/pump/deployed.so').resolve())]
    assert candidate_sha256 == inputs[str(args.candidate.resolve())]
    run, source = full_capture()
    rows = []
    for case, message in (
        ({'name': 'accrual-add-overflow', 'unclaimed': 2**64-1, 'volume': 1}, 'Unexpected overflow'),
        ({'name': 'claimed-add-overflow', 'claimed': 2**64-1, 'volume': 1}, 'called `Option::unwrap()` on a `None` value'),
    ):
        original = run(original_binary, case)
        candidate = run(candidate_binary, case)
        assert original['transaction_base64'] == candidate['transaction_base64']
        Transaction.from_bytes(base64.b64decode(original['transaction_base64'])).verify()
        before, after = panic(original), panic(candidate, required=False)
        assert before['message'] == message
        differences = [k for k in FIELDS if original[k] != candidate[k]]
        if after is None or before['message'] != after['message']:
            differences.append('panic_message')
        rows.append({'case': case, 'original': original, 'candidate': candidate,
                     'original_panic': before, 'candidate_panic': after,
                     'expected_message': message, 'differences': differences})
    assert inputs == {str(p.resolve()): sha(p) for p in paths}
    assert sha(original_binary) == original_sha256 and sha(candidate_binary) == candidate_sha256
    report = {'scope': __doc__, 'original_sha256': original_sha256,
              'candidate_sha256': candidate_sha256, 'inputs_sha256': inputs,
              'capture_source': source, 'case_count': len(rows),
              'mismatches': [row['case']['name'] for row in rows if row['differences']], 'cases': rows}
    raw = (json.dumps(report, indent=2) + '\n').encode('utf-8')
    payload = gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw
    publisher.write(payload)
    print(json.dumps({'cases': len(rows), 'mismatches': report['mismatches']}))
    if report['mismatches']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
