"""Captured-program checks for Pump `migrate_v2` on Token-2022 quote mints.

Every case runs `migrate_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token,
Token-2022 and Associated Token programs and the no-op pump_amm of
`tests/test_migrate_v2_captured.py`, on a curve whose quote mint has Token-2022
extensions. The same inputs go to
`programs/pump/recovered/migrate_v2_token2022_host.rs`, and the error, the
`create_pool` and `init_boost` CPIs, the CompletePumpAmmMigrationEvent, the quote
tokens moved and withheld, the tokens harvested to the mint, the quote accounts
afterwards and the curve must agree. The no-op pump_amm never takes the quote,
so the pool authority's quote account can only close when it holds no tokens.
This shows matching behavior on these inputs only; it is not a byte-identity
claim.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_migrate_v2_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = base.PUMP_ELF
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/migrate_v2_token2022_host.rs'

PUMP, PUMP_AMM, TOKEN, TOKEN22, ATA = base.PUMP, base.PUMP_AMM, base.TOKEN, base.TOKEN22, base.ATA
QUOTE, MINT, CURVE, SYSTEM = base.QUOTE, base.MINT, base.CURVE, base.SYSTEM
USER = Keypair.from_seed(bytes([232]) * 32)
TS = base.TS
U64 = base.U64
PROGRAMS = {'t22': TOKEN22, 'spl': TOKEN}
FEE_250 = (0, 0, 0, 250, 10**18)
FEE_ALL = (0, 0, 0, 10_000, U64)
# Mint extension type -> body, for the kinds that do not change a transfer here.
EXTENSIONS = {3: bytes(32), 4: bytes(65), 12: bytes(32), 16: bytes(64), 18: bytes(64), 20: bytes(64), 10: bytes(52)}


def rent(size):
    return (128 + size) * 6960


def tlv(kind, body=b''):
    return struct.pack('<HH', kind, len(body)) + body


def mint_data(item):
    head = base.mint_data()
    if item['malformed'] == 'short':
        return head.ljust(165, b'\0') + bytes([1])
    ext = b''
    if item['tfee']:
        older_bps, older_max, newer_epoch, newer_bps, newer_max = item['tfee']
        ext += tlv(1, bytes(64) + struct.pack('<QQQH', item['mint_withheld'], 0, older_max, older_bps)
                   + struct.pack('<QQH', newer_epoch, newer_max, newer_bps))
    if item['hook_set']:
        ext += tlv(14, bytes(32) + bytes([7]) * 32)
    if item['paused']:
        ext += tlv(26, bytes(32) + b'\1')
    if item['mint_non_transferable']:
        ext += tlv(9)
    for kind in item['extra_ext']:
        ext += tlv(kind, EXTENSIONS[kind])
    if item['malformed'] == 'extensions':
        ext += tlv(99)
    if item['malformed'] == 'padding':
        return head.ljust(100, b'\0') + b'\1' + bytes(64) + bytes([1]) + (ext or tlv(3, bytes(32)))
    return head.ljust(165, b'\0') + bytes([1]) + ext if ext else head


HOLDING = dict(balance=0, frozen=False, fee_extension=None, memo=False, cpi_guard=False, non_transferable=False,
               hook_extension=False)


def holding(**changes):
    return dict(HOLDING, **changes)


def token_data(mint, owner, held, fallback_fee_extension):
    fee_extension = fallback_fee_extension if held['fee_extension'] is None else held['fee_extension']
    data = (bytes(mint) + bytes(owner) + struct.pack('<Q', held['balance']) + struct.pack('<I', 0) + bytes(32)
            + bytes([2 if held['frozen'] else 1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))
    ext = b''
    if fee_extension:
        ext += tlv(2, bytes(8))
    if held['memo']:
        ext += tlv(8, b'\1')
    if held['cpi_guard']:
        ext += tlv(11, b'\1')
    if held['non_transferable']:
        ext += tlv(13)
    if held['hook_extension']:
        ext += tlv(15, b'\0')
    return data + bytes([2]) + ext if ext else data


DEFAULTS = dict(program='t22', mint_owner='t22', tfee=None, mint_withheld=0, epoch=0, hook_set=False, paused=False,
                mint_non_transferable=False, extra_ext=(), malformed=None, mint_writable=False, vault_held=None, pa=None)


def case(**changes):
    extra = {k: changes.pop(k) for k in list(changes) if k in DEFAULTS}
    item = dict(base.case(quote='spl', **changes), **DEFAULTS)
    item.update(extra)
    if item['vault_held'] is None:
        item['vault_held'] = holding()
    item['vault_held'] = dict(item['vault_held'], balance=item['vault'])
    if item['pa'] is None:
        item['pa'] = holding()
    return item


def named(item):
    acc = dict(base.accounts(QUOTE))
    program = PROGRAMS[item['program']]
    pool = acc['pool']
    acc.update(associated_quote_bonding_curve=base.ata(CURVE, QUOTE, program),
               pool_authority_quote_account=base.ata(base.POOL_AUTHORITY, QUOTE, program),
               pool_quote_token_account=base.ata(pool, QUOTE, program), quote_token_program=program, user=USER.pubkey())
    return acc


def error_name(text):
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    for name in ('BorshIoError', 'ArithmeticOverflow', 'InsufficientFundsForRent'):
        if name in text:
            return name
    name = re.search(r'Fieldless\((\w+)\)', text)
    return name.group(1) if name else text


def withheld_of(data):
    offset = 166
    while offset + 4 <= len(data):
        kind, length = struct.unpack_from('<HH', data, offset)
        if kind == 0:
            break
        if kind == 2:
            return struct.unpack_from('<Q', data, offset + 4)[0]
        offset += 4 + length
    return 0


def mint_withheld_of(data):
    return struct.unpack_from('<Q', data, 166 + 4 + 64)[0] if len(data) > 170 and data[166] == 1 else 0


class Chain:
    """One VM for every case: reloading the ELFs costs far more than a transaction."""

    def __init__(self):
        self.vm = vm = LiteSVM().with_transaction_history(0)
        programdata = base.pda([bytes(PUMP)], base.UPGRADEABLE)
        vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + PUMP_ELF.read_bytes(),
                                            base.UPGRADEABLE, False))
        vm.set_account(PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), base.UPGRADEABLE, True))
        vm.add_program(PUMP_AMM, base.noop_program())
        for key, path in ((TOKEN, TOKEN_ELF), (TOKEN22, TOKEN22_ELF), (ATA, ATA_ELF)):
            vm.add_program_from_file(key, path)
        self.stale = set()
        self.slot = 1000

    def run(self, item):
        vm = self.vm
        self.slot += 1
        vm.set_clock(Clock(self.slot, 0, item['epoch'], 0, TS))
        for key in self.stale:
            vm.set_account(key, Account(0, b'', SYSTEM))
        acc = named(item)
        program = PROGRAMS[item['program']]
        state = {base.GLOBAL: (10**9, PUMP, base.global_data(item['fee'])), USER.pubkey(): (10**12, SYSTEM, b''),
                 base.WITHDRAW: (1_000_000, SYSTEM, b''), MINT: (1_461_600, TOKEN, base.mint_data()),
                 QUOTE: (10**10, PROGRAMS[item['mint_owner']], mint_data(item)),
                 CURVE: (base.curve_lamports(item), PUMP, base.curve_data(item)),
                 acc['associated_base_bonding_curve']: (2_039_280, TOKEN, base.token_data(MINT, CURVE, 0)),
                 acc['lp_mint']: (1_461_600, TOKEN22, base.mint_data(9, 0)),
                 acc['user_pool_token_account']: (2_074_080, TOKEN22, base.token_data(acc['lp_mint'], base.POOL_AUTHORITY, 0)),
                 acc['associated_quote_bonding_curve']: (10**8, program, token_data(QUOTE, CURVE, item['vault_held'], bool(item['tfee'])))}
        if item['pa'] != 'missing':
            state[acc['pool_authority_quote_account']] = (10**8, program, token_data(QUOTE, base.POOL_AUTHORITY, item['pa'], bool(item['tfee'])))
        if item['config'] is not None:
            state[base.AMM_CONFIG] = (10**7, PUMP_AMM, base.config_data(item['config']))
        for key, (lamports, owner, data) in state.items():
            vm.set_account(key, Account(lamports, data, owner))
        self.stale = ({k for k in state if k != USER.pubkey()} | {acc[n] for n in (
            'pool_authority', 'pool_base_token_account', 'pool_quote_token_account', 'pool_authority_mint_account',
            'pool_authority_quote_account')})
        metas = [AccountMeta(acc[a['name']], a.get('signer', False),
                             a.get('writable', False) or (a['name'] == 'quote_mint' and item['mint_writable']))
                 for a in base.MIGRATE['accounts']]
        metas += [AccountMeta(key, False, True) for key in base.BOOST[:item['remaining']]]
        tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), Instruction(PUMP, bytes(base.MIGRATE['discriminator']), metas)],
            USER.pubkey(), [USER], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        cpis = []
        for group in json.loads(meta.to_json())['inner_instructions'] or []:
            for inner in group:
                data = bytes(inner['instruction']['data'][1:])
                if data[:8] in (base.AMM_IX['create_pool'], base.AMM_IX['init_boost']):
                    cpis.append(data)

        def data(key):
            account = vm.get_account(key)
            return bytes(account.data) if account else b''

        def tokens(key):
            raw = data(key)
            return struct.unpack_from('<Q', raw, 64)[0] if len(raw) >= 72 else 0

        if failed:
            if any('panicked' in line for line in meta.logs()):
                return {'error': 'panic', 'cpis': cpis, 'logs': meta.logs()}
            return {'error': error_name(str(result.err())), 'cpis': cpis, 'logs': meta.logs()}
        pa = data(acc['pool_authority_quote_account'])
        curve = vm.get_account(CURVE)
        return {'error': None, 'cpis': cpis, 'logs': meta.logs(),
                'events': [base64.b64decode(line[14:]) for line in meta.logs() if line.startswith('Program data: ')],
                'curve': (curve.lamports, bytes(curve.data)) if curve is not None else None,
                'vault': tokens(acc['associated_quote_bonding_curve']), 'pa_tokens': tokens(acc['pool_authority_quote_account']),
                'pa_withheld': withheld_of(pa), 'pa_len': len(pa), 'pool_quote_len': len(data(acc['pool_quote_token_account'])),
                'mint_withheld': mint_withheld_of(data(QUOTE))}


def host_held(item, held):
    if held == 'missing':
        return held
    fee_extension = bool(item['tfee']) if held['fee_extension'] is None else held['fee_extension']
    return ':'.join(str(int(v)) for v in (held['frozen'], fee_extension, held['memo'], held['cpi_guard'],
                                          held['non_transferable'], held['hook_extension']))


def host_line(item):
    fee = ':'.join(str(v) for v in item['tfee']) if item['tfee'] else '-'
    fields = [base.host_line(item), item['program'], item['mint_owner'], int(item['malformed'] in ('padding', 'short')),
              int(item['malformed'] == 'extensions'), fee, item['epoch'],
              int(item['hook_set']), int(item['paused']), int(item['mint_non_transferable']), int(item['mint_writable']),
              host_held(item, item['vault_held']), host_held(item, item['pa'])]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    zero_quote = dict(rqr=0, vqr=1)
    boost = dict(config=(949, 1, 1), remaining=2)
    for tfee in (None, FEE_250, FEE_ALL):
        add(tfee=tfee)
        add(tfee=tfee, pcqi=1_234_567)
        add(tfee=tfee, **boost)
        add(tfee=tfee, config=(949, 1, 1))
        add(tfee=tfee, config=(949, 1, 1), remaining=3)
        add(tfee=tfee, config=(949, 1, 1), remaining=1, pa='missing')
        add(tfee=tfee, mayhem=1, config=(949, 1, 1))
        add(tfee=tfee, mint_owner='spl')
        add(tfee=tfee, mint_owner='spl', rqr=U64, pcqi=1)
        add(tfee=tfee, mint_owner='spl', complete=0)
        add(tfee=tfee, mint_owner='spl', vtr=0, vqr=0, rtr=0, rqr=0)
        add(tfee=tfee, complete=0)
        add(tfee=tfee, complete=2)
        add(tfee=tfee, vtr=0, vqr=0, rtr=0, rqr=0)
        add(tfee=tfee, vtr=0, vqr=0, rtr=0, rqr=0, pa='missing', vault_held=holding(frozen=True))
        add(tfee=tfee, rqr=U64, pcqi=1)
        add(tfee=tfee, rqr=U64, pcqi=1, vault_held=holding(frozen=True))
        add(tfee=tfee, rqr=5)
        add(tfee=tfee, rqr=5, vault=4)
        add(tfee=tfee, rqr=5, vault=9)
        add(tfee=tfee, rqr=0, pcqi=3, vqr=1)
        add(tfee=tfee, rqr=2, pcqi=3, vault=4)
        add(tfee=tfee, rqr=U64 - 5, pcqi=5, vault=U64)
        # A pool authority quote account created here is closed: nothing left, a writable fee mint.
        for writable in (False, True):
            add(tfee=tfee, pa='missing', mint_writable=writable)
            add(tfee=tfee, pa='missing', mint_writable=writable, **zero_quote)
            add(tfee=tfee, pa='missing', mint_writable=writable, **zero_quote, **boost)
            add(tfee=tfee, pa='missing', mint_writable=writable, **boost)
            add(tfee=tfee, pa='missing', mint_writable=writable, mint_withheld=77)
            add(tfee=tfee, pa='missing', mint_writable=writable, malformed='extensions', **boost)
            add(tfee=tfee, mint_writable=writable)
        add(tfee=tfee, pa='missing', vault_held=holding(frozen=True))
        add(tfee=tfee, pa='missing', paused=True)
        add(tfee=tfee, pa='missing', paused=True, **zero_quote)
        add(tfee=tfee, pa='missing', hook_set=True)
        add(tfee=tfee, pa='missing', hook_set=True, vault_held=holding(hook_extension=True))
        add(tfee=tfee, hook_set=True, vault_held=holding(hook_extension=True))
        add(tfee=tfee, hook_set=True, pa=holding(hook_extension=True))
        add(tfee=tfee, hook_set=True, vault_held=holding(hook_extension=True), pa=holding(hook_extension=True))
        add(tfee=tfee, pa='missing', hook_set=True, **zero_quote, mint_writable=True)
        add(tfee=tfee, pa='missing', mint_non_transferable=True, mint_writable=True)
        add(tfee=tfee, pa='missing', mint_non_transferable=True, mint_writable=True, **zero_quote)
        add(tfee=tfee, pa='missing', mint_non_transferable=True, vault_held=holding(non_transferable=True))
        # Mint shapes on the boost path.
        for malformed in ('padding', 'short', 'extensions'):
            add(tfee=tfee, malformed=malformed)
            add(tfee=tfee, malformed=malformed, complete=0)
            add(tfee=tfee, malformed=malformed, complete=2)
            add(tfee=tfee, malformed=malformed, vtr=0, vqr=0, rtr=0, rqr=0)
            add(tfee=tfee, malformed=malformed, rqr=U64, pcqi=1)
            add(tfee=tfee, malformed=malformed, mint_owner='spl')
            add(tfee=tfee, malformed=malformed, **boost)
            add(tfee=tfee, malformed=malformed, **boost, **zero_quote)
            add(tfee=tfee, malformed=malformed, **boost, mayhem=1)
            add(tfee=tfee, malformed=malformed, **boost, vault_held=holding(frozen=True))
            add(tfee=tfee, malformed=malformed, config=(949, 1, 1))
            add(tfee=tfee, malformed=malformed, remaining=3)
        for kind in sorted(EXTENSIONS):
            add(tfee=tfee, extra_ext=(kind,))
            add(tfee=tfee, extra_ext=(kind,), **boost)
    add(program='spl', mint_owner='spl')
    add(program='spl', mint_owner='t22')
    add(program='spl', mint_owner='t22', rqr=U64, pcqi=1)
    add(program='spl', mint_owner='spl', pa='missing', **zero_quote)
    add(program='spl', mint_owner='spl', **boost)
    # Transfer fee: schedule choice, rounding, cap, whole amount.
    for tfee, epoch in ((FEE_250, 0), ((0, 0, 0, 250, 100), 0), ((100, 10**18, 5, 250, 10**18), 4),
                        ((100, 10**18, 5, 250, 10**18), 5), ((100, 10**18, 5, 250, 10**18), 6), ((100, 17, 5, 250, 10**18), 1),
                        ((0, 0, 0, 0, 10**18), 0), ((0, 0, 0, 250, 0), 0), ((0, 0, 3, 10_000, U64), 2), ((0, 0, 3, 10_000, U64), 3)):
        add(tfee=tfee, epoch=epoch)
        add(tfee=tfee, epoch=epoch, pa='missing', mint_writable=True)
        add(tfee=tfee, epoch=epoch, rqr=U64 - 5, pcqi=5, vault=U64)
    for amount in (1, 39, 40, 41, 79, 80, 81, 400, 401, 10**9):
        add(tfee=FEE_250, rqr=amount)
        add(tfee=FEE_250, rqr=amount, pa=holding(fee_extension=False))
        add(tfee=FEE_ALL, rqr=amount, pa='missing', mint_writable=True)
    add(tfee=(0, 0, 0, 0, 10**18), pa=holding(fee_extension=False))
    add(tfee=(0, 0, 0, 250, 0), pa=holding(fee_extension=False))
    add(tfee=FEE_250, vault_held=holding(fee_extension=False))
    # Rent top-up and flags reach the same way as on an SPL quote.
    add(slack=0)
    add(slack=146_239)
    add(cashback=1, cfb=123, can_edit=1, holder=1, tfee=FEE_250)
    # Order of the token checks, pair by pair.
    faults = {
        'frozen': dict(vault_held=dict(frozen=True)), 'short': dict(vault=5),
        'non_transferable': dict(vault_held=dict(non_transferable=True)), 'paused': dict(paused=True),
        'cpi_guard': dict(vault_held=dict(cpi_guard=True)), 'destination_frozen': dict(pa=dict(frozen=True)),
        'memo': dict(pa=dict(memo=True)), 'no_fee_extension': dict(tfee=FEE_250, pa=dict(fee_extension=False)),
        'hook': dict(hook_set=True), 'marked': dict(hook_set=True, vault_held=dict(hook_extension=True), pa=dict(hook_extension=True)),
        'mint_program': dict(mint_owner='spl'), 'overflow': dict(rqr=U64, pcqi=1), 'not_complete': dict(complete=0),
        'no_boost_accounts': dict(config=(949, 1, 1)),
    }
    names = list(faults)
    for i, left in enumerate(names):
        cases.append(with_faults(faults[left]))
        for right in names[i + 1:]:
            cases.append(with_faults(faults[left], faults[right]))
    return cases


def with_faults(*faults):
    merged = dict(vault_held={}, pa={})
    extra = {}
    for fault in faults:
        for key, value in fault.items():
            if key in merged and isinstance(value, dict):
                merged[key] = dict(merged[key], **value)
            else:
                extra[key] = value
    return case(vault_held=holding(**merged['vault_held']), pa=holding(**merged['pa']), **extra)


def random_cases(count=300, seed=2331):
    rng = random.Random(seed)
    cases = []

    def tfee():
        if rng.random() < 0.3:
            return None
        return (rng.randrange(0, 10_001), rng.choice((0, rng.randrange(0, 10**6), U64)), rng.randrange(0, 8),
                rng.choice((10_000, rng.randrange(0, 10_001))), rng.choice((0, rng.randrange(0, 10**6), U64)))

    def held():
        flag = lambda p: rng.random() < p
        return holding(frozen=flag(0.05), fee_extension=None if flag(0.9) else flag(0.5), memo=flag(0.05), cpi_guard=flag(0.05),
                       non_transferable=flag(0.05), hook_extension=flag(0.3))

    for _ in range(count):
        rqr = rng.choice((0, rng.randrange(1, 10**6), rng.randrange(1, 10**12)))
        pcqi = rng.choice((0, 0, rng.randrange(10**9)))
        cases.append(case(tfee=tfee(), epoch=rng.randrange(0, 8), hook_set=rng.random() < 0.08, paused=rng.random() < 0.08,
                          mint_non_transferable=rng.random() < 0.06, malformed=rng.choice((None,) * 12 + ('padding', 'short', 'extensions')),
                          mint_writable=rng.random() < 0.7, vault_held=held(), pa='missing' if rng.random() < 0.4 else held(),
                          mint_owner=rng.choice(('t22',) * 19 + ('spl',)), rqr=rqr, pcqi=pcqi, vqr=1,
                          vault=rqr + pcqi + rng.choice((0, 0, 1, -1 if rqr + pcqi else 0, rng.randrange(10**6))),
                          complete=rng.choice((1,) * 9 + (0,)), config=rng.choice((None, (949, 1, 1), (949, 1, 0))),
                          remaining=rng.randrange(4), mayhem=int(rng.random() < 0.2), cashback=rng.randrange(2),
                          cfb=rng.randrange(10_001), can_edit=rng.randrange(2), holder=rng.randrange(2),
                          fee=rng.choice((0, rng.randrange(10**10))), slack=rng.choice((2_046_240, rng.randrange(10**10)))))
    return cases


class MigrateV2Token2022CapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'migrate-v2-token2022-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.chain = Chain()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, item, answer, captured):
        if not answer.startswith(('ok,', 'noop,')):
            names = {'borsh': 'BorshIoError', 'arith': 'ArithmeticOverflow', 'rent': 'InsufficientFundsForRent'}
            self.assertEqual(captured['error'], names.get(answer, answer))
            return
        self.assertIsNone(captured['error'])
        if answer.startswith('noop,'):
            self.assertEqual(captured['cpis'], [])
            self.assertEqual(captured['events'], [])
            self.assertEqual(captured['curve'], (int(answer[5:]), base.curve_data(item)))
            return
        boost, lamports, vault, moved, kept, quote, closed, size, harvested = map(int, answer.split(',')[1:])
        create_pool = (base.AMM_IX['create_pool'] + struct.pack('<HQQ', 0, 0, quote) + bytes(base.CREATOR)
                       + struct.pack('<BBQBB', item['mayhem'], item['cashback'], item['cfb'], item['can_edit'], item['holder']))
        self.assertEqual(captured['cpis'], [create_pool] + ([base.AMM_IX['init_boost']] if boost else []))
        after = bytearray(base.curve_data(item))
        struct.pack_into('<QQQQ', after, 8, 0, 0, 0, 0)
        self.assertEqual(captured['curve'], (lamports, bytes(after)) if lamports else None)
        self.assertEqual(captured['vault'], vault)
        self.assertEqual(moved, quote + kept)
        self.assertEqual((captured['pa_tokens'], captured['pa_withheld']), (0, 0) if closed else (quote, kept))
        self.assertEqual(captured['pa_len'] == 0, bool(closed))
        self.assertEqual(captured['pool_quote_len'], size)
        self.assertEqual(captured['mint_withheld'], (item['mint_withheld'] if item['tfee'] else 0) + harvested)
        self.assertEqual(len(captured['events']), 1)
        event = captured['events'][0]
        self.assertEqual(event[:72], base.MIGRATION_EVENT + bytes(USER.pubkey()) + bytes(MINT))
        self.assertEqual(struct.unpack_from('<QQQ', event, 72), (0, quote, item['fee']))
        self.assertEqual(event[-32:], bytes(QUOTE))

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, self.chain.run(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_a_wrong_quote(self):
        item = case(tfee=FEE_ALL, pa='missing', mint_writable=True)
        answer = self.host_answers([item])[0]
        captured = self.chain.run(item)
        self.assert_matches(item, answer, captured)
        self.assertGreater(captured['mint_withheld'], 0)
        for broken in (dict(captured, mint_withheld=captured['mint_withheld'] - 1),
                       dict(captured, vault=captured['vault'] + 1), dict(captured, pool_quote_len=170),
                       dict(captured, pa_len=178), dict(captured, cpis=[])):
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, broken)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {
            'ok', 'noop', 'borsh', 'InvalidAccountData', 'IncorrectProgramId', 'MissingAccount', 'error:1', 'error:11', 'error:13',
            'error:17', 'error:36', 'error:37', 'error:42', 'error:67', 'error:6006', 'error:6024', 'error:6027', 'error:6110',
        })


if __name__ == '__main__':
    unittest.main()
