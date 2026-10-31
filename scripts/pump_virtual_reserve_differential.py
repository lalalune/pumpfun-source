#!/usr/bin/env python3
"""Main Pump reserve-sync comparison using an unchanged local signer fixture.

The synthetic caller supplies the required PDA signature in a local VM. This
is not evidence of a production caller or live reachability. No other program
is reconstructed or changed, and no transaction is broadcast.
Every execution uses the same frozen program and configuration bytes; receipt
hashes identify those snapshots even if the input paths later change.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import base64
import gzip
import hashlib
import json
import struct
from pathlib import Path

import pump_set_mayhem_virtual_params_differential as f
from build_source_manifest import source_manifest
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport

FIELDS = ('error', 'before', 'after', 'events', 'inner', 'return_data')
U64 = 2**64 - 1
RETAINED_SHA256 = {
    'original': '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    'stub': '2cbb2d1908b5a2e6416b3c2d01693c45495706d8556fac07883bc5ac72f44b3b',
    'spl_token_2022': '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    'associated_token': '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}


def program_paths():
    return {'original': f.ORIGINAL, 'stub': f.STUB,
            'spl_token_2022': f.ROOT / 'evidence/dependencies/spl_token_2022/deployed.so',
            'associated_token': f.ROOT / 'evidence/dependencies/associated_token/deployed.so'}


def run(binary, case, *, programs=None, capture=None):
    binary = binary if isinstance(binary, bytes) else pin_program(binary).read_bytes()
    if programs is None:
        programs = {name: pin_program(path).read_bytes() for name, path in program_paths().items()}
    vm = f.LiteSVM().with_transaction_history(0).with_sigverify(True)
    vm.add_program(f.PUMP, binary)
    vm.add_program(f.MAYHEM, programs['stub'])
    for key, name in ((f.TOKEN22, 'spl_token_2022'), (f.ATA, 'associated_token')):
        vm.add_program(key, programs[name])
    vm.airdrop(f.PAYER.pubkey(), 10**10)
    global_data = bytearray(base64.b64decode((f.CAPTURE if capture is None else capture)['data_base64']))
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
    if not all(tx.verify_with_results()):
        raise ValueError('transaction signature verification failed')
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
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    candidate = pin_program(args.candidate).read_bytes()
    paths = program_paths()
    programs = {name: pin_program(path).read_bytes() for name, path in paths.items()}
    for name, raw in programs.items():
        if sha(raw) != RETAINED_SHA256[name]:
            raise ValueError(f'retained {name} image hash mismatch')
    config_path = f.ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json'
    config_bytes = config_path.read_bytes()
    captures = [item for item in json.loads(config_bytes)['accounts'] if item['program_name'] == 'pump']
    if len(captures) != 1:
        raise ValueError('configuration snapshot must contain one Pump account')
    capture = captures[0]
    supplied_build = args.build_comparison is not None
    build = json.loads(args.build_comparison.read_text()) if supplied_build else None
    if supplied_build:
        if not isinstance(build, dict) or not isinstance(build.get('comparison'), dict):
            raise ValueError('invalid build comparison')
        if build['comparison'].get('candidate_sha256') != sha(candidate):
            raise ValueError('candidate does not match build comparison')
        if build['source_sha256'] != source_manifest(f.ROOT/'programs/pump', f.ROOT/'programs/pump', f.ROOT):
            raise ValueError('source does not match build comparison')
    source_paths = {'scripts/pump_virtual_reserve_differential.py': Path(__file__).resolve(),
                    'scripts/pump_set_mayhem_virtual_params_differential.py': Path(f.__file__).resolve(),
                    'scripts/pump_amm_reusable_harness.py': Path(pin_program.__code__.co_filename).resolve()}
    source_hashes = {name: sha(path.read_bytes()) for name, path in source_paths.items()}
    inputs = {str(paths[name].relative_to(f.ROOT)): sha(raw) for name, raw in programs.items()}
    inputs.update(source_hashes)
    inputs[str(config_path.relative_to(f.ROOT))] = sha(config_bytes)
    rows = []
    for case in cases():
        original = run(programs['original'], case, programs=programs, capture=capture)
        compared = run(candidate, case, programs=programs, capture=capture)
        if original['transaction_base64'] != compared['transaction_base64']:
            raise ValueError('original and candidate transactions differ')
        rows.append({'case': case, 'original': original, 'candidate': compared,
                     'differences': [key for key in FIELDS if original[key] != compared[key]]})
    if any(sha(path.read_bytes()) != source_hashes[name] for name, path in source_paths.items()):
        raise ValueError('differential source changed during run')
    if supplied_build:
        if build['source_sha256'] != source_manifest(f.ROOT/'programs/pump', f.ROOT/'programs/pump', f.ROOT):
            raise ValueError('source changed during run')
    report = {'scope': __doc__, 'original_sha256': sha(programs['original']), 'candidate_sha256': sha(candidate),
              'inputs_sha256': inputs, 'compiled_source_sha256': build['source_sha256'] if supplied_build else None,
              'case_count': len(rows), 'mismatches': [r['case']['name'] for r in rows if r['differences']], 'cases': rows}
    # Publish through the shared bound publisher, as the sibling differentials
    # do: the report is staged beside the output and linked into place only
    # once complete, so an interrupted publish never leaves a truncated
    # receipt at the final path, and the output may not alias an input.
    publisher = PumpReport(args.output, f.ROOT, args.candidate, __file__,
                           extra_inputs=[Path(f.__file__),
                                         Path(pin_program.__code__.co_filename),
                                         config_path, *program_paths().values()],
                           overwrite=False)
    publisher.write(gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0))
    print(json.dumps({'cases':len(rows), 'mismatches':report['mismatches']}))
    if report['mismatches']:raise SystemExit(1)


if __name__ == '__main__':
    main()
