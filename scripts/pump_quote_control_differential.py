#!/usr/bin/env python3
"""Offline original-vs-recovered differential tests for the Pump quote-control instructions.

Covers initialize_quote_control, set_quote_control_admin, set_quote_control_reserves_admin,
add_quote_control_mint, remove_quote_control_mint and set_quote_control_mint_reserves.
Uses LiteSVM only, test-owned keys with normal signatures and synthetic QuoteControl state
on top of the captured Pump Global account. Nothing is broadcast.
"""
import argparse, base64, gzip, hashlib, json, pathlib, struct
from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = pathlib.Path(__file__).resolve().parents[1]
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


def execute(binary, name, args=b'', state=None, roles=None, overrides=None, signers=None, drop=None, raw=None):
    """Run one instruction. state: dict account->Account; roles: signer role for the authority/user slot."""
    vm = LiteSVM().with_transaction_history(0)
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
        if signer and kp is not None:
            tx_signers[kp.pubkey()] = kp
    data = raw if raw is not None else bytes(IX[name]['discriminator']) + args
    ix = Instruction(PROGRAM, data, metas)
    tx = Transaction.new_signed_with_payer([ix], PAYER.pubkey(), list(tx_signers.values()), vm.latest_blockhash())
    r = vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    qc = vm.get_account(QUOTE_CONTROL)
    return {'error': str(r.err()) if failed else None,
            'quote_control': None if qc is None else {'owner': str(qc.owner), 'lamports': qc.lamports, 'data_hex': bytes(qc.data).hex()},
            'global_hex_sha256': hashlib.sha256(bytes(vm.get_account(GLOBAL).data)).hexdigest(),
            'payer_lamports': vm.get_account(PAYER.pubkey()).lamports,
            'role_lamports': vm.get_account(role.pubkey()).lamports,
            'logs': [l for l in meta.logs() if 'consumed' not in l],
            'event_payloads': [l[14:] for l in meta.logs() if l.startswith('Program data: ')],
            'inner_instructions': json.loads(meta.to_json())['inner_instructions']}


def qc_account(**kw):
    lamports = kw.pop('lamports', 10**9)
    owner = kw.pop('owner', PROGRAM)
    return {QUOTE_CONTROL: Account(lamports, quote_control_bytes(**kw), owner)}


def cases():
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--candidate', type=pathlib.Path)
    p.add_argument('--output', type=pathlib.Path)
    p.add_argument('--original-only', action='store_true')
    a = p.parse_args()
    original = ROOT / 'evidence/original/pump/deployed.so'
    results, mismatches = [], 0
    for label, name, kw in cases():
        o = execute(original, name, **kw)
        row = {'case': label, 'instruction': name, 'original': o}
        if not a.original_only:
            c = execute(a.candidate, name, **kw)
            keys = ['error', 'quote_control', 'global_hex_sha256', 'payer_lamports', 'role_lamports', 'event_payloads', 'inner_instructions']
            row['candidate'] = c
            row['matches'] = all(o[k] == c[k] for k in keys)
            mismatches += not row['matches']
            if not row['matches']:
                print('MISMATCH', label, {k: (o[k], c[k]) for k in keys if o[k] != c[k]})
        results.append(row)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(a.output, 'wt') as f:
            json.dump({'scope': 'Offline LiteSVM differential; synthetic QuoteControl state, test-owned keys.', 'cases': len(results), 'mismatches': mismatches, 'results': results}, f)
    print(f'{len(results)} cases, {mismatches} mismatches')
    return 1 if mismatches else 0


if __name__ == '__main__':
    raise SystemExit(main())
