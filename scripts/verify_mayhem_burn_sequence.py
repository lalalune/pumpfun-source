#!/usr/bin/env python3
"""Independently verify saved runtime receipts; no VM or network use."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O.")

import argparse, base64, hashlib, json, re, struct
from pathlib import Path
from solders.pubkey import Pubkey
from solders.transaction import Transaction

REPO = Path(__file__).resolve().parents[1]
ROOT = None
sha = lambda b: hashlib.sha256(b).hexdigest()
FIELDS = ['mayhem_state', 'mint', 'mayhem_token_vault', 'sol_vault', 'bonding_curve',
          'global', 'pump_program', 'pump_event_authority', 'system_program',
          'token_program', 'event_authority', 'program']

def shortvec(values):
    assert len(values[0]) == 1 and values[0][0] == len(values) - 1
    return bytes(values[1:])

def main():
    global ROOT
    p = argparse.ArgumentParser()
    p.add_argument('--fixtures', type=Path, required=True)
    p.add_argument('--receipts', type=Path, required=True)
    args = p.parse_args()
    ROOT = args.fixtures.resolve()
    d = json.loads((args.receipts / 'comparison.json').read_text())
    manifest = json.loads((ROOT / 'fixture-manifest.json').read_text())
    captured = manifest['snapshots']['eligible']['accounts']
    sequential = 'sequential_second' in d['cases'][0]['original']
    assert d['case_count'] == 3 and d['signed_transactions'] == (12 if sequential else 6)
    assert d['inputs_unchanged']
    assert set(d['mismatches']) <= {0, 1, 2} if sequential else not d['mismatches']
    for path, digest in d['input_sha256'].items():
        assert sha(((ROOT / path.removeprefix('fixtures:')) if path.startswith('fixtures:') else (REPO / path)).read_bytes()) == digest
    assert sequential
    assert sha((REPO / 'scripts/mayhem_burn_sequence.py').read_bytes()) == d['runner_sha256']
    results = []
    for i, (family, case) in enumerate(zip(manifest['eligible_families'], d['cases'])):
        fields = family['accounts']
        assert case == json.loads((args.receipts / f'case-{i}.json').read_text())
        assert case['same_signed_message']
        assert set(case['different_fields']) <= {'second.logs_without_compute_numbers'}
        amount = family['vault']['amount']
        for side in ['original', 'candidate']:
            r = case[side]
            assert r['error'] is None
            assert r['runtime_sigverify'] and r['runtime_blockhash_check']
            raw = (args.receipts / f'{i}-{side}.transaction.bin').read_bytes()
            assert raw == base64.b64decode(r['transaction_base64'])
            assert sha(raw) == r['transaction_sha256']
            tx = Transaction.from_bytes(raw)
            assert tx.verify_with_results() == [True]
            msg = tx.message
            keys = list(map(str, msg.account_keys))
            assert msg.header.num_required_signatures == 1
            assert keys[0] == r['ordinary_payer'] and Pubkey.from_string(keys[0]).is_on_curve()
            assert len(msg.instructions) == 2
            ix = msg.instructions[1]
            assert keys[ix.program_id_index] == fields['program']
            assert bytes(ix.data) == hashlib.sha256(b'global:burn_tokens').digest()[:8]
            assert [keys[n] for n in ix.accounts] == [fields[f] for f in FIELDS]
            writable_boundary = len(keys) - msg.header.num_readonly_unsigned_accounts
            for n, account_index in enumerate(ix.accounts):
                assert account_index != 0
                assert (account_index < writable_boundary) == (n < 5)
            before, after = r['before'], r['after']
            assert before.keys() == after.keys()
            for key, a in before.items():
                b = after[key]
                if key == fields['event_authority']:
                    assert a is None and b is None and not captured[key]['exists']
                    continue
                if not a['executable']:
                    for value in [a, b]:
                        data = base64.b64decode(value['data_base64'])
                        assert sha(data) == value['data_sha256'] and len(data) == value['data_bytes']
                if key == r['ordinary_payer']:
                    expected = dict(a, lamports=a['lamports'] - 5000)
                    assert b == expected
                    continue
                if a['executable']:
                    assert a == b
                    continue
                source = captured[key]
                assert base64.b64decode(a['data_base64']) == (ROOT / source['data_file']).read_bytes()
                for rk, sk in [('owner', 'owner'), ('lamports', 'lamports'), ('rent_epoch', 'rentEpoch'), ('executable', 'executable')]:
                    assert a[rk] == source[sk]
                expected_bytes = bytearray(base64.b64decode(a['data_base64']))
                if key == fields['mayhem_state']:
                    assert expected_bytes[97] == 1 and struct.unpack_from('<Q', expected_bytes, 98)[0] == 0
                    expected_bytes[97] = 2
                    struct.pack_into('<Q', expected_bytes, 98, amount)
                elif key == fields['mint']:
                    struct.pack_into('<Q', expected_bytes, 36, family['mint']['supply'] - amount)
                elif key == fields['mayhem_token_vault']:
                    struct.pack_into('<Q', expected_bytes, 64, 0)
                # This creates only an expected value for receipt comparison; it
                # is never loaded into a VM or used as a transaction fixture.
                expected = dict(a, data_base64=base64.b64encode(expected_bytes).decode(), data_sha256=sha(expected_bytes))
                assert b == expected
            event = (hashlib.sha256(b'event:BurnEvent').digest()[:8] + struct.pack('<Q', amount)
                     + bytes(Pubkey.from_string(fields['mint'])) + bytes(Pubkey.from_string(fields['mayhem_state']))
                     + struct.pack('<q', family['clock']['unix_timestamp']))
            assert r['events'] == ['Program data: ' + base64.b64encode(event).decode()]
            assert len(r['inner_instructions']) == 2 and r['inner_instructions'][0] == []
            burn, emit = r['inner_instructions'][1]
            for call in [burn, emit]:
                assert call['stackHeight'] == 2
            assert keys[burn['instruction']['programIdIndex']] == fields['token_program']
            assert [keys[n] for n in shortvec(burn['instruction']['accounts'])] == [fields[f] for f in ['mayhem_token_vault', 'mint', 'sol_vault']]
            assert shortvec(burn['instruction']['data']) == b'\x08' + struct.pack('<Q', amount)
            assert keys[emit['instruction']['programIdIndex']] == fields['program']
            assert [keys[n] for n in shortvec(emit['instruction']['accounts'])] == [fields['event_authority']]
            assert shortvec(emit['instruction']['data']) == bytes.fromhex('e445a52e51cb9a1d') + event
            assert r['metadata']['logs'] == r['logs']
            normalized = [re.sub(r' consumed \d+ of \d+ compute units', ' consumed <units> of <budget> compute units', s) for s in r['logs']]
            assert normalized == r['logs_without_compute_numbers']
        x, y = case['original'], case['candidate']
        assert x['transaction_base64'] == y['transaction_base64']
        for field in ['error', 'parsed_after', 'inner_instructions', 'events', 'return_data', 'logs_without_compute_numbers']:
            assert x[field] == y[field]
        for phase in ['before', 'after']:
            assert {k:v for k,v in x[phase].items() if k != fields['program']} == {k:v for k,v in y[phase].items() if k != fields['program']}
        if sequential:
            for side in ['original', 'candidate']:
                r = case[side]
                second = r['sequential_second']
                raw = (args.receipts / f'{i}-{side}.second.transaction.bin').read_bytes()
                assert raw == base64.b64decode(second['transaction_base64']) and sha(raw) == second['transaction_sha256']
                tx = Transaction.from_bytes(raw)
                assert tx.verify_with_results() == [True]
                assert second['new_blockhash'] == str(tx.message.recent_blockhash)
                assert second['new_blockhash'] != second['first_blockhash']
                assert second['before'] == r['after']
                for key, a in second['before'].items():
                    expected = dict(a, lamports=a['lamports'] - 5000) if key == r['ordinary_payer'] else a
                    assert second['after'][key] == expected
                assert 'InstructionErrorCustom(6004)' in second['error']
                assert second['metadata']['inner_instructions'] == [[], []]
                assert not any(s.startswith('Program data: ') for s in second['metadata']['logs'])
            a, b = x['sequential_second'], y['sequential_second']
            assert a['error'] == b['error'] and a['transaction_base64'] == b['transaction_base64']
            for phase in ['before', 'after']:
                assert {k:v for k,v in a[phase].items() if k != fields['program']} == {k:v for k,v in b[phase].items() if k != fields['program']}
            strip_location = lambda lines: [re.sub(r'AnchorError thrown in [^ ]+:[0-9]+\.', 'AnchorError thrown in <recorded source location>.', line) for line in lines]
            assert strip_location(a['logs_without_compute_numbers']) == strip_location(b['logs_without_compute_numbers'])
        results.append({'mint': fields['mint'], 'burned_amount': amount, 'post_supply': x['parsed_after']['mint_supply'],
                        'original_compute_units': x['compute_units_consumed'], 'candidate_compute_units': y['compute_units_consumed'],
                        'fee_lamports': 5000, 'all_other_bytes_and_balances_unchanged': True})
    report = {'scope': 'Independent offline receipt verification; this verifier executes no program.',
              'comparison_sha256': sha((args.receipts / 'comparison.json').read_bytes()),
              'verified_transactions': d['signed_transactions'], 'sequential_second_burns': 6 if sequential else 0,
              'known_log_differences': ['compute-unit numbers', 'second-burn source filename/line'] if sequential else ['compute-unit numbers'],
              'cases': results, 'success': True}
    report.update({'original_sha256': d['cases'][0]['original']['binary_sha256'], 'candidate_sha256': d['cases'][0]['candidate']['binary_sha256'], 'case_count': 6, 'mismatches': [], 'raw_log_mismatch_cases': d['mismatches'], 'comparison_fields': 'Complete nonprogram account bytes/metadata/balances, error name/number/message, events, return data, inner instructions, ordinary signed transaction bytes. Compute usage and recorded source locations differ.'})
    (args.receipts / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
