#!/usr/bin/env python3
"""Bounded pump create_v2 Mayhem-mode differential with a fixed captured Mayhem.

Extends the retained create_v2 coverage with its unresolved Mayhem mode: the
real pump `create_v2` Mayhem branch, which internally `invoke_signed`s into the
captured Mayhem program's `initialize_mayhem_state` using pump's off-curve
["mint-authority"] PDA as the signer. One valid transaction exercises BOTH the
pump create_v2 Mayhem branch AND the genuine pump->mayhem CPI. The Mayhem
executable is the captured ORIGINAL on both sides: the only variable under test
is the Pump ELF (captured original vs candidate). No Mayhem source work, no
initializer reconstruction, no synthetic signer or oracle fake.

Mayhem preconditions are honest: mayhem `global_params` is created by sending
mayhem's own `initialize_global_params` (ordinary admin signature); the pump
global is seeded from the captured config snapshot with the create_v2 /
mayhem-mode / holder toggles and the quote whitelist slot patched per case.

New bounded dimensions beyond `scripts/pump_create_mayhem_differential.py`:
  - Mayhem + whitelisted quote-mint creation (line-758 whitelist admission),
    Mayhem + WSOL quote (native normalization), unlisted quote rejections
    (with and without a quote-control record) and the unsupported quote mint;
  - Mayhem account boundaries (wrong program id, wrong PDA bindings, readonly
    and bogus token vaults, pre-existing mayhem_state, missing accounts);
  - holder-reward and deprecated-cashback option boundaries in Mayhem mode.
"""
import argparse
import base64
import gzip
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

REPO = Path('/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained')
ROOT = REPO
IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PROGRAM = Pubkey.from_string(IDL['address'])
ORIGINAL_PUMP = ROOT / 'evidence/original/pump/deployed.so'
ORIGINAL_MAYHEM = ROOT / 'evidence/original/mayhem/deployed.so'
MAYHEM = Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
META = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
UNSUPPORTED_QUOTE_MINT = Pubkey.from_string('9pan9bMn5HatX4EJdBwg9VgCa7Uz5HL8N1m5D3NdXejP')
USER = Keypair.from_seed(bytes([211]) * 32)
MINT = Keypair.from_seed(bytes([212]) * 32)
OTHER = Keypair.from_seed(bytes([213]) * 32)
ADMIN = Keypair.from_seed(bytes([214]) * 32)

GLOBAL = Pubkey.find_program_address([b'global'], PROGRAM)[0]
CURVE = Pubkey.find_program_address([b'bonding-curve', bytes(MINT.pubkey())], PROGRAM)[0]
MA = Pubkey.find_program_address([b'mint-authority'], PROGRAM)[0]
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
GLOBAL_PARAMS = Pubkey.find_program_address([b'global-params'], MAYHEM)[0]
SOL_VAULT = Pubkey.find_program_address([b'sol-vault'], MAYHEM)[0]
MAYHEM_STATE = Pubkey.find_program_address([b'mayhem-state', bytes(MINT.pubkey())], MAYHEM)[0]
QUOTE_CONTROL = Pubkey.find_program_address([b'quote-control'], PROGRAM)[0]


def _ata(owner, mint, prog=TOKEN22):
    return Pubkey.find_program_address([bytes(owner), bytes(prog), bytes(mint)], ATA)[0]


ABC = _ata(CURVE, MINT.pubkey())
MTV = _ata(SOL_VAULT, MINT.pubkey())

CAPTURE = next(x for x in json.loads((ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name'] == 'pump')

NAMES = {'mint': MINT.pubkey(), 'mint_authority': MA, 'bonding_curve': CURVE, 'associated_bonding_curve': ABC,
         'global': GLOBAL, 'user': USER.pubkey(), 'system_program': Pubkey.default(), 'token_program': TOKEN22,
         'associated_token_program': ATA, 'mayhem_program_id': MAYHEM, 'global_params': GLOBAL_PARAMS,
         'sol_vault': SOL_VAULT, 'mayhem_state': MAYHEM_STATE, 'mayhem_token_vault': MTV,
         'event_authority': EVENT, 'program': PROGRAM}

COMPUTE_LINE = re.compile(r'Program (\w+) consumed (\d+) of (\d+) compute units')


def _string(s):
    b = s.encode()
    return struct.pack('<I', len(b)) + b


def _anchor_disc(name):
    return hashlib.sha256(b'global:' + name.encode()).digest()[:8]


def _init_global_params(vm):
    metas = [AccountMeta(ADMIN.pubkey(), True, True), AccountMeta(GLOBAL_PARAMS, False, True), AccountMeta(Pubkey.default(), False, False)]
    tx = Transaction.new_signed_with_payer([Instruction(MAYHEM, _anchor_disc('initialize_global_params'), metas)], ADMIN.pubkey(), [ADMIN], vm.latest_blockhash())
    return vm.send_transaction(tx)


def run(c, pump_bin=ORIGINAL_PUMP):
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(PROGRAM, pump_bin)
    vm.add_program_from_file(MAYHEM, ORIGINAL_MAYHEM)  # captured original on both sides
    for name, key in [('spl_token', TOKEN), ('spl_token_2022', TOKEN22), ('associated_token', ATA), ('token_metadata', META)]:
        vm.add_program_from_file(key, ROOT / 'evidence/dependencies' / name / 'deployed.so')
    vm.set_clock(Clock(100, 1700000000, 0, 0, 1700000000))
    vm.airdrop(USER.pubkey(), 10**12)
    vm.airdrop(ADMIN.pubkey(), 10**12)
    gd = bytearray(base64.b64decode(CAPTURE['data_base64']))
    gd[450] = c.get('create_v2_enabled', 1)
    gd[515] = c.get('mayhem_mode_enabled', 1)
    gd[1086] = c.get('holder_reward_enabled', 1)
    for off, hexdata in c.get('global_patches', []):
        gd[off:off + len(bytes.fromhex(hexdata))] = bytes.fromhex(hexdata)
    vm.set_account(GLOBAL, Account(10**9, bytes(gd), PROGRAM))
    if c.get('init_global_params', True):
        r = _init_global_params(vm)
        if isinstance(r, FailedTransactionMetadata):
            raise SystemExit('setup: initialize_global_params failed: %s' % r.err())
        dur = c.get('duration_hours')
        if dur is not None:
            a = vm.get_account(GLOBAL_PARAMS)
            d = bytearray(a.data)
            d[137] = dur
            vm.set_account(GLOBAL_PARAMS, Account(a.lamports, bytes(d), a.owner))
    names = dict(NAMES)
    snap_keys = set(str(v) for v in names.values())
    if c.get('quote'):
        quote = Pubkey.from_string(c['quote']) if isinstance(c['quote'], str) else c['quote']
        qt = TOKEN if c.get('quote_tokenkeg') else TOKEN22
        mint_data = struct.pack('<I', 1) + bytes(USER.pubkey()) + struct.pack('<Q', 10**15) + bytes([6, 1]) + bytes(36)
        vm.set_account(quote, Account(10000000, mint_data, qt))
        if c.get('quote_whitelisted', False):
            g = bytearray(vm.get_account(GLOBAL).data)
            g[1013:1045] = bytes(quote)
            vm.set_account(GLOBAL, Account(10**9, bytes(g), PROGRAM))
        names.update(quote_mint=quote, associated_quote_bonding_curve=_ata(CURVE, quote, qt), quote_token_program=qt)
    if c.get('quote_control_entries') is not None:
        entries = c['quote_control_entries']
        blob = hashlib.sha256(b'account:QuoteControl').digest()[:8] + bytes(USER.pubkey()) * 2 + bytes(32) + struct.pack('<I', len(entries)) + b''.join(bytes(Pubkey.from_string(k)) + struct.pack('<Q', n) for k, n in entries)
        vm.set_account(QUOTE_CONTROL, Account(10**9, blob, PROGRAM))
        names['quote_control'] = QUOTE_CONTROL
    if c.get('preexisting_mayhem_state'):
        vm.set_account(MAYHEM_STATE, Account(10**9, bytes(8 + 64), MAYHEM))
    ix = next(x for x in IDL['instructions'] if x['name'] == 'create_v2')
    metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
    if c.get('readonly'):
        key = names[c['readonly']]
        metas = [AccountMeta(m.pubkey, m.is_signer, False) if m.pubkey == key else m for m in metas]
    if c.get('wrong'):
        key = names[c['wrong']]
        metas = [AccountMeta(OTHER.pubkey() if m.pubkey == key else m.pubkey, m.is_signer, m.is_writable) for m in metas]
    if c.get('quote'):
        metas += [AccountMeta(names['quote_mint'], False, False),
                  AccountMeta(names['associated_quote_bonding_curve'], False, True),
                  AccountMeta(names['quote_token_program'], False, False)]
    if c.get('quote_control_entries') is not None:
        metas.append(AccountMeta(names['quote_control'], False, False))
    metas = metas[:c.get('account_count', 100)]
    payload = (bytes(ix['discriminator']) + _string(c.get('name', 'Synthetic Coin')) + _string(c.get('symbol', 'SYNTH'))
               + _string(c.get('uri', 'https://example.invalid/metadata.json'))
               + bytes(Pubkey.from_string(c.get('creator', str(USER.pubkey()))))
               + bytes([1 if c.get('is_mayhem_mode', True) else 0]) + bytes.fromhex(c.get('optional_args', '')))
    signers = [k for k in [USER, MINT] if k.pubkey() in {m.pubkey for m in metas if m.is_signer} | {USER.pubkey()}]
    tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1400000), Instruction(PROGRAM, payload, metas)], USER.pubkey(), signers, vm.latest_blockhash())
    assert all(tx.verify_with_results())

    def snap():
        out = {}
        for k in sorted(snap_keys):
            key = Pubkey.from_string(k)
            a = vm.get_account(key)
            if a and a.executable:
                continue
            out[k] = None if a is None else {'lamports': a.lamports, 'owner': str(a.owner), 'data': a.data.hex()}
        return out

    before = snap()
    r = vm.send_transaction(tx)
    fail = isinstance(r, FailedTransactionMetadata)
    m = r.meta() if fail else r
    raw = json.loads(m.to_json())
    return {'error': str(r.err()) if fail else None, 'logs': m.logs(),
            'events': [l for l in m.logs() if l.startswith('Program data:')],
            'inner': raw['inner_instructions'], 'return': raw.get('return_data'),
            'before': before, 'after': snap(),
            'compute': [{'program': x.group(1), 'consumed': int(x.group(2)), 'budget': int(x.group(3))}
                        for x in (COMPUTE_LINE.search(l) for l in m.logs()) if x],
            'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'transaction_sha256': hashlib.sha256(bytes(tx)).hexdigest(),
            'verified_signature_count': len(tx.signatures),
            'program_sha256': {str(PROGRAM): hashlib.sha256(Path(pump_bin).read_bytes()).hexdigest(),
                               str(MAYHEM): hashlib.sha256(ORIGINAL_MAYHEM.read_bytes()).hexdigest()}}


QUOTE_MINT_WHITELISTED = str(Pubkey.from_bytes(bytes([7]) * 32))
QUOTE_MINT_UNLISTED = str(Pubkey.from_bytes(bytes([8]) * 32))


def cases():
    out = [{'case': 'mayhem-base'},
           {'case': 'mayhem-duration-7', 'duration_hours': 7},
           {'case': 'mayhem-name-32', 'name': 'x' * 32}]
    # Mayhem quote-mint admission (the create_v2 line-754..758 branch).
    out += [{'case': 'mayhem-quote-whitelisted', 'quote': QUOTE_MINT_WHITELISTED, 'quote_whitelisted': True},
            {'case': 'mayhem-quote-wsol', 'quote': str(WSOL), 'quote_tokenkeg': True},
            {'case': 'mayhem-quote-unlisted-no-control', 'quote': QUOTE_MINT_UNLISTED},
            {'case': 'mayhem-quote-configured-unlisted', 'quote': QUOTE_MINT_UNLISTED,
             'quote_control_entries': [(QUOTE_MINT_UNLISTED, 123456789)]},
            {'case': 'mayhem-quote-unsupported-mint', 'quote': str(UNSUPPORTED_QUOTE_MINT), 'quote_whitelisted': True}]
    # Holder reward / deprecated cashback option boundaries in Mayhem mode.
    out += [{'case': 'mayhem-holder-enabled', 'optional_args': '00' * 9 + '01'},
            {'case': 'mayhem-holder-disabled', 'holder_reward_enabled': 0, 'optional_args': '00' * 9 + '01'},
            {'case': 'mayhem-cashback-deprecated', 'optional_args': '01'},
            {'case': 'mayhem-optional-fee-301', 'optional_args': '00' + struct.pack('<Q', 301).hex() + '00'},
            {'case': 'mayhem-zero-creator', 'creator': str(Pubkey.default())}]
    # Mayhem account boundaries.
    out += [{'case': 'mayhem-mode-disabled', 'mayhem_mode_enabled': 0},
            {'case': 'create-v2-disabled', 'create_v2_enabled': 0},
            {'case': 'wrong-mayhem-program', 'wrong': 'mayhem_program_id'},
            {'case': 'wrong-global-params', 'wrong': 'global_params'},
            {'case': 'wrong-sol-vault', 'wrong': 'sol_vault'},
            {'case': 'wrong-mayhem-state', 'wrong': 'mayhem_state'},
            {'case': 'wrong-mint-authority', 'wrong': 'mint_authority'},
            {'case': 'readonly-mayhem-state', 'readonly': 'mayhem_state'},
            {'case': 'readonly-mayhem-token-vault', 'readonly': 'mayhem_token_vault'},
            {'case': 'readonly-sol-vault', 'readonly': 'sol_vault'},
            {'case': 'mayhem-token-vault-bogus', 'wrong': 'mayhem_token_vault'},
            {'case': 'mayhem-state-preexisting', 'preexisting_mayhem_state': True},
            {'case': 'missing-accounts-15', 'account_count': 15},
            {'case': 'missing-accounts-13', 'account_count': 13},
            {'case': 'name-33', 'name': 'x' * 33}]
    return out


FIELDS = ['before', 'after', 'error', 'events', 'inner', 'return']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate-pump', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--only', default='')
    args = parser.parse_args()
    assert not args.output.exists(), 'Retain prior attempts; output must be fresh'
    candidate = args.candidate_pump.resolve()
    rows = []
    bad = []
    for c in cases():
        if args.only and args.only not in c['case']:
            continue
        x = run(c)
        y = run(c, candidate)
        diff = [k for k in FIELDS if x[k] != y[k]]
        rows.append({'case': c, 'original': x, 'candidate': y, 'mismatches': diff,
                     'ordered_logs_equal': x['logs'] == y['logs']})
        print(json.dumps({'case': c['case'], 'original_error': x['error'], 'candidate_error': y['error'],
                          'mismatches': diff}), flush=True)
        if diff:
            bad.append(c['case'])
    report = {'scope': __doc__,
              'mode': 'original-versus-candidate; captured Mayhem ELF fixed on both sides',
              'original_pump_sha256': hashlib.sha256(ORIGINAL_PUMP.read_bytes()).hexdigest(),
              'candidate_pump_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
              'original_mayhem_sha256': hashlib.sha256(ORIGINAL_MAYHEM.read_bytes()).hexdigest(),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'python_version': sys.version,
              'case_count': len(rows),
              'original_successes': sum(1 for r in rows if r['original']['error'] is None),
              'verified_outer_signatures': sum(r['original']['verified_signature_count'] + r['candidate']['verified_signature_count'] for r in rows),
              'mismatches': bad, 'cases': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0))
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))
    if bad:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
