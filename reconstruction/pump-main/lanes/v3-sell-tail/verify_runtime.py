"""Verify retained receipts and signatures; this does not execute the programs."""
import base64
import gzip
import hashlib
import json
import re
from pathlib import Path

from solders.transaction import Transaction

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FIELDS = ('error', 'accounts', 'inner_instructions', 'event_payloads', 'return_data')
METER = re.compile(r'Program [1-9A-HJ-NP-Za-km-z]+ consumed \d+ of \d+ compute units')


def logs(receipt):
    return [line for line in receipt['logs'] if not METER.fullmatch(line)]


def verify_rows(report):
    rows = report['rows']
    assert len(rows) == report['case_count'] == 117
    assert report['differences'] == report['regressions'] == []
    successes = 0
    for row in rows:
        receipts = row['receipts']
        assert set(receipts) == {'original', 'control', 'candidate'}
        assert row['different_fields'] == row['regression_fields'] == []
        assert row['ordered_non_meter_logs_equal'] is True
        for receipt in receipts.values():
            tx = Transaction.from_bytes(base64.b64decode(receipt['transaction_base64']))
            signatures = tx.verify_with_results()
            assert signatures and all(signatures)
            assert receipt['signature_verified'] is True
        for name in ('original', 'control'):
            assert all(receipts[name][field] == receipts['candidate'][field] for field in FIELDS)
            assert logs(receipts[name]) == logs(receipts['candidate'])
        successes += receipts['candidate']['error'] is None
    assert successes == 77
    return {'cases': len(rows), 'signed_executions': len(rows) * 3,
            'successes_per_image': successes, 'expected_failures_per_image': len(rows) - successes}


def main():
    manifest = json.loads((HERE / 'runtime-manifest.json').read_text())
    for name, digest in manifest['packet'].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    for name, digest in manifest['external'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    report = json.loads(gzip.decompress((HERE / 'runtime.json.gz').read_bytes()))
    assert report['images'] == manifest['images']
    assert report['fixture_sha256'] == hashlib.sha256(gzip.decompress((HERE / 'fixture.json.gz').read_bytes())).hexdigest()
    for name, digest in report['source_inputs'].items():
        assert manifest['external'][name] == digest
    print(json.dumps(verify_rows(report), sort_keys=True))


if __name__ == '__main__':
    main()
