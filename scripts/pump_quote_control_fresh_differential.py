#!/usr/bin/env python3
"""Offline original-vs-recovered differential tests for the Pump quote-control instructions.

Covers initialize_quote_control, set_quote_control_admin, set_quote_control_reserves_admin,
add_quote_control_mint, remove_quote_control_mint and set_quote_control_mint_reserves.
Uses LiteSVM only, test-owned keys with normal signatures and synthetic QuoteControl state
on top of the captured Pump Global account. Nothing is broadcast.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse, base64, gzip, hashlib, json, pathlib, struct, platform, sys
from importlib.metadata import version
from solders.clock import Clock
from solders.transaction import VersionedTransaction
from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_diagnostic_audit import bound_input_key
from pump_differential_output import PumpReport

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / 'evidence/upstream/pump.json').is_file() and (p / 'programs/pump/Cargo.toml').is_file())
IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PROGRAM = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.from_string('11111111111111111111111111111111')
GLOBAL = Pubkey.find_program_address([b'global'], PROGRAM)[0]
QUOTE_CONTROL = Pubkey.find_program_address([b'quote-control'], PROGRAM)[0]
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
AUTHORITY = Keypair.from_seed(bytes([211]) * 32)
ADMIN = Keypair.from_seed(bytes([212]) * 32)
RESERVES_ADMIN = Keypair.from_seed(bytes([213]) * 32)
OUTSIDER = Keypair.from_seed(bytes([214]) * 32)
PAYER = Keypair.from_seed(bytes([215]) * 32)
CAPTURE = next(x for x in json.loads((ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name'] == 'pump')
GLOBAL_DATA = bytearray(base64.b64decode(CAPTURE['data_base64']))
GLOBAL_DATA[9:41] = bytes(AUTHORITY.pubkey())
KEYS = {'authority': AUTHORITY, 'admin': ADMIN, 'reserves_admin': RESERVES_ADMIN, 'outsider': OUTSIDER, 'payer': PAYER}
QC_DISC = hashlib.sha256(b'account:QuoteControl').digest()[:8]
IX = {x['name']: x for x in IDL['instructions']}
u64 = lambda n: struct.pack('<Q', n)
MINT_A, MINT_B, MINT_C = Pubkey(bytes([61]) * 32), Pubkey(bytes([62]) * 32), Pubkey(bytes([63]) * 32)


def quote_control_bytes(admin=None, reserves_admin=None, mints=(), reserved=bytes(32), length=None):
    body = bytes(admin or Pubkey.default()) + bytes(reserves_admin or Pubkey.default()) + reserved
    body += struct.pack('<I', len(mints)) + b''.join(bytes(m) + u64(r) for m, r in mints)
    data = QC_DISC + body
    if length is not None:
        data = data[:length] if length < len(data) else data + bytes(length - len(data))
    return data


def snapshot(vm, keys):
    result = {}
    for key in sorted(keys, key=str):
        a = vm.get_account(key)
        result[str(key)] = None if a is None else {
            'owner': str(a.owner), 'lamports': a.lamports,
            'data_base64': base64.b64encode(bytes(a.data)).decode(),
            'executable': a.executable, 'rent_epoch': a.rent_epoch}
    return result


def execute(binary, name, args=b'', state=None, roles=None, overrides=None, signers=None, drop=None, raw=None):
    assert signers is None, 'Only the explicitly declared test-owned signer set is supported'
    vm = LiteSVM().with_sigverify(True).with_blockhash_check(True).with_transaction_history(0)
    vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    vm.add_program_from_file(PROGRAM, binary)
    for kp in KEYS.values():
        vm.airdrop(kp.pubkey(), 10**12)
    vm.set_account(GLOBAL, Account(10**10, bytes(GLOBAL_DATA), PROGRAM))
    for key, acct in (state or {}).items():
        vm.set_account(key, acct)
    role = KEYS[roles or ('payer' if name == 'initialize_quote_control' else 'authority')]
    defaults = {'global': (GLOBAL, None), 'quote_control': (QUOTE_CONTROL, None), 'system_program': (SYSTEM, None),
                'event_authority': (EVENT, None), 'program': (PROGRAM, None), 'authority': (role.pubkey(), role), 'user': (role.pubkey(), role)}
    metas, tx_signers = [], {PAYER.pubkey(): PAYER}
    for spec in IX[name]['accounts']:
        acct = spec['name']
        if drop and acct in drop:
            continue
        key, kp = defaults[acct]
        writable, signer = bool(spec.get('writable')), bool(spec.get('signer'))
        if overrides and acct in overrides:
            o = overrides[acct]
            key = o.get('key', key); writable = o.get('writable', writable); signer = o.get('signer', signer)
        metas.append(AccountMeta(key, signer, writable))
        if signer and kp is not None and kp.pubkey() == key:
            tx_signers[kp.pubkey()] = kp
    data = raw if raw is not None else bytes(IX[name]['discriminator']) + args
    ix = Instruction(PROGRAM, data, metas)
    blockhash = vm.latest_blockhash()
    tx = Transaction.new_signed_with_payer([ix], PAYER.pubkey(), list(tx_signers.values()), blockhash)
    signed_bytes = bytes(tx)
    verification = tx.verify_with_results()
    decoded = VersionedTransaction.from_bytes(signed_bytes)
    assert verification and all(verification) and all(decoded.verify_with_results())
    assert bytes(decoded) == signed_bytes and tx.message.recent_blockhash == blockhash
    tracked = {GLOBAL, QUOTE_CONTROL, *[kp.pubkey() for kp in KEYS.values()], *(state or {}).keys()}
    tracked.update(m.pubkey for m in metas if m.pubkey not in {PROGRAM, SYSTEM})
    before = snapshot(vm, tracked)
    r = vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    after = snapshot(vm, tracked)
    rollback = None
    if failed:
        payer = str(PAYER.pubkey())
        unchanged = all(before[k] == after[k] for k in before if k != payer)
        pbefore, pafter = dict(before[payer]), dict(after[payer])
        fee = pbefore.pop('lamports') - pafter.pop('lamports')
        rollback = {'nonpayer_accounts_unchanged': unchanged,
                    'payer_except_fee_unchanged': pbefore == pafter,
                    'charged_fee': fee, 'expected_signature_fee': len(tx.signatures) * 5000}
    return {'error': str(r.err()) if failed else None,
            'before_accounts': before, 'after_accounts': after, 'rollback': rollback,
            'logs': list(meta.logs()),
            'event_payloads': [l[14:] for l in meta.logs() if l.startswith('Program data: ')],
            'inner_instructions': json.loads(meta.to_json())['inner_instructions'],
            'return_data': json.loads(meta.to_json())['return_data'],
            'compute_units': meta.compute_units_consumed(),
            'transaction_base64': base64.b64encode(signed_bytes).decode(),
            'transaction_sha256': hashlib.sha256(signed_bytes).hexdigest(),
            'signature_verification': verification, 'blockhash': str(blockhash),
            'sigverify_enabled': True, 'blockhash_check_enabled': True}


def qc_account(**kw):
    lamports = kw.pop('lamports', 10**9)
    owner = kw.pop('owner', PROGRAM)
    return {QUOTE_CONTROL: Account(lamports, quote_control_bytes(**kw), owner)}


def historical_cases():
    """Yield (label, name, kwargs) differential cases."""
    for role in ['payer', 'authority', 'outsider']:
        yield f'init/{role}', 'initialize_quote_control', {'roles': role}
    yield 'init/existing', 'initialize_quote_control', {'state': qc_account(admin=ADMIN.pubkey())}
    yield 'init/user_unsigned', 'initialize_quote_control', {'overrides': {'user': {'signer': False}}}
    yield 'init/user_readonly', 'initialize_quote_control', {'overrides': {'user': {'writable': False}}}
    yield 'init/wrong_pda', 'initialize_quote_control', {'overrides': {'quote_control': {'key': Pubkey(bytes([90]) * 32)}}}
    yield 'init/wrong_system', 'initialize_quote_control', {'overrides': {'system_program': {'key': PROGRAM}}}
    yield 'init/prefunded', 'initialize_quote_control', {'state': {QUOTE_CONTROL: Account(5000, b'', SYSTEM)}}
    base = dict(admin=ADMIN.pubkey(), reserves_admin=RESERVES_ADMIN.pubkey(), mints=[(MINT_A, 1000)])
    for name, args in [('set_quote_control_admin', [bytes(OUTSIDER.pubkey()), bytes(32), bytes(ADMIN.pubkey())]),
                       ('set_quote_control_reserves_admin', [bytes(OUTSIDER.pubkey()), bytes(32), bytes(RESERVES_ADMIN.pubkey())])]:
        for i, arg in enumerate(args):
            for role in ['authority', 'admin', 'reserves_admin', 'outsider']:
                yield f'{name}/{role}/arg{i}', name, {'args': arg, 'roles': role, 'state': qc_account(**base)}
        yield f'{name}/empty_state', name, {'args': args[0], 'state': qc_account()}
        yield f'{name}/no_state', name, {'args': args[0]}
        yield f'{name}/unsigned', name, {'args': args[0], 'state': qc_account(**base), 'overrides': {'authority': {'signer': False}}}
        yield f'{name}/qc_readonly', name, {'args': args[0], 'state': qc_account(**base), 'overrides': {'quote_control': {'writable': False}}}
        yield f'{name}/qc_wrong_owner', name, {'args': args[0], 'state': qc_account(owner=SYSTEM, **base)}
        yield f'{name}/qc_wrong_key', name, {'args': args[0], 'state': {Pubkey(bytes([90]) * 32): Account(10**9, quote_control_bytes(**base), PROGRAM)}, 'overrides': {'quote_control': {'key': Pubkey(bytes([90]) * 32)}}}
        yield f'{name}/global_wrong', name, {'args': args[0], 'state': qc_account(**base), 'overrides': {'global': {'key': QUOTE_CONTROL}}}
        yield f'{name}/event_wrong', name, {'args': args[0], 'state': qc_account(**base), 'overrides': {'event_authority': {'key': Pubkey(bytes([92]) * 32)}}}
        yield f'{name}/short_args', name, {'args': args[0][:31], 'state': qc_account(**base)}
    mint_states = {'empty': [], 'one': [(MINT_A, 1000)], 'two': [(MINT_A, 1000), (MINT_B, 2000)]}
    for sname, mints in mint_states.items():
        st = dict(admin=ADMIN.pubkey(), reserves_admin=RESERVES_ADMIN.pubkey(), mints=mints)
        for mint in [MINT_A, MINT_B, MINT_C, Pubkey.default(), Pubkey.from_string('So11111111111111111111111111111111111111112')]:
            for role in ['authority', 'admin', 'reserves_admin', 'outsider']:
                for reserves in [0, 1, 2**64 - 1]:
                    yield f'add/{sname}/{mint}/{role}/{reserves}', 'add_quote_control_mint', {'args': bytes(mint) + u64(reserves), 'roles': role, 'state': qc_account(**st)}
                    yield f'set_reserves/{sname}/{mint}/{role}/{reserves}', 'set_quote_control_mint_reserves', {'args': bytes(mint) + u64(reserves), 'roles': role, 'state': qc_account(**st)}
                yield f'remove/{sname}/{mint}/{role}', 'remove_quote_control_mint', {'args': bytes(mint), 'roles': role, 'state': qc_account(**st)}
    many = [(Pubkey(bytes([100 + i]) * 32), i) for i in range(20)]
    for role in ['admin', 'reserves_admin', 'authority']:
        yield f'add/many/{role}', 'add_quote_control_mint', {'args': bytes(MINT_C) + u64(7), 'roles': role, 'state': qc_account(admin=ADMIN.pubkey(), reserves_admin=RESERVES_ADMIN.pubkey(), mints=many)}
        yield f'remove/many_middle/{role}', 'remove_quote_control_mint', {'args': bytes(many[7][0]), 'roles': role, 'state': qc_account(admin=ADMIN.pubkey(), reserves_admin=RESERVES_ADMIN.pubkey(), mints=many)}
    for role in ['admin', 'authority']:
        st = qc_account(admin=ADMIN.pubkey(), reserves_admin=RESERVES_ADMIN.pubkey(), mints=[(MINT_A, 1)])
        yield f'add/no_system/{role}', 'add_quote_control_mint', {'args': bytes(MINT_B) + u64(1), 'roles': role, 'state': st, 'drop': ['system_program']}
        yield f'add/authority_readonly/{role}', 'add_quote_control_mint', {'args': bytes(MINT_B) + u64(1), 'roles': role, 'state': st, 'overrides': {'authority': {'writable': False}}}
        yield f'add/zero_admin_state/{role}', 'add_quote_control_mint', {'args': bytes(MINT_B) + u64(1), 'roles': role, 'state': qc_account()}
        yield f'add/padded_state/{role}', 'add_quote_control_mint', {'args': bytes(MINT_B) + u64(1), 'roles': role, 'state': {QUOTE_CONTROL: Account(10**9, quote_control_bytes(admin=ADMIN.pubkey(), mints=[(MINT_A, 1)], length=400), PROGRAM)}}
        yield f'remove/padded_state/{role}', 'remove_quote_control_mint', {'args': bytes(MINT_A), 'roles': role, 'state': {QUOTE_CONTROL: Account(10**9, quote_control_bytes(admin=ADMIN.pubkey(), mints=[(MINT_A, 1), (MINT_B, 2)], length=400), PROGRAM)}}
        yield f'add/low_rent/{role}', 'add_quote_control_mint', {'args': bytes(MINT_B) + u64(1), 'roles': role, 'state': qc_account(lamports=1, admin=ADMIN.pubkey(), mints=[(MINT_A, 1)])}
    yield 'add/truncated_vec', 'add_quote_control_mint', {'args': bytes(MINT_B) + u64(1), 'roles': 'admin', 'state': {QUOTE_CONTROL: Account(10**9, quote_control_bytes(admin=ADMIN.pubkey(), mints=[(MINT_A, 1)])[:-4], PROGRAM)}}
    yield 'add/bad_discriminator', 'add_quote_control_mint', {'args': bytes(MINT_B) + u64(1), 'roles': 'admin', 'state': {QUOTE_CONTROL: Account(10**9, b'\0' * 8 + quote_control_bytes(admin=ADMIN.pubkey())[8:], PROGRAM)}}


def cases():
    yield from historical_cases()
    # These two use a different fee payer so message privilege union cannot mask
    # the missing signer or readonly user condition in the historical fixtures.
    for key in ['signer', 'writable']:
        yield f'fresh/init_user_{key}_false', 'initialize_quote_control', {
            'roles': 'authority', 'overrides': {'user': {key: False}}}
    # Captured layout: 108-byte header and 40-byte mint entries, with initial
    # capacity 50 and maximum listed length 256. Test both sides of each boundary.
    for n in [49, 50, 51, 255, 256]:
        mints = [(Pubkey(hashlib.sha256(f'quote-control-mint-{i}'.encode()).digest()), i) for i in range(n)]
        for role in ['authority', 'admin']:
            yield f'fresh/add_capacity/{n}/{role}', 'add_quote_control_mint', {
                'args': bytes(MINT_C) + u64(123), 'roles': role,
                'state': qc_account(admin=ADMIN.pubkey(), reserves_admin=RESERVES_ADMIN.pubkey(), mints=mints,
                                    reserved=bytes([17]) * 32, length=108 + max(50, n) * 40)}
    native_2022 = Pubkey.from_string('9pan9bMn5HatX4EJdBwg9VgCa7Uz5HL8N1m5D3NdXejP')
    for role in ['authority', 'admin']:
        yield f'fresh/add_token2022_native/{role}', 'add_quote_control_mint', {
            'args': bytes(native_2022) + u64(1), 'roles': role,
            'state': qc_account(admin=ADMIN.pubkey())}
        # Minimal rent top-up and realloc use the normal signed authority payer.
        yield f'fresh/add_rent_topup/{role}', 'add_quote_control_mint', {
            'args': bytes(MINT_B) + u64(99), 'roles': role,
            'state': qc_account(admin=ADMIN.pubkey(), mints=[(MINT_A, 12)], lamports=2000000)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--candidate', type=pathlib.Path, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    a = p.parse_args()
    original = ROOT / 'evidence/original/pump/deployed.so'
    digest = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    bound_files = [original, a.candidate.resolve(), pathlib.Path(__file__).resolve(),
                   ROOT / 'scripts/pump_diagnostic_audit.py',
                   ROOT / 'scripts/pump_differential_output.py',
                   ROOT / 'evidence/upstream/pump.json',
                   ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json']
    # Build evidence is adjacent to both clean-target artifacts and frozen package
    # candidates. No work-only path is required for clean-checkout execution.
    candidate = a.candidate.resolve()
    for directory in [candidate.parent, candidate.parent.parent]:
        build_report = directory / 'build-comparison.json'
        if build_report.is_file():
            build_data = json.loads(build_report.read_text())
            assert build_data['comparison']['candidate_sha256'] == digest(candidate)
            bound_files.append(build_report)
            for source, expected in build_data['source_sha256'].items():
                source_path = ROOT / source
                assert digest(source_path) == expected, source
                bound_files.append(source_path)
            break
    else:
        # When an independently supplied ELF has no adjacent build report,
        # record current source bytes without claiming they produced that ELF.
        for source_path in (ROOT / 'programs/pump').rglob('*'):
            if source_path.is_file() and 'target' not in source_path.relative_to(ROOT / 'programs/pump').parts and (
                    source_path.suffix == '.rs' or source_path.name in {'Cargo.toml', 'Cargo.lock'}):
                bound_files.append(source_path)
    # Refuse to publish through any input before a single case executes.
    publisher = PumpReport(a.output, ROOT, a.candidate, __file__,
                           extra_inputs=[ROOT / 'programs/pump', *bound_files])
    bound = {bound_input_key(f, ROOT): digest(f) for f in bound_files}
    results, mismatches = [], 0
    compare_keys = ['error', 'before_accounts', 'after_accounts', 'rollback', 'event_payloads',
                    'inner_instructions', 'return_data', 'transaction_base64',
                    'signature_verification', 'blockhash', 'sigverify_enabled', 'blockhash_check_enabled']
    for label, name, kw in cases():
        o = execute(original, name, **kw)
        c = execute(a.candidate, name, **kw)
        differences = [k for k in compare_keys if o[k] != c[k]]
        row = {'case': label, 'instruction': name, 'original': o, 'candidate': c,
               'matches': not differences, 'different_fields': differences}
        mismatches += bool(differences)
        if differences:
            print('MISMATCH', label, differences, flush=True)
        results.append(row)
    assert all(digest(ROOT / f) == value for f, value in bound.items()), 'Inputs changed during run'
    report = {'scope': 'Fresh isolated main42 plus six quote-control handlers; offline LiteSVM only. Historical results are not reused.',
              'cases': len(results), 'mismatches': mismatches, 'compare_keys': compare_keys,
              'bound_inputs_sha256': bound, 'python': sys.version, 'platform': platform.platform(),
              'solders_version': version('solders'),
              'fixture_policy': 'Ordinary test-owned synthetic keys, explicit signature and blockhash checks; complete signed transaction bytes saved. No live broadcast.',
              'results': results}
    publisher.write(gzip.compress(json.dumps(report).encode(), mtime=0))
    print(f'{len(results)} cases, {mismatches} mismatches', flush=True)
    return 1 if mismatches else 0


if __name__ == '__main__':
    raise SystemExit(main())
