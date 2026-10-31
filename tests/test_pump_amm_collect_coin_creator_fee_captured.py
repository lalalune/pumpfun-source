"""Captured-program checks for PumpSwap `collect_coin_creator_fee`.

Each case builds a synthetic quote mint, creator, creator-vault ATA and
destination token account, runs the instruction on
`evidence/original/pump_amm/deployed.so` in LiteSVM (with the captured SPL
Token and Token-2022 programs), and feeds the same bytes to
`programs/pump-amm/recovered/collect_coin_creator_fee_host.rs`. Owners,
lamports and PDA matches are worked out here from the accounts actually
loaded. The error, the committed token balances, the logged event and the
same bytes in the `emit_cpi!` self-call must agree, and token-account
lamports stay put. This is matching behaviour on these inputs only, not a
byte-identity claim.

Base 82-byte mints and base 165-byte token accounts only. A zero-padded tail
is an invalid layout. Token-2022 extensions and native wrapped-SOL accounts
are outside this model.
"""
from pathlib import Path
from functools import cache
from unittest import mock
import base64
import hashlib
import random
import re
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
AMM_ELF = ROOT / 'evidence/original/pump_amm/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/collect_coin_creator_fee_host.rs'
ELF_SHA256 = {
    AMM_ELF: '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
}

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
DISC = bytes([160, 57, 89, 42, 181, 139, 43, 66])
EVENT_DISC = bytes([232, 245, 194, 238, 234, 218, 58, 89])
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
PAYER = Keypair.from_seed(bytes([231]) * 32)
CREATOR = Pubkey.from_bytes(bytes([41]) * 32)
OTHER = Pubkey.from_bytes(bytes([42]) * 32)
MINT = Pubkey.from_bytes(bytes([43]) * 32)
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
STRAY_VAULT = Pubkey.from_bytes(bytes([78]) * 32)
STRAY_EVENT = Pubkey.from_bytes(bytes([79]) * 32)
STRAY_AUTH = Pubkey.from_bytes(bytes([80]) * 32)
NOW = 1_761_800_000
TOKEN_RENT = 2_039_280
TX_FEE = 5000
U64 = 2**64 - 1
PROGRAMS = {'spl': TOKEN, 't22': TOKEN22, 'ata': ATA, 'system': SYSTEM, 'amm': AMM, 'fees': FEES}


def pda(seeds, program):
    return Pubkey.find_program_address(list(seeds), program)[0]


def ata(owner, token_program, mint):
    return pda([bytes(owner), bytes(token_program), bytes(mint)], ATA)


def mint_data(decimals, initialized):
    return (struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([decimals, initialized])
            + struct.pack('<I', 0) + bytes(32))


def token_data(mint, owner, amount, state, delegate=False):
    data = bytearray(165)
    data[0:32] = bytes(mint)
    data[32:64] = bytes(owner)
    data[64:72] = struct.pack('<Q', amount)
    data[108] = state
    if delegate:
        data[72:76] = struct.pack('<I', 1)
        data[76:108] = bytes(OTHER)
        data[121:129] = struct.pack('<Q', 1)
    return data


def sized(data, n):
    if n is None:
        return bytes(data)
    data = bytes(data)
    if n <= len(data):
        return data[:n]
    return data + bytes(n - len(data))


def creator_of(c):
    return OTHER if c.get('creator') == 'other' else c.get('creator', CREATOR)


def program_of(c):
    return PROGRAMS.get(c.get('token_prog', 'spl'), TOKEN)


def owner_pubkey(c, field):
    name = c.get(field)
    if name is None:
        prog = c.get('token_prog', 'spl')
        return TOKEN22 if prog == 't22' else TOKEN
    return PROGRAMS[name]


def build(c):
    """Return `(metas, accounts, payload, keys)` for one case."""
    creator = creator_of(c)
    mint = c.get('mint_key', MINT)
    token_program = program_of(c)
    authority = pda([b'creator_vault', bytes(creator)], AMM) if c.get('authority_ok', True) else STRAY_AUTH
    vault = ata(authority, token_program, mint) if c.get('vault_ata_ok', True) else STRAY_VAULT
    if c.get('same_account'):
        dest = vault
    elif c.get('dest') == 'stray':
        dest = STRAY
    else:
        dest = ata(creator, token_program, mint)
    event = EVENT_AUTHORITY if c.get('event_ok', True) else STRAY_EVENT
    program = {'stray': STRAY, 'token': TOKEN}.get(c.get('program'), AMM)
    mint_field = OTHER if c.get('vault_mint') == 'other' else mint
    vault_field = creator if c.get('vault_field_owner') == 'creator' else OTHER if c.get('vault_field_owner') == 'other' else authority
    dest_mint = OTHER if c.get('dest_mint') == 'other' else mint
    dest_field = authority if c.get('dest_field_owner') == 'authority' else OTHER if c.get('dest_field_owner') == 'other' else creator
    accounts = {}
    if not c.get('omit_mint'):
        raw = mint_data(c.get('decimals', 6), c.get('mint_init', 1))
        accounts[mint] = Account(c.get('mint_lamports', 10**9), sized(raw, c.get('mint_len')), owner_pubkey(c, 'mint_owner'))
    if not c.get('omit_creator'):
        accounts[creator] = Account(c.get('creator_lamports', 10**9), c.get('creator_data', b'\x01'),
                                    PROGRAMS[c.get('creator_owner', 'system')])
    vault_raw = token_data(mint_field, vault_field, c.get('amount', 1000), c.get('vault_state', 1), c.get('delegate', False))
    if not c.get('omit_vault'):
        accounts[vault] = Account(c.get('vault_lamports', TOKEN_RENT), sized(vault_raw, c.get('vault_len')),
                                  owner_pubkey(c, 'vault_owner'))
    if dest != vault and not c.get('omit_dest'):
        dest_raw = token_data(dest_mint, dest_field, c.get('dest_amount', 0), c.get('dest_state', 1))
        accounts[dest] = Account(c.get('dest_lamports', TOKEN_RENT), sized(dest_raw, c.get('dest_len')),
                                 owner_pubkey(c, 'dest_owner'))
    metas = [AccountMeta(mint, False, False), AccountMeta(token_program, False, False),
             AccountMeta(creator, False, False), AccountMeta(authority, False, False),
             AccountMeta(vault, False, c.get('vault_writable', True)),
             AccountMeta(dest, False, c.get('dest_writable', True)),
             AccountMeta(event, False, False), AccountMeta(program, False, False)]
    metas += [AccountMeta(Pubkey.from_bytes(bytes([90 + i]) * 32), False, False) for i in range(c.get('extra', 0))]
    if 'count' in c:
        metas = metas[:c['count']]
    payload = c['data'] if 'data' in c else DISC + c.get('trailing', b'')
    payload = payload[:c['payload_len']] if 'payload_len' in c else payload
    keys = {'creator': creator, 'authority': authority, 'vault': vault, 'dest': dest, 'mint': mint,
            'token_program': token_program, 'event': event, 'program': program}
    return metas, accounts, payload, keys


def owner_code(owner):
    if owner == TOKEN:
        return '1'
    if owner == TOKEN22:
        return '2'
    return '0'


def token_code(key):
    if key == TOKEN:
        return '1'
    if key == TOKEN22:
        return '2'
    return '0'


def host_line(c):
    metas, accounts, payload, keys = build(c)

    def facts(key):
        account = accounts.get(key)
        if account is None:
            return '0', '0', ''
        return owner_code(account.owner), str(account.lamports), bytes(account.data).hex()

    def bit(ok):
        return '1' if ok else '0'

    mint_owner, mint_lamports, mint_hex = facts(keys['mint'])
    creator_account = accounts.get(keys['creator'])
    creator_fees = bit(creator_account is not None and creator_account.owner == FEES)
    creator_lamports = '0' if creator_account is None else str(creator_account.lamports)
    vault_owner, vault_lamports, vault_hex = facts(keys['vault'])
    dest_owner, dest_lamports, dest_hex = facts(keys['dest'])
    token_program = metas[1].pubkey if len(metas) > 1 else keys['token_program']
    authority = metas[3].pubkey if len(metas) > 3 else keys['authority']
    vault = metas[4].pubkey if len(metas) > 4 else keys['vault']
    dest = metas[5].pubkey if len(metas) > 5 else keys['dest']
    event = metas[6].pubkey if len(metas) > 6 else keys['event']
    program = metas[7].pubkey if len(metas) > 7 else keys['program']
    mint = metas[0].pubkey if metas else keys['mint']
    creator = metas[2].pubkey if len(metas) > 2 else keys['creator']
    fields = [
        payload.hex(), str(len(metas)), token_code(token_program), mint_owner, mint_lamports, mint_hex,
        creator_fees, creator_lamports,
        bit(len(metas) > 3 and authority == pda([b'creator_vault', bytes(creator)], AMM)),
        bit(len(metas) > 4 and metas[4].is_writable),
        vault_owner, vault_lamports,
        bit(len(metas) > 4 and vault == ata(authority, token_program, mint)),
        vault_hex,
        bit(len(metas) > 5 and metas[5].is_writable),
        dest_owner, dest_lamports, dest_hex,
        bit(len(metas) > 6 and event == EVENT_AUTHORITY),
        bit(len(metas) > 7 and program == AMM),
        bytes(creator).hex(), bytes(authority).hex(), bytes(vault).hex(), bytes(dest).hex(), bytes(mint).hex(),
        str(NOW),
    ]
    return ','.join(fields)


@cache
def image(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ELF_SHA256[path]:
        raise ValueError('captured program hash mismatch')
    return raw


def run_captured(c):
    metas, accounts, payload, keys = build(c)
    vm = LiteSVM().with_sigverify(False).with_transaction_history(0)
    vm.add_program(AMM, image(AMM_ELF))
    vm.add_program(TOKEN, image(TOKEN_ELF))
    vm.add_program(TOKEN22, image(TOKEN22_ELF))
    vm.set_clock(Clock(100, NOW, 0, 0, NOW))
    vm.airdrop(PAYER.pubkey(), 10**10)
    for key, account in accounts.items():
        vm.set_account(key, account)
    def live(key):
        # A zero-lamport write does not survive in the VM: the program sees no account.
        account = vm.get_account(key)
        if account is None:
            return b'', 0, None
        return bytes(account.data), account.lamports, account.owner

    before = {}
    lamports = {}
    owners = {}
    for key in accounts:
        data, balance, owner = live(key)
        before[key] = data
        lamports[key] = balance
        owners[key] = owner
    pay_before = vm.get_account(PAYER.pubkey()).lamports
    tx = Transaction.new_signed_with_payer([Instruction(AMM, payload, metas)], PAYER.pubkey(), [PAYER],
                                           vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = [base64.b64decode(line[len('Program data: '):]) for line in meta.logs() if line.startswith('Program data: ')]
    token_ix = 0
    event_cpi = []
    for group in meta.inner_instructions():
        for ix in group:
            raw = bytes(ix.instruction().data)
            if raw.startswith(EVENT_CPI_TAG):
                event_cpi.append(raw)
            else:
                token_ix += 1
    after = {}
    lamports_held = True
    for key in accounts:
        data, balance, owner = live(key)
        after[key] = data
        if balance != lamports[key] or owner != owners[key]:
            lamports_held = False
    out = {'events': events, 'event_cpi': event_cpi, 'token_ix': token_ix, 'before': before, 'after': after,
           'lamports_held': lamports_held, 'payer': vm.get_account(PAYER.pubkey()).lamports - pay_before,
           'idle_log': any('No coin creator fee to collect' in line for line in meta.logs()),
           'vault': keys['vault'], 'dest': keys['dest']}
    if failed:
        text = str(result.err())
        custom = re.search(r'Custom\((\d+)\)', text)
        if custom:
            out['error'] = int(custom.group(1))
        elif 'InsufficientFundsForRent' in text:
            out['error'] = 'InsufficientFundsForRent'
        else:
            field = re.search(r'Fieldless\((\w+)\)', text)
            out['error'] = field.group(1) if field else text
        return out
    out['error'] = None
    return out


def patch_amount(data, amount):
    raw = bytearray(data)
    raw[64:72] = struct.pack('<Q', amount)
    return bytes(raw)


def fixed_cases():
    cases = []
    add = cases.append
    for amount in (0, 1, 1000, 10**12, U64):
        add({'amount': amount})
    for dest_amount in (1, 7, U64, U64 - 1000):
        add({'dest_amount': dest_amount})
    add({'amount': 5, 'dest_amount': U64 - 3})
    for decimals in (0, 9, 255):
        add({'decimals': decimals})
    add({'token_prog': 't22'})
    add({'token_prog': 't22', 'amount': 42, 'dest_amount': 8})
    add({'token_prog': 't22', 'amount': 1, 'dest_amount': U64 - 2})
    add({'token_prog': 't22', 'amount': 1, 'dest_amount': U64})
    add({'token_prog': 't22', 'amount': 5, 'dest_amount': U64, 'vault_state': 2})
    add({'mint_owner': 't22'})
    add({'trailing': b'\xff\x00'})
    add({'extra': 2})
    add({'amount': 0, 'vault_state': 2})
    add({'amount': 0, 'vault_mint': 'other'})
    add({'amount': 0, 'program': 'stray'})
    add({'amount': 0, 'dest_state': 2})
    add({'amount': 0, 'dest_mint': 'other'})
    add({'amount': 0, 'authority_ok': False})
    for n in range(9):
        add({'payload_len': n})
    add({'data': bytes(8)})
    add({'payload_len': 0, 'count': 0})
    for n in range(8):
        add({'count': n})
    add({'count': 1, 'mint_owner': 'system'})
    add({'count': 1, 'mint_len': 10})
    add({'count': 1, 'mint_lamports': 0})
    add({'count': 2, 'token_prog': 'ata'})
    add({'count': 4, 'authority_ok': False})
    add({'count': 5, 'vault_len': 10})
    add({'count': 5, 'vault_owner': 'system'})
    add({'count': 5, 'vault_lamports': 0})
    add({'count': 5, 'vault_ata_ok': False})
    add({'count': 6, 'dest_len': 4})
    add({'count': 6, 'dest_mint': 'other'})
    add({'count': 7, 'event_ok': False})
    for n in (0, 81, 82, 200):
        add({'mint_len': n})
    for init in (0, 2, 255):
        add({'mint_init': init})
    add({'mint_lamports': 0})
    add({'mint_lamports': 1})
    add({'mint_owner': 'system'})
    add({'mint_owner': 'amm'})
    add({'omit_mint': True})
    add({'token_prog': 'ata'})
    add({'token_prog': 'system'})
    add({'authority_ok': False})
    add({'authority_ok': False, 'vault_writable': False})
    add({'authority_ok': False, 'vault_len': 10})
    add({'vault_ata_ok': False})
    add({'vault_field_owner': 'other'})
    add({'vault_field_owner': 'other', 'vault_ata_ok': False})
    add({'vault_writable': False})
    add({'vault_writable': False, 'vault_field_owner': 'other'})
    add({'vault_writable': False, 'vault_ata_ok': False})
    add({'token_prog': 'spl', 'vault_owner': 't22'})
    add({'token_prog': 'spl', 'vault_owner': 't22', 'vault_writable': False})
    add({'token_prog': 'spl', 'vault_owner': 't22', 'vault_ata_ok': False})
    add({'vault_owner': 'system'})
    add({'vault_owner': 'amm'})
    add({'vault_owner': 'system', 'vault_writable': False})
    add({'vault_lamports': 0})
    add({'vault_lamports': 1, 'amount': 20})
    add({'omit_vault': True})
    for state in (0, 2, 3, 255):
        add({'vault_state': state})
    add({'vault_len': 164})
    add({'vault_len': 166, 'amount': 5})
    add({'vault_len': 200, 'amount': 5})
    add({'vault_mint': 'other'})
    add({'vault_mint': 'other', 'vault_state': 2})
    add({'vault_state': 2, 'dest_state': 2})
    add({'dest_writable': False})
    add({'dest_writable': False, 'dest_field_owner': 'other'})
    add({'dest_writable': False, 'dest_mint': 'other'})
    add({'dest_field_owner': 'other'})
    add({'dest_mint': 'other'})
    add({'dest_field_owner': 'other', 'dest_mint': 'other'})
    add({'token_prog': 'spl', 'dest_owner': 't22'})
    add({'token_prog': 'spl', 'dest_owner': 't22', 'dest_mint': 'other'})
    add({'token_prog': 'spl', 'dest_owner': 't22', 'dest_field_owner': 'other'})
    add({'dest_owner': 'system'})
    add({'dest_lamports': 0})
    add({'omit_dest': True})
    for state in (0, 2, 3):
        add({'dest_state': state})
    add({'dest_len': 164})
    add({'dest': 'stray', 'amount': 9, 'dest_amount': 4})
    add({'same_account': True})
    add({'event_ok': False})
    add({'event_ok': False, 'creator_owner': 'fees'})
    add({'program': 'stray', 'amount': 9})
    add({'program': 'token', 'amount': 8})
    add({'program': 'stray', 'vault_state': 2})
    add({'creator_owner': 'fees'})
    add({'creator_owner': 'fees', 'amount': 0})
    add({'creator_owner': 'fees', 'creator_lamports': 0})
    add({'creator_owner': 'fees', 'creator_lamports': 1})
    add({'creator_owner': 'fees', 'vault_writable': False})
    add({'creator_owner': 'amm'})
    add({'creator_owner': 'spl'})
    add({'omit_creator': True})
    add({'creator_lamports': 1, 'amount': 3})
    add({'delegate': True, 'amount': 40})
    add({'creator': 'other', 'amount': 12})
    add({'creator': 'other', 'creator_owner': 'fees', 'amount': 6})
    return cases


def random_cases(count=48, seed=20261030):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        c = {'token_prog': rng.choice(('spl', 'spl', 't22')),
             'amount': rng.choice((0, 1, rng.randint(2, 10**9), U64)),
             'dest_amount': rng.choice((0, rng.randint(0, 10**6), U64, U64 - 2))}
        if rng.random() < 0.12:
            c['vault_state'] = rng.choice((0, 1, 2, 3))
        if rng.random() < 0.12:
            c['dest_state'] = rng.choice((0, 1, 2, 3))
        if rng.random() < 0.08:
            c['count'] = rng.randint(0, 7)
        if rng.random() < 0.06:
            c['payload_len'] = rng.randint(0, 8)
        if rng.random() < 0.05:
            c['authority_ok'] = False
        if rng.random() < 0.05:
            c['vault_ata_ok'] = False
        if rng.random() < 0.05:
            c['event_ok'] = False
        if rng.random() < 0.05:
            c['program'] = rng.choice(('stray', 'token'))
        if rng.random() < 0.05:
            c['vault_writable'] = False
        if rng.random() < 0.05:
            c['dest_writable'] = False
        if rng.random() < 0.06:
            c['creator_owner'] = 'fees'
        if rng.random() < 0.05:
            c['vault_owner'] = rng.choice(('system', 't22', 'spl', 'amm'))
        if rng.random() < 0.05:
            c['dest_owner'] = rng.choice(('system', 't22', 'spl'))
        if rng.random() < 0.04:
            c['mint_owner'] = rng.choice(('system', 't22', 'spl', 'amm'))
        if rng.random() < 0.04:
            c['vault_field_owner'] = 'other'
        if rng.random() < 0.04:
            c['dest_field_owner'] = 'other'
        if rng.random() < 0.04:
            c['vault_mint'] = 'other'
        if rng.random() < 0.04:
            c['dest_mint'] = 'other'
        if rng.random() < 0.04:
            c['mint_init'] = rng.choice((0, 1, 2))
        if rng.random() < 0.04:
            c['vault_lamports'] = 0
        if rng.random() < 0.05:
            c['decimals'] = rng.choice((0, 6, 9))
        if rng.random() < 0.06:
            c['creator'] = 'other'
        if rng.random() < 0.04:
            c['delegate'] = True
        cases.append(c)
    return cases


class PumpAmmCollectCoinCreatorFeeCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in ELF_SHA256:
            image(path)
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'collect-coin-creator-fee-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(c) + '\n' for c in cases)
        answers = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        lines = answers.splitlines()
        self.assertEqual(len(lines), len(cases), answers)
        return lines

    def assert_matches(self, answer, captured):
        self.assertTrue(captured['lamports_held'])
        self.assertEqual(captured['payer'], -TX_FEE)
        if answer.startswith('error:'):
            code = answer[6:]
            self.assertEqual(captured['error'], int(code) if code.isdigit() else code)
            self.assertEqual(captured['events'], [])
            self.assertEqual(captured['before'], captured['after'])
            return
        if answer.startswith('event-then:'):
            name, event = answer.split(',', 1)[0][len('event-then:'):], answer.split(',', 1)[1]
            self.assertEqual(name, 'MissingAccount')
            self.assertEqual(captured['error'], 'MissingAccount')
            self.assertEqual(captured['events'], [bytes.fromhex(event)])
            self.assertEqual(captured['before'], captured['after'])
            return
        self.assertIsNone(captured['error'])
        vault, dest = captured['vault'], captured['dest']
        if answer == 'idle':
            self.assertTrue(captured['idle_log'])
            self.assertEqual(captured['events'], [])
            self.assertEqual(captured['event_cpi'], [])
            self.assertEqual(captured['token_ix'], 0)
            self.assertEqual(captured['before'], captured['after'])
            return
        _, vault_amount, dest_amount, event = answer.split(',', 3)
        self.assertFalse(captured['idle_log'])
        self.assertEqual(captured['events'], [bytes.fromhex(event)])
        self.assertEqual(captured['event_cpi'], [EVENT_CPI_TAG + bytes.fromhex(event)])
        self.assertEqual(captured['token_ix'], 1)
        self.assertEqual(bytes.fromhex(event)[:8], EVENT_DISC)
        expected = dict(captured['before'])
        expected[vault] = patch_amount(expected[vault], int(vault_amount))
        expected[dest] = patch_amount(expected[dest], int(dest_amount))
        self.assertEqual(captured['after'], expected)

    def run_cases(self, cases):
        for c, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=repr(c)[:240], host=answer[:80]):
                self.assert_matches(answer, run_captured(c))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_captured_image_identity_is_required(self):
        image.cache_clear()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                wrong = Path(temporary) / 'wrong.so'
                wrong.write_bytes(AMM_ELF.read_bytes() + b'wrong capture')
                with mock.patch.dict(ELF_SHA256, {wrong: ELF_SHA256[AMM_ELF]}):
                    with self.assertRaisesRegex(ValueError, 'captured program hash mismatch'):
                        image(wrong)
        finally:
            image.cache_clear()

    def test_checker_rejects_tampered_outcomes(self):
        samples = ({}, {'amount': 0}, {'token_prog': 't22', 'amount': 1, 'dest_amount': U64},
                   {'program': 'stray', 'amount': 9}, {'vault_state': 0}, {'creator_owner': 'fees'},
                   {'payload_len': 3}, {'vault_mint': 'other'}, {'vault_len': 10})
        flip = lambda h, i: h[:i] + ('0' if h[i] != '0' else '1') + h[i + 1:]
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured)
            with self.assertRaises(AssertionError):
                self.assert_matches(answer, dict(captured, lamports_held=False))
            if answer.startswith('ok,'):
                _, vault_amount, dest_amount, event = answer.split(',', 3)
                tampered = [f'ok,{vault_amount},{int(dest_amount) + 1},{event}',
                            f'ok,{1},{dest_amount},{event}',
                            f'ok,{vault_amount},{dest_amount},{flip(event, 0)}',
                            f'ok,{vault_amount},{dest_amount},{flip(event, 16)}',
                            'idle', 'error:6048']
            elif answer == 'idle':
                tampered = ['ok,0,1,' + (EVENT_DISC + bytes(112)).hex(), 'error:6048', 'error:0']
            elif answer.startswith('event-then:'):
                event = answer.split(',', 1)[1]
                tampered = ['event-then:MissingAccount,' + flip(event, 20), 'error:MissingAccount', 'idle',
                            'event-then:BorshIoError,' + event]
            else:
                tampered = ['error:6048' if answer != 'error:6048' else 'error:2000',
                            'error:InvalidAccountData' if answer != 'error:InvalidAccountData' else 'error:101',
                            'idle']
            for text in tampered:
                with self.subTest(case=repr(c)[:120], tampered=text[:70]):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a for a in answers if a.startswith('error:')}, {
            'error:101', 'error:2000', 'error:2006', 'error:2009', 'error:2014', 'error:2015', 'error:2021',
            'error:2023', 'error:3005', 'error:3007', 'error:3008', 'error:3012', 'error:6048', 'error:3',
            'error:14', 'error:17', 'error:InvalidAccountData', 'error:UninitializedAccount'})
        self.assertTrue(any(a.startswith('event-then:MissingAccount,') for a in answers))
        self.assertGreater(sum(a == 'idle' for a in answers), 3)
        self.assertGreater(sum(a.startswith('ok,') for a in answers), 15)
        events = {bytes.fromhex(a.split(',', 3)[3])[:8] for a in answers if a.startswith('ok,')}
        self.assertEqual(events, {EVENT_DISC})


if __name__ == '__main__':
    unittest.main()
