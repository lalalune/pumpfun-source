#!/usr/bin/env python3
"""Independent re-check of this packet: replay every receipt on both images.

usage (inside the packet folder): python3 verify.py --images '{"original": p, "candidate": p}'
Uses MANIFEST.json, runtime/receipts.jsonl.gz, runtime/report.json.gz and the two images.
Exit 0 = every packet file matches MANIFEST.json and every recorded step and final account
state reproduces on its own image, with image sha256 values equal to the report and a
consistent report summary.
"""
import argparse, gzip, hashlib, json, pathlib, struct, sys
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

HERE = pathlib.Path(__file__).resolve().parent
COMPARED = ['error', 'custom_error', 'error_number', 'return_hex', 'events', 'program_logs', 'state']
ZERO = Pubkey.default()
TOKEN_PROGRAMS = ('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA', 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
VAULT_DISC = hashlib.sha256(b'account:BuybackVault').digest()[:8]


def decode_vault(d):
    # same raw decode as producer.py (recorded in receipts as state.decoded)
    if len(d) < 88 or d[:8] != VAULT_DISC:
        return None
    tc, t1, t2, last, rate = struct.unpack_from('<QQQqq', d, 40)
    return {'authority': str(Pubkey.from_bytes(d[8:40])), 'total_claimed': tc, 'total_claimed_token1': t1, 'total_claimed_token2': t2,
            'last_claimed': last, 'claim_rate_limit': rate, 'nonzero_reserved': sum(1 for b in d[88:] if b)}


def snap(a):
    if a is None:
        return None
    d = bytes(a.data)
    s = {'lamports': a.lamports, 'owner': str(a.owner), 'len': len(d), 'sha256': hashlib.sha256(d).hexdigest()}
    if str(a.owner) in TOKEN_PROGRAMS and len(d) >= 165:
        s['token_amount'] = int.from_bytes(d[64:72], 'little')
        s['token_owner'] = str(Pubkey.from_bytes(d[32:64]))
        if len(d) > 165 and d[165] == 2:
            # Token-2022 account TLV: report the TransferFeeAmount.withheld_amount extension if present
            o = 166
            while o + 4 <= len(d):
                t, n = struct.unpack_from('<HH', d, o)
                if t == 2 and n == 8:
                    s['withheld'] = int.from_bytes(d[o + 4:o + 12], 'little')
                o += 4 + n
    if d[:8] == VAULT_DISC:
        s['decoded'] = decode_vault(d)
    return s


def replay(binary, program, keys, case, watched):
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(program, binary)
    for k in keys.values():
        vm.set_account(k.pubkey(), Account(10**12, b'', ZERO))
    vm.set_clock(Clock(1000, 0, 0, 0, case['clock_unix']))
    for a in case['initial']:
        vm.set_account(Pubkey.from_string(a['pubkey']), Account(a['lamports'], bytes.fromhex(a['data_hex']), Pubkey.from_string(a['owner'])))
    steps = []
    for st in case['steps']:
        if 'clock_unix' in st:
            vm.set_clock(Clock(1000, 0, 0, 0, st['clock_unix']))
        vm.expire_blockhash()
        ixs = [Instruction(Pubkey.from_string(i.get('program_id', str(program))), bytes.fromhex(i['data_hex']), [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in i['accounts']]) for i in st['instructions']]
        signers = [keys['PAYER']] + [keys[s] for s in st['signers'] if s != 'PAYER']
        r = vm.send_transaction(Transaction.new_signed_with_payer(ixs, keys['PAYER'].pubkey(), signers, vm.latest_blockhash()))
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        rd = meta.return_data()
        cu = meta.compute_units_consumed
        steps.append({'error': str(r.err()) if failed else None,
                      'custom_error': next((l.split('Error Code: ')[1].split('.')[0] for l in logs if 'Error Code: ' in l), None),
                      'error_number': next((int(l.split('Error Number: ')[1].split('.')[0]) for l in logs if 'Error Number: ' in l), None),
                      'return_hex': bytes(rd.data).hex() if rd is not None and len(rd.data) else None,
                      'events': [l for l in logs if l.startswith('Program data:')],
                      'program_logs': [l for l in logs if l.startswith('Program log:')],
                      'state': {k: snap(vm.get_account(Pubkey.from_string(k))) for k in watched},
                      'compute_units': cu() if callable(cu) else cu})
    final = {}
    for k in watched:
        a = vm.get_account(Pubkey.from_string(k))
        final[k] = None if a is None else {'lamports': a.lamports, 'owner': str(a.owner), 'data_hex': bytes(a.data).hex()}
    return steps, final


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--images', required=True)
    a = p.parse_args()
    manifest = json.loads((HERE / 'MANIFEST.json').read_text())
    listed = {entry['path']: entry for entry in manifest['files']}
    if len(listed) != len(manifest['files']):
        raise SystemExit('duplicate packet manifest path')
    entries = list(HERE.rglob('*'))
    if any(path.is_symlink() or path.suffix in ('.pyc', '.pyo') for path in entries):
        raise SystemExit('packet contains a symlink or cached Python bytecode')
    actual = {path.relative_to(HERE).as_posix(): path for path in entries
              if path.is_file() and path != HERE / 'MANIFEST.json'
              and path.name != '.DS_Store' and '.git' not in path.relative_to(HERE).parts}
    if set(listed) != set(actual):
        print('FAIL: packet file set differs from MANIFEST.json: '
              f'missing={sorted(set(actual) - set(listed))} extra={sorted(set(listed) - set(actual))}')
        sys.exit(1)
    for rel, entry in listed.items():
        data = actual[rel].read_bytes()
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            print(f'FAIL: packet member differs from MANIFEST.json: {rel}'); sys.exit(1)
    arg = a.images.strip()
    images = json.loads(arg if arg.startswith('{') else pathlib.Path(arg).read_text())
    report = json.loads(gzip.decompress((HERE / 'runtime/report.json.gz').read_bytes()))
    if report['compared_fields'] != COMPARED:
        print(f'FAIL: compared fields {report["compared_fields"]} != {COMPARED}'); sys.exit(1)
    receipts = [json.loads(l) for l in gzip.decompress((HERE / 'runtime/receipts.jsonl.gz').read_bytes()).splitlines()]
    problems = []
    for name in ['original', 'candidate']:
        sha = hashlib.sha256(pathlib.Path(images[name]).read_bytes()).hexdigest()
        if sha != report['image_sha256'][name]:
            problems.append(f'{name} image sha256 {sha} != report {report["image_sha256"][name]}')
    if problems:
        print('\n'.join(problems)); sys.exit(1)
    program = Pubkey.from_string(report['program_id'])
    keys = {k: Keypair.from_seed(bytes([v]) * 32) for k, v in report['signer_seeds'].items()}
    compared = report['compared_fields']
    addr = report['addresses']
    if str(Pubkey.find_program_address([b'buyback-vault', bytes([0])], program)[0]) != addr['buyback_vault_0']:
        problems.append('buyback vault 0 address differs')
    if str(Pubkey.find_program_address([b'referral-vault', bytes(keys['USER'].pubkey())], program)[0]) != addr['referral_vault_USER']:
        problems.append('referral vault address differs')
    if len(receipts) != report['case_count'] or [r['case']['name'] for r in receipts] != [c['name'] for c in report['cases']]:
        problems.append('receipt/report case list differs')
    steps_total = 0
    for r, summary in zip(receipts, report['cases']):
        case = r['case']
        watched = list(r['final_state']['original'].keys())
        replays = {}
        for name in ['original', 'candidate']:
            got_steps, got_final = replay(images[name], program, keys, case, watched)
            replays[name] = got_steps
            for i, (got, rec) in enumerate(zip(got_steps, r['steps'])):
                if got != rec[name]:
                    problems.append(f'{case["name"]} step {i} ({rec["label"]}) {name}: replay differs from receipt')
            if len(got_steps) != len(r['steps']):
                problems.append(f'{case["name"]} {name}: step count differs')
            if got_final != r['final_state'][name]:
                problems.append(f'{case["name"]} {name}: final state differs from receipt')
        step_match = [all(o[f] == k[f] for f in compared) for o, k in zip(replays['original'], replays['candidate'])]
        final_match = r['final_state']['original'] == r['final_state']['candidate']
        if [s['match'] for s in r['steps']] != step_match or r['final_match'] != final_match:
            problems.append(f'{case["name"]}: recorded match flags differ from recomputed')
        if summary['match'] != (final_match and all(step_match)) or summary['steps'] != len(r['steps']) or summary['labels'] != [s['label'] for s in r['steps']]:
            problems.append(f'{case["name"]}: report summary differs')
        oc = lambda s: 'ok' if s['error'] is None else (s['custom_error'] or s['error'])
        if summary['outcomes'] != [oc(s) for s in replays['original']] or summary['outcomes_candidate'] != [oc(s) for s in replays['candidate']]:
            problems.append(f'{case["name"]}: report outcomes differ')
        if summary['cu_original'] != [s['compute_units'] for s in replays['original']] or summary['cu_candidate'] != [s['compute_units'] for s in replays['candidate']]:
            problems.append(f'{case["name"]}: report compute units differ')
        steps_total += len(r['steps'])
    if steps_total != report['step_count']:
        problems.append('step_count differs')
    if report['mismatched_cases'] != [c['name'] for c in report['cases'] if not c['match']]:
        problems.append('mismatched_cases differs')
    if problems:
        print('\n'.join(problems[:50])); print(f'FAIL {len(problems)} problems'); sys.exit(1)
    print(json.dumps({'verified_cases': len(receipts), 'verified_steps': steps_total, 'mismatched_cases': report['mismatched_cases']}))
    sys.exit(0)


if __name__ == '__main__':
    main()
