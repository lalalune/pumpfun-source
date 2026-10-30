#!/usr/bin/env python3
"""Independent re-check of this packet: replay every receipt on both images.

usage (inside the packet folder): python3 verify.py --images '{"original": p, "candidate": p}'
Uses only runtime/receipts.jsonl.gz, runtime/report.json.gz and the two images.
Exit 0 = every recorded step and final account state reproduces on its own image,
image sha256 values equal the report, and the report summary is consistent.
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
CONFIG_PROGRAM = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
ZERO = Pubkey.default()
CONFIG_DISC = hashlib.sha256(b'account:FeeConfig').digest()[:8]


def decode_config(d):
    # same raw full-layout decode as producer.py (recorded in receipts as state.decoded)
    if len(d) < 69 or d[:8] != CONFIG_DISC:
        return None
    out = {'admin': str(Pubkey.from_bytes(d[9:41])), 'flat': list(struct.unpack_from('<QQQ', d, 41))}
    o = 65
    for name in ['normal', 'stable']:
        if o + 4 > len(d):
            out[name] = None
            return out
        n = struct.unpack_from('<I', d, o)[0]
        if o + 4 + n * 40 > len(d):
            out[name] = {'count': n, 'fits': False}
            return out
        out[name] = {'count': n, 'tiers': [[int.from_bytes(d[o + 4 + i * 40:o + 20 + i * 40], 'little')] + list(struct.unpack_from('<QQQ', d, o + 20 + i * 40)) for i in range(n)]}
        o += 4 + n * 40
    out['exotic'] = list(struct.unpack_from('<QQQ', d, o)) if o + 24 <= len(d) else None
    out['end'] = o + 24
    out['nonzero_after_end'] = sum(1 for b in d[o + 24:] if b)
    return out


def replay(binary, program, keys, case, watched):
    config_key = str(Pubkey.find_program_address([b'fee_config', bytes(CONFIG_PROGRAM)], program)[0])
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(program, binary)
    for k in keys.values():
        vm.set_account(k.pubkey(), Account(10**12, b'', ZERO))
    vm.set_account(CONFIG_PROGRAM, Account(10**9, b'', ZERO))
    if 'clock_unix' in case:
        vm.set_clock(Clock(1000, 0, 0, 0, case['clock_unix']))
    for a in case['initial']:
        vm.set_account(Pubkey.from_string(a['pubkey']), Account(a['lamports'], bytes.fromhex(a['data_hex']), Pubkey.from_string(a['owner'])))
    steps = []
    for st in case['steps']:
        if 'clock_unix' in st:
            vm.set_clock(Clock(1000, 0, 0, 0, st['clock_unix']))
        ixs = [Instruction(program, bytes.fromhex(i['data_hex']), [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in i['accounts']]) for i in st['instructions']]
        signers = [keys['PAYER']] + [keys[s] for s in st['signers'] if s != 'PAYER']
        r = vm.send_transaction(Transaction.new_signed_with_payer(ixs, keys['PAYER'].pubkey(), signers, vm.latest_blockhash()))
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        rd = meta.return_data()
        state = {}
        for k in watched:
            a = vm.get_account(Pubkey.from_string(k))
            state[k] = None if a is None else {'lamports': a.lamports, 'owner': str(a.owner), 'len': len(a.data), 'sha256': hashlib.sha256(bytes(a.data)).hexdigest()}
            if a is not None and k == config_key:
                state[k]['decoded'] = decode_config(bytes(a.data))
        cu = meta.compute_units_consumed
        steps.append({'error': str(r.err()) if failed else None,
                      'custom_error': next((l.split('Error Code: ')[1].split('.')[0] for l in logs if 'Error Code: ' in l), None),
                      'error_number': next((int(l.split('Error Number: ')[1].split('.')[0]) for l in logs if 'Error Number: ' in l), None),
                      'return_hex': bytes(rd.data).hex() if rd is not None and len(rd.data) else None,
                      'events': [l for l in logs if l.startswith('Program data:')],
                      'program_logs': [l for l in logs if l.startswith('Program log:')],
                      'state': state,
                      'compute_units': cu() if callable(cu) else cu})
    final = {}
    for k in watched:
        a = vm.get_account(Pubkey.from_string(k))
        final[k] = None if a is None else bytes(a.data).hex()
    return steps, final


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--images', required=True)
    a = p.parse_args()
    arg = a.images.strip()
    images = json.loads(arg if arg.startswith('{') else pathlib.Path(arg).read_text())
    report = json.loads(gzip.decompress((HERE / 'runtime/report.json.gz').read_bytes()))
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
    if len(receipts) != report['case_count'] or [r['case']['name'] for r in receipts] != [c['name'] for c in report['cases']]:
        problems.append('receipt/report case list differs')
    steps_total = 0
    for r, summary in zip(receipts, report['cases']):
        case = r['case']
        watched = sorted(r['final_state']['original'].keys())
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
        if summary['match'] != (final_match and all(step_match)) or summary['steps'] != len(r['steps']):
            problems.append(f'{case["name"]}: report summary differs')
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
