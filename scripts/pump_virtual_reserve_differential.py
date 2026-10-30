#!/usr/bin/env python3
"""Main Pump reserve-sync comparison using an unchanged local signer fixture.

The synthetic caller supplies the required PDA signature in a local VM. This
is not evidence of a production caller or live reachability. No other program
is reconstructed or changed, and no transaction is broadcast.
"""
import argparse
import base64
import gzip
import hashlib
import json
import struct
from pathlib import Path

import pump_set_mayhem_virtual_params_differential as f
from build_source_manifest import source_manifest

FIELDS = ('error', 'before', 'after', 'events', 'inner', 'return_data')
U64 = 2**64 - 1


def run(binary, case):
    vm = f.LiteSVM().with_transaction_history(0).with_sigverify(True)
    vm.add_program_from_file(f.PUMP, str(binary))
    vm.add_program_from_file(f.MAYHEM, str(f.STUB))
    for key, name in ((f.TOKEN22, 'spl_token_2022'), (f.ATA, 'associated_token')):
        vm.add_program_from_file(key, str(f.ROOT / f'evidence/dependencies/{name}/deployed.so'))
    vm.airdrop(f.PAYER.pubkey(), 10**10)
    global_data = bytearray(base64.b64decode(f.CAPTURE['data_base64']))
    struct.pack_into('<Q', global_data, f.IRTR_OFF, case['irtr'])
    roles = {'authority': f.SOL_VAULT[0], 'vault': f.MTV, 'mint': f.MINT,
             'global': f.GLOBAL, 'curve': f.CURVE, 'token_program': f.TOKEN22,
             'event_authority': f.EVENT_AUTH, 'program': f.PUMP}
    accounts = {
        'global': f.Account(10**9, bytes(global_data), f.PUMP),
        'mint': f.Account(10**9, f.mint_acct(), f.TOKEN22),
        'vault': f.Account(10**9, f.tok(f.MINT, f.SOL_VAULT[0], case['vault']), f.TOKEN22),
        'authority': f.Account(10**9, b'', f.MAYHEM),
        'curve': f.Account(10**9, f.bc_data(case['vtr'], case['vqr'], case['rtr'],
                          case['rqr'], case['tts'], f.QM_SPL if case['spl'] else f.Pubkey.default(), case['mayhem']), f.PUMP),
    }
    for role, account in accounts.items():
        vm.set_account(roles[role], account)
    for role, changes in case.get('mutations', {}).items():
        key = roles[role]
        old = vm.get_account(key)
        data = bytearray(old.data)
        for offset, encoded in changes.get('patches', []):
            patch = bytes.fromhex(encoded); data[offset:offset+len(patch)] = patch
        if 'length' in changes:
            data = data[:changes['length']]
        vm.set_account(key, f.Account(changes.get('lamports', old.lamports), bytes(data),
                       f.Pubkey.from_string(changes.get('owner', str(old.owner))), old.executable))
    metas = [f.AccountMeta(f.PUMP, False, False),
             f.AccountMeta(roles['authority'], False, case.get('readonly') != 'authority'),
             f.AccountMeta(roles['vault'], False, case.get('readonly') != 'vault'),
             f.AccountMeta(roles['mint'], False, False), f.AccountMeta(roles['global'], False, False),
             f.AccountMeta(roles['curve'], False, case.get('readonly') != 'curve'),
             f.AccountMeta(f.TOKEN22, False, False), f.AccountMeta(f.EVENT_AUTH, False, False),
             f.AccountMeta(f.PUMP, False, False)]
    if case.get('direct'):
        ix = f.Instruction(f.PUMP, f.SMVP_DISC, metas[1:])
    else:
        payload = struct.pack('<H', len(f.SMVP_DISC)) + f.SMVP_DISC + bytes([2,9]) + b'sol-vault' + bytes([1,f.SOL_VAULT[1]])
        ix = f.Instruction(f.MAYHEM, payload, metas)
    tx = f.Transaction.new_signed_with_payer([ix], f.PAYER.pubkey(), [f.PAYER], vm.latest_blockhash())
    assert all(tx.verify_with_results())
    def snapshot():
        out = {}
        for name, key in {**roles, 'payer': f.PAYER.pubkey()}.items():
            a = vm.get_account(key)
            if a is not None and a.executable:
                continue
            out[name] = None if a is None else {'lamports': a.lamports, 'owner': str(a.owner), 'data': a.data.hex()}
        return out
    before = snapshot()
    result = vm.send_transaction(tx)
    failed = isinstance(result, f.FailedTransactionMetadata)
    meta = result.meta() if failed else result
    details = json.loads(meta.to_json())
    logs = list(meta.logs())
    return {'logs': logs, 'error': str(result.err()) if failed else None, 'before': before, 'after': snapshot(),
            'events': [l[14:] for l in logs if l.startswith('Program data: ')],
            'inner': details['inner_instructions'], 'return_data': details.get('return_data'),
            'transaction_base64': base64.b64encode(bytes(tx)).decode()}


def cases():
    for index, case in enumerate(f.cases()):
        yield {'name': f'prior-{index}', **case}
    base = f.cases()[0]
    def row(name, **values):
        return {**base, 'name': name, **values}
    for supply in (0, 1, U64//2, U64//2+1, U64):
        for mode in (False, True):
            yield row(f'supply-{supply}-{mode}', tts=supply, mayhem=mode)
    for reserve in (0, 9_999_999, 10_000_000, U64//2, U64-1, U64):
        for token_reserve in (0, 1, 10**15, U64):
            for spl in (False, True):
                yield row(f'arithmetic-{reserve}-{token_reserve}-{spl}', rqr=reserve, vtr=token_reserve, spl=spl)
    for denominator in (0, 1, 10**12-1, 10**12, 10**12+1):
        for reserve in (9_999_999, 10_000_000, U64):
            yield row(f'denominator-{denominator}-{reserve}', tts=10**15, irtr=0,
                      vault=2*10**15-denominator, rqr=reserve)
    for role in ('global', 'curve', 'mint', 'vault'):
        for label, mutation in (
            ('owner', {'owner': str(f.Pubkey.default())}),
            ('empty', {'length': 0}), ('zero-lamports', {'lamports': 0}),
            ('discriminator', {'patches': [(0, 'ff')]})):
            yield row(f'{role}-{label}', mutations={role: mutation})
    for length in (7, 8, 48, 80, 81, 82, 83, 115, 125, 165):
        yield row(f'curve-length-{length}', mutations={'curve': {'length': length}})
    for role in ('authority', 'vault', 'curve'):
        yield row(f'readonly-{role}', readonly=role)
    yield row('direct-without-pda-signature', direct=True)
    yield row('completed-curve', mutations={'curve': {'patches': [(48, '01')]}})
    yield row('completed-curve-overflowing-supply', tts=U64,
              mutations={'curve': {'patches': [(48, '01')]}})
    for reserve in (999_999, 1_000_000, 1_000_001):
        yield row(f'non-native-threshold-{reserve}', spl=True, rqr=reserve)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--build-comparison', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError('Refusing to overwrite existing output; choose a fresh path')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    build = json.loads(args.build_comparison.read_text()) if args.build_comparison else None
    if build:
        assert build['comparison']['candidate_sha256'] == sha(args.candidate)
        assert build['source_sha256'] == source_manifest(f.ROOT/'programs/pump', f.ROOT/'programs/pump', f.ROOT)
    inputs = {str(p.relative_to(f.ROOT)): sha(p) for p in (
        Path(__file__).resolve(), Path(f.__file__).resolve(), f.STUB,
        f.ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json',
        f.ROOT/'evidence/dependencies/spl_token_2022/deployed.so',
        f.ROOT/'evidence/dependencies/associated_token/deployed.so')}
    rows = []
    for case in cases():
        original = run(f.ORIGINAL, case); candidate = run(args.candidate, case)
        assert original['transaction_base64'] == candidate['transaction_base64']
        rows.append({'case': case, 'original': original, 'candidate': candidate,
                     'differences': [key for key in FIELDS if original[key] != candidate[key]]})
    assert all(sha(f.ROOT/name) == digest for name,digest in inputs.items())
    if build:
        assert build['source_sha256'] == source_manifest(f.ROOT/'programs/pump', f.ROOT/'programs/pump', f.ROOT)
    report = {'scope': __doc__, 'original_sha256': sha(f.ORIGINAL), 'candidate_sha256': sha(args.candidate),
              'inputs_sha256': inputs, 'compiled_source_sha256': build['source_sha256'] if build else None,
              'case_count': len(rows), 'mismatches': [r['case']['name'] for r in rows if r['differences']], 'cases': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(gzip.compress(json.dumps(report, separators=(',',':')).encode(),mtime=0))
    print(json.dumps({'cases':len(rows), 'mismatches':report['mismatches']}))
    if report['mismatches']:raise SystemExit(1)


if __name__ == '__main__':
    main()
