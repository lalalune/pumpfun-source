"""Captured-program checks for the recovered fee and buyback recipient admission.

Every case runs one Pump trade, or `sweep_protocol_fee`, from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured Pump Fees,
SPL Token, and Associated Token programs, against a synthetic `Global` whose
recipient lists vary by case, on the native (WSOL quote mint) route. The same
keys go to `programs/pump/recovered/trade_recipients_host.rs`, and the error
code and the set of paid recipients must agree. Trade amounts are held fixed:
their arithmetic belongs to the models of each trade. This shows matching
behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import json
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
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
FEES_ELF = ROOT / 'evidence/original/pump_fees/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    FEES_ELF: '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/trade_recipients_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}

USER = Keypair.from_seed(bytes([215]) * 32)
CREATOR = Pubkey.from_bytes(bytes([12]) * 32)
MINT = Pubkey.from_bytes(bytes([15]) * 32)


def pda(*seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)


GLOBAL = pda(b'global')[0]
CURVE = pda(b'bonding-curve', bytes(MINT))[0]
CURVE_V2 = pda(b'bonding-curve-v2', bytes(MINT))[0]
EVENT_AUTHORITY = pda(b'__event_authority')[0]
GLOBAL_VOLUME = pda(b'global_volume_accumulator')[0]
USER_VOLUME = pda(b'user_volume_accumulator', bytes(USER.pubkey()))[0]
FEE_CONFIG, FEE_CONFIG_BUMP = pda(b'fee_config', bytes(PUMP), program=FEES)
SHARING = pda(b'sharing-config', bytes(MINT), program=FEES)[0]
VAULT = pda(b'creator-vault', bytes(CREATOR))[0]

CURVE_RENT = 2_046_960
TOKEN_RENT = 2_039_280
VT, VS, RT, RS, SUPPLY = 1_073_000_000_000_000, 30_000_000_000, 793_100_000_000_000, 10**10, 10**15
ZERO = bytes(32)
# Operation -> (route in the model, amount, limit, trailing bytes).
OPS = {
    'buy': ('trade', 10**9, 10**12, b''),
    'buy_exact_sol_in': ('trade', 10**9, 1, b''),
    'sell': ('trade', 10**12, 0, b''),
    'buy_v2': ('trade', 10**9, 10**12, b''),
    'buy_exact_quote_in_v2': ('trade', 10**9, 1, b''),
    'sell_v2': ('trade', 10**12, 0, b''),
    'buy_v3': ('v3', 10**9, 10**12, b'\0'),
    'buy_exact_quote_in_v3': ('v3', 10**9, 1, b'\0'),
    'sell_v3': ('v3', 10**12, 0, b''),
    'sweep_protocol_fee': ('sweep', None, None, b''),
}
LEGACY = ('buy', 'buy_exact_sol_in', 'sell')


def fill(n):
    return bytes([n]) * 32


MAIN, RESERVED, STRANGER = fill(13), fill(14), fill(99)
FEE_LIST = [fill(n) for n in range(30, 37)]
RESERVED_LIST = [fill(n) for n in range(56, 49, -1)]  # searched linearly
BUYBACK_LIST = [fill(n) for n in range(77, 69, -1)]  # searched linearly
DEFAULTS = dict(op='buy', mayhem=0, fee=MAIN, buyback=BUYBACK_LIST[0], main=MAIN, reserved=RESERVED,
                fee_list=FEE_LIST, reserved_list=RESERVED_LIST, buyback_list=BUYBACK_LIST)


def case(op, **changes):
    return dict(DEFAULTS, op=op, **changes)


def ata(owner, mint=MINT):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]


def mint_data(supply, decimals=6):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(owner, amount):
    return (bytes(MINT) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def global_data(item):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[41:73] = item['main']
    data[97:105] = struct.pack('<Q', SUPPLY)
    for i, key in enumerate(item['fee_list']):
        data[162 + 32 * i:194 + 32 * i] = key
    data[483:515] = item['reserved']
    for i, key in enumerate(item['reserved_list']):
        data[516 + 32 * i:548 + 32 * i] = key
    for i, key in enumerate(item['buyback_list']):
        data[741 + 32 * i:773 + 32 * i] = key
    struct.pack_into('<Q', data, 997, 5_000)
    return bytes(data)


def fee_config_data():
    data = bytearray(ACCOUNT_DISC['FeeConfig']) + bytes([FEE_CONFIG_BUMP]) + bytes(32) + bytes(24)
    data += struct.pack('<I', 1) + (0).to_bytes(16, 'little') + struct.pack('<QQQ', 0, 95, 30)
    data += struct.pack('<I', 0) + bytes(24)
    return bytes(data).ljust(4104, b'\0')


def curve_data(item):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, VT, VS, RT, RS, SUPPLY)
    data[49:81] = bytes(CREATOR)
    data[81] = item['mayhem']
    struct.pack_into('<QQ', data, 125, 0, 7_000_000)
    return bytes(data)


class Captured:
    """One VM for all cases: every account a case reads is rewritten first."""

    def __init__(self):
        vm = self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        vm.add_program_from_file(PUMP, PUMP_ELF)
        vm.add_program_from_file(FEES, FEES_ELF)
        vm.add_program_from_file(TOKEN, TOKEN_ELF)
        vm.add_program_from_file(ATA, ATA_ELF)
        vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))

    def lamports(self, key):
        account = self.vm.get_account(key)
        return account.lamports if account else 0

    def run(self, item):
        vm, op = self.vm, item['op']
        user = USER.pubkey()
        fee, buyback = Pubkey.from_bytes(item['fee']), Pubkey.from_bytes(item['buyback'])
        accounts = {
            user: Account(10**13, b'', SYSTEM),
            GLOBAL: Account(10**9, global_data(item), PUMP),
            MINT: Account(10**9, mint_data(SUPPLY), TOKEN),
            WSOL: Account(10**9, mint_data(0, 9), TOKEN),
            CURVE: Account(CURVE_RENT + RS + 7_000_000, curve_data(item), PUMP),
            ata(CURVE): Account(TOKEN_RENT, token_data(CURVE, RT), TOKEN),
            ata(user): Account(TOKEN_RENT, token_data(user, 10**13), TOKEN),
            FEE_CONFIG: Account(10**9, fee_config_data(), FEES),
            GLOBAL_VOLUME: Account(10**9, ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP),
            CURVE_V2: Account(10**7, b'', SYSTEM),
            # sell_v2 creates this account itself.
            USER_VOLUME: Account(0, b'', SYSTEM) if op == 'sell_v2' else Account(
                10**9, ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(user) + bytes(97), PUMP),
        }
        for key in (fee, buyback):
            if key != SYSTEM:
                accounts[key] = Account(10**9, b'', SYSTEM)
        for key, account in accounts.items():
            vm.set_account(key, account)
        names = {
            'global': GLOBAL, 'base_mint': MINT, 'mint': MINT, 'quote_mint': WSOL, 'base_token_program': TOKEN,
            'quote_token_program': TOKEN, 'token_program': TOKEN, 'associated_token_program': ATA,
            'fee_recipient': fee, 'recipient': fee, 'associated_quote_fee_recipient': ata(fee, WSOL),
            'associated_quote_recipient': ata(fee, WSOL), 'buyback_fee_recipient': buyback,
            'associated_quote_buyback_fee_recipient': ata(buyback, WSOL), 'bonding_curve': CURVE,
            'associated_bonding_curve': ata(CURVE), 'associated_base_bonding_curve': ata(CURVE),
            'associated_quote_bonding_curve': ata(CURVE, WSOL), 'user': user, 'payer': user,
            'associated_user': ata(user), 'associated_base_user': ata(user),
            'associated_quote_user': ata(user, WSOL), 'creator_vault': VAULT,
            'associated_creator_vault': ata(VAULT, WSOL), 'sharing_config': SHARING,
            'global_volume_accumulator': GLOBAL_VOLUME, 'user_volume_accumulator': USER_VOLUME,
            'associated_user_volume_accumulator': ata(USER_VOLUME, WSOL), 'fee_config': FEE_CONFIG,
            'fee_program': FEES, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
        }
        ix = IX[op]
        metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
        if op in LEGACY:
            metas += [AccountMeta(CURVE_V2, False, False), AccountMeta(buyback, False, True)]
        _, amount, limit, trailing = OPS[op]
        data = bytes(ix['discriminator'])
        if amount is not None:
            data += struct.pack('<QQ', amount, limit) + trailing
        vm.expire_blockhash()
        before = self.lamports(fee), self.lamports(buyback)
        tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], user, [USER], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            return {'error': int(code.group(1)) if code else text}
        # The same key in both roles counts once, as the fee recipient.
        return {'error': None, 'fee': self.lamports(fee) - before[0],
                'buyback': 0 if buyback == fee else self.lamports(buyback) - before[1]}


def host_line(item):
    keys = lambda items: ';'.join(key.hex() for key in items)
    return ','.join((OPS[item['op']][0], str(item['mayhem']), item['fee'].hex(), item['buyback'].hex(), item['main'].hex(),
                     item['reserved'].hex(), keys(item['fee_list']), keys(item['reserved_list']), keys(item['buyback_list'])))


# Unsorted lists where each search form answers differently: 40 sits on the
# first probe, and 36 sits beyond it on the wrong side.
FOUND_BY_LEFT_RIGHT = [fill(n) for n in (30, 31, 32, 40, 33, 50, 51)]
MISSED_MEMBER = [fill(n) for n in (36, 31, 32, 33, 34, 35, 30)]
# Sorted as bytes, unsorted as little-endian words: only a byte compare finds every slot.
BYTE_ORDER = [bytes([n, 255 - n]) + bytes(30) for n in range(30, 37)]
LAST_BYTE = [bytes(31) + bytes([n]) for n in range(30, 37)]


def fixed_cases():
    cases = []
    for op, (route, _, _, _) in OPS.items():
        add = lambda **k: cases.append(case(op, **k))
        add()
        add(fee=STRANGER)
        add(fee=RESERVED)
        add(fee=RESERVED_LIST[3])
        add(fee=BUYBACK_LIST[2])
        for key in FEE_LIST:
            add(fee=key)
        add(fee_list=FOUND_BY_LEFT_RIGHT, fee=fill(40))
        add(fee_list=FOUND_BY_LEFT_RIGHT, fee=fill(30))
        add(fee_list=MISSED_MEMBER, fee=fill(36))
        add(fee_list=MISSED_MEMBER, fee=fill(33))
        for key in BYTE_ORDER + LAST_BYTE:
            add(fee_list=BYTE_ORDER if key in BYTE_ORDER else LAST_BYTE, fee=key)
        # Mayhem curves take only the reserved keys, in any list order.
        add(mayhem=1, fee=RESERVED)
        for key in RESERVED_LIST:
            add(mayhem=1, fee=key)
        add(mayhem=1)
        add(mayhem=1, fee=FEE_LIST[3])
        add(mayhem=1, fee=STRANGER)
        # Buyback list members in any order, the zero key, and strangers.
        for key in BUYBACK_LIST:
            add(buyback=key)
        add(buyback=ZERO)
        add(buyback=STRANGER)
        add(buyback=MAIN)
        add(buyback=FEE_LIST[1])
        add(buyback=ZERO, buyback_list=[ZERO] * 8)
        add(mayhem=1, fee=RESERVED, buyback=STRANGER)
        add(mayhem=1, fee=RESERVED, buyback=ZERO)
        add(mayhem=1, fee=STRANGER, buyback=STRANGER)
        add(fee=STRANGER, buyback=STRANGER)
        add(fee=STRANGER, buyback=ZERO)
        # The zero key against zero slots.
        add(fee=ZERO)
        add(fee=ZERO, fee_list=[ZERO] * 3 + FEE_LIST[:4])
        add(fee=ZERO, main=ZERO)
        add(mayhem=1, fee=ZERO)
        add(mayhem=1, fee=ZERO, reserved_list=[ZERO] + RESERVED_LIST[:6])
        add(mayhem=1, fee=ZERO, reserved=ZERO)
    return cases


def random_key(rng, shape):
    if shape == 0:
        return rng.randbytes(32)
    if shape == 1:
        return bytes([rng.randrange(1, 4)]) * 8 + rng.randbytes(24)
    return b'\5' * 8 + rng.randbytes(24)


def random_cases(count=60, seed=157):
    rng = random.Random(seed)
    cases = []
    for op in OPS:
        for _ in range(count):
            shape = rng.randrange(3)
            keys = [random_key(rng, shape) for _ in range(7)]
            if rng.random() < 0.5:
                keys.sort()
                a, b = rng.randrange(7), rng.randrange(7)
                keys[a], keys[b] = keys[b], keys[a]
            cases.append(case(op, fee_list=keys, fee=rng.choice(keys), buyback=rng.choice(BUYBACK_LIST + [STRANGER])))
    return cases


class TradeRecipientsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'trade-recipients-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.captured = Captured()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, answer, captured, fee_key=None):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        if fee_key == ZERO and answer.split(',')[1] == '1':
            # Admitted: only the payment into the system program then fails, with no Pump code.
            self.assertIsInstance(captured['error'], str)
            return
        self.assertIsNone(captured['error'])
        paid_fee, paid_buyback = map(int, answer.split(',')[1:])
        self.assertEqual((captured['fee'] > 0, captured['buyback'] > 0), (bool(paid_fee), bool(paid_buyback)))
        self.assertGreaterEqual(min(captured['fee'], captured['buyback']), 0)

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=item['op'], host=answer, line=host_line(item)):
                self.assert_matches(answer, self.captured.run(item), item['fee'])
        return answers

    def test_fixed_cases_match_captured_program(self):
        answers = self.run_cases(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers}, {'ok', 'error:6000', 'error:6057', 'error:6062'})

    def test_seeded_random_lists_match_captured_program(self):
        answers = self.run_cases(random_cases())
        # Both answers occur for list members: unsorted lists hide some of them.
        self.assertLessEqual({'ok', 'error:6000'}, {a.split(',')[0] for a in answers})

    def test_search_is_not_a_scan(self):
        # Negative control: a linear scan would admit this member, the program does not.
        item = case('buy_v2', fee_list=MISSED_MEMBER, fee=fill(36))
        self.assertIn(item['fee'], item['fee_list'])
        self.assertEqual(self.captured.run(item)['error'], 6000)
        self.assertEqual(self.host_answers([item]), ['error:6000'])

    def test_checker_rejects_a_wrong_answer(self):
        # Negative control: the same captured run must fail against other answers.
        captured = self.captured.run(case('buy_v2'))
        self.assert_matches('ok,1,1', captured)
        for wrong in ('error:6000', 'error:6057', 'ok,0,1', 'ok,1,0'):
            with self.subTest(wrong=wrong), self.assertRaises(AssertionError):
                self.assert_matches(wrong, captured)


if __name__ == '__main__':
    unittest.main()
