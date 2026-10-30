#!/usr/bin/env python3
"""Signed offline Pump incentive-claim boundary comparisons.

Uses the historical captured user/mint fixture plus explicit synthetic schedule
and vault state. The suite is finite; successful comparison is not a whole-
contract proof. It never broadcasts a transaction.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import base64
import gzip
import hashlib
import json
import random
from pathlib import Path

import pump_claim_token_incentives_differential as fixture
from build_source_manifest import source_manifest

FIELDS = ('error', 'before', 'after', 'event_data_base64', 'inner')


def run_case(binary, case):
    if not (case.get('stored_user_zero') or case.get('missing_user_ata') or case.get('ata_mutation')):
        return fixture.run_case(binary, case)
    # Reuse the verified captured fixture loader, then apply this explicitly
    # recorded account mutation before either VM is initialized.
    loader = fixture.fixture_data
    def altered_fixture():
        source, keys, prior, volume, vault = loader()
        if case.get('stored_user_zero'):
            data = bytearray(base64.b64decode(prior['volume']['data_base64']))
            data[8:40] = bytes(32)
            prior['volume']['data_base64'] = base64.b64encode(data).decode()
            prior['volume']['data_sha256'] = hashlib.sha256(data).hexdigest()
        if case.get('missing_user_ata'):
            prior['user_base'].update(lamports=0, data_base64='',
                                      owner=str(fixture.Pubkey.default()))
        if case.get('ata_mutation'):
            mutation = case['ata_mutation']
            account = prior['user_base']
            data = bytearray(base64.b64decode(account['data_base64']))
            for offset, value in mutation.get('patches', []):
                data[offset:offset + len(bytes.fromhex(value))] = bytes.fromhex(value)
            if 'length' in mutation:
                data = data[:mutation['length']]
            account.update(data_base64=base64.b64encode(data).decode(),
                           data_sha256=hashlib.sha256(data).hexdigest())
            for field in ('lamports', 'owner'):
                if field in mutation:
                    account[field] = mutation[field]
        return source, keys, prior, volume, vault
    fixture.fixture_data = altered_fixture
    try:
        return fixture.run_case(binary, case)
    finally:
        fixture.fixture_data = loader


def cases(seed=20261027):
    yield from fixture.CASES
    for field in ('now', 'start', 'end', 'seconds_in_a_day', 'last'):
        for value in (-(2**63), -1, 0, 1, 29, 30, 31, 2**63 - 1):
            yield {'name': f'boundary-{field}-{value}', field: value}
    for field in ('volume', 'supply', 'day_volume', 'claimed', 'unclaimed'):
        for value in (0, 1, 2**32, 2**63, 2**64 - 1):
            yield {'name': f'boundary-{field}-{value}', field: value}
    yield {'name': 'quotient-overflow', 'volume': 2**64 - 1, 'supply': 2**64 - 1, 'day_volume': 1}
    yield {'name': 'accrual-add-overflow', 'unclaimed': 2**64 - 1, 'volume': 1}
    yield {'name': 'claimed-add-overflow', 'claimed': 2**64 - 1, 'volume': 1}
    yield {'name': 'stored-user-zero', 'stored_user_zero': True}
    yield {'name': 'stored-user-before-start', 'stored_user_zero': True, 'now': 1, 'start': 10}
    yield {'name': 'missing-user-ata', 'missing_user_ata': True}
    yield {'name': 'missing-user-ata-zero-payout', 'missing_user_ata': True, 'volume': 0}
    for name, mutation in (
        ('wrong-authority', {'patches': [(32, bytes(32).hex())]}),
        ('wrong-mint', {'patches': [(0, bytes(32).hex())]}),
        ('frozen', {'patches': [(108, '02')]}),
        ('uninitialized', {'patches': [(108, '00')]}),
        ('empty', {'length': 0}),
        ('short', {'length': 164}),
        ('system-owner', {'owner': str(fixture.Pubkey.default())}),
        ('zero-lamports', {'lamports': 0}),
    ):
        yield {'name': 'ata-' + name, 'ata_mutation': mutation}
    yield {'name': 'missing-user-ata-prefunded', 'missing_user_ata': True,
           'ata_mutation': {'lamports': 1}}
    yield {'name': 'missing-user-ata-wrong-stored-user', 'missing_user_ata': True,
           'stored_user_zero': True}
    rng = random.Random(seed)
    for index in range(192):
        start = rng.choice([-10, -1, 0, 1, 10])
        yield {'name': f'schedule-{index}', 'start': start,
               'end': start + rng.choice([-1, 0, 1, 29, 30, 59, 100]),
               'now': rng.choice([-1, 0, 1, 9, 10, 29, 30, 31, 50, 100]),
               'seconds_in_a_day': rng.choice([-1, 0, 1, 2, 10]),
               'last': rng.choice([-1, 0, 1, 10, 29, 30, 31]),
               'needs_claim': rng.choice([0, 1]),
               'unclaimed': rng.choice([0, 1, 100]),
               'volume': rng.choice([0, 1, 20, 2**32]),
               'supply': rng.choice([0, 1, 1000]),
               'day_volume': rng.choice([0, 1, 100])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--build-comparison', type=Path)
    parser.add_argument('--seed', type=int, default=20261027)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    candidate_sha = sha(args.candidate)
    original_sha = sha(fixture.ORIGINAL)
    inputs = {str(p.relative_to(fixture.ROOT)): sha(p) for p in
              (Path(__file__).resolve(), Path(fixture.__file__).resolve(),
               fixture.ROOT / 'scripts/build_source_manifest.py')}
    build = json.loads(args.build_comparison.read_text()) if args.build_comparison else None
    if build:
        assert build['comparison']['candidate_sha256'] == candidate_sha
        assert build['source_sha256'] == source_manifest(
            fixture.ROOT / 'programs/pump', fixture.ROOT / 'programs/pump', fixture.ROOT)
    rows = []
    for case in cases(args.seed):
        original = run_case(fixture.ORIGINAL, case)
        candidate = run_case(args.candidate, case)
        assert original['transaction_base64'] == candidate['transaction_base64']
        differences = [field for field in FIELDS if original[field] != candidate[field]]
        rows.append({'case': case, 'original': original, 'candidate': candidate, 'differences': differences})
    assert candidate_sha == sha(args.candidate) and original_sha == sha(fixture.ORIGINAL)
    assert all(sha(fixture.ROOT / path) == digest for path, digest in inputs.items())
    if build:
        assert build['source_sha256'] == source_manifest(
            fixture.ROOT / 'programs/pump', fixture.ROOT / 'programs/pump', fixture.ROOT)
    report = {'scope': __doc__, 'candidate_sha256': candidate_sha, 'original_sha256': original_sha,
              'harness_sha256': sha(Path(__file__)), 'fixture_harness_sha256': sha(Path(fixture.__file__)),
              'fixture_sha256': sha(fixture.FIXTURE), 'case_count': len(rows),
              'inputs_sha256': inputs, 'seed': args.seed,
              'build_comparison_sha256': sha(args.build_comparison) if build else None,
              'compiled_source_sha256': build['source_sha256'] if build else None,
              'mismatches': [row['case']['name'] for row in rows if row['differences']], 'cases': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    assert not args.output.exists(), 'Retain earlier results'
    args.output.write_bytes(gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0))
    print(json.dumps({key: report[key] for key in ('case_count', 'mismatches')}))
    if report['mismatches']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
