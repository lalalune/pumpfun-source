"""Captured-program checks for trades on token-quote `BondingCurve` accounts below 166 bytes.

Every case runs one Pump v2 or v3 trade from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured Pump Fees,
SPL Token, and Associated Token programs, on a short synthetic curve whose
stored quote mint is a token mint and whose quote accounts are that mint's
token accounts. The bytes also go to
`programs/pump/recovered/short_curve_quote_host.rs`, which predicts the
166-byte account the short one is read as, or the failure. The captured
program then runs that account too, already funded with the predicted
top-up, and both runs must leave the same error, stored curve, events,
lamports, and token balances, apart from the top-up the user paid.

The quote mint occupies bytes 83..115, which a shape reads only from 115
bytes up. Below that the account reads as a native curve, and every route
here must refuse the short account and its predicted full account alike
with 6004 (`MintDoesNotMatchBondingCurve`). From 115 the trade proceeds and
the top-up holds nothing back: the reserves and accrued fees of a
token-quote curve are quote tokens, not lamports. Trade amounts are not
re-modelled here: they come from the captured program on both sides. This
shows matching behavior on these inputs only; it is not a byte-identity
claim.
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/short_curve_quote_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}

USER = Keypair.from_seed(bytes([216]) * 32)
CREATOR = Pubkey.from_bytes(bytes([12]) * 32)
FEE_RECIPIENT = Pubkey.from_bytes(bytes([13]) * 32)
RESERVED = Pubkey.from_bytes(bytes([14]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([17]) * 32)
MINT = Pubkey.from_bytes(bytes([15]) * 32)
QUOTE = Pubkey.from_bytes(bytes([96]) * 32)
MINT_MISMATCH = 6004


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

TOKEN_RENT = 2_039_280
VT, VS, RT, RS, SUPPLY = 1_073_000_000_000_000, 30_000_000_000, 793_100_000_000_000, 10**10, 10**15
U64 = 2**64 - 1
OPS = {
    'buy_v2': (10**9, 10**12, b''), 'buy_exact_quote_in_v2': (10**9, 1, b''), 'sell_v2': (10**12, 0, b''),
    'buy_v3': (10**9, 10**12, b'\0'), 'buy_exact_quote_in_v3': (10**9, 1, b'\0'), 'sell_v3': (10**12, 0, b''),
}
LENGTHS = (0, 7, 8, 48, 49, 60, 80, 81, 82, 83, 100, 114, 115, 116, 123, 124, 125, 130, 140, 141, 150, 165, 166, 167, 200)
BOUNDARIES = (49, 80, 81, 82, 83, 114, 115, 123, 124, 125, 140, 141, 165, 166)
BOOL_OFFSETS = (48, 81, 82, 123, 124)


def rent(length):
    return (length + 128) * 6960


def ata(owner, mint=MINT):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]


def mint_data(supply, decimals=6):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(owner, amount, mint=MINT):
    return (bytes(mint) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def global_data():
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[41:73] = bytes(FEE_RECIPIENT)
    data[97:105] = struct.pack('<Q', SUPPLY)
    data[483:515] = bytes(RESERVED)
    data[741:773] = bytes(BUYBACK)
    struct.pack_into('<Q', data, 997, 5_000)
    data[1045] = 1
    struct.pack_into('<Q', data, 1046, 10_000)
    return bytes(data)


def fee_config_data():
    data = bytearray(ACCOUNT_DISC['FeeConfig']) + bytes([FEE_CONFIG_BUMP]) + bytes(32) + bytes(24)
    data += struct.pack('<I', 1) + (0).to_bytes(16, 'little') + struct.pack('<QQQ', 0, 95, 30)
    data += struct.pack('<I', 0) + bytes(24)
    return bytes(data).ljust(4104, b'\0')


def curve_data(length, *fields, rs=RS, complete=0):
    """A token-quote curve whose tail bytes are set before it is cut to `length`."""
    data = bytearray(max(length, 166))
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, VT, VS, RT, rs, SUPPLY)
    data[48] = complete
    data[49:81] = bytes(CREATOR)
    data[83:115] = bytes(QUOTE)
    for offset, value in fields:
        data[offset:offset + len(value)] = value
    return bytes(data[:length])


# Tail fields a shape may or may not read. Each stays valid if it is read.
PROFILES = {
    'plain': (),
    'mayhem': ((81, b'\1'),),
    'cashback': ((82, b'\1'),),
    'creator_bps': ((115, struct.pack('<Q', 500)), (123, b'\1')),
    'holder': ((124, b'\1'),),
    'accrued': ((125, struct.pack('<QQ', 3_000_000, 7_000_000)),),
    'post_fields': ((141, b'\2' + struct.pack('<QQQ', 25_000_000_000, 5, 6)),),
}


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

    def run(self, op, curve, lamports, mayhem, creator):
        vm = self.vm
        user = USER.pubkey()
        fee = RESERVED if mayhem else FEE_RECIPIENT
        vault = pda(b'creator-vault', bytes(creator))[0]
        accounts = {
            user: Account(10**13, b'', SYSTEM),
            GLOBAL: Account(10**9, global_data(), PUMP),
            MINT: Account(10**9, mint_data(SUPPLY), TOKEN),
            QUOTE: Account(10**9, mint_data(0), TOKEN),
            CURVE: Account(lamports, curve, PUMP),
            ata(CURVE): Account(TOKEN_RENT, token_data(CURVE, RT), TOKEN),
            ata(user): Account(TOKEN_RENT, token_data(user, 10**13), TOKEN),
            ata(CURVE, QUOTE): Account(TOKEN_RENT, token_data(CURVE, RS + 20_000_000, QUOTE), TOKEN),
            ata(user, QUOTE): Account(TOKEN_RENT, token_data(user, 10**14, QUOTE), TOKEN),
            ata(fee, QUOTE): Account(TOKEN_RENT, token_data(fee, 0, QUOTE), TOKEN),
            ata(BUYBACK, QUOTE): Account(TOKEN_RENT, token_data(BUYBACK, 0, QUOTE), TOKEN),
            ata(vault, QUOTE): Account(TOKEN_RENT, token_data(vault, 0, QUOTE), TOKEN),
            FEE_CONFIG: Account(10**9, fee_config_data(), FEES),
            GLOBAL_VOLUME: Account(10**9, ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP),
            CURVE_V2: Account(10**7, b'', SYSTEM),
            fee: Account(10**9, b'', SYSTEM),
            BUYBACK: Account(10**9, b'', SYSTEM),
            vault: Account(10**9, b'', SYSTEM),
            # sell_v2 creates this account itself.
            USER_VOLUME: Account(0, b'', SYSTEM) if op == 'sell_v2' else Account(
                10**9, ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(user) + bytes(97), PUMP),
            # A token-quote trade creates the volume accumulator's quote
            # account and the user pays its rent; reset it to absent so the
            # short run and the twin run both pay it.
            ata(USER_VOLUME, QUOTE): Account(0, b'', SYSTEM),
        }
        for key, account in accounts.items():
            vm.set_account(key, account)
        names = {
            'global': GLOBAL, 'base_mint': MINT, 'mint': MINT, 'quote_mint': QUOTE, 'base_token_program': TOKEN,
            'quote_token_program': TOKEN, 'token_program': TOKEN, 'associated_token_program': ATA,
            'fee_recipient': fee, 'recipient': fee, 'associated_quote_fee_recipient': ata(fee, QUOTE),
            'associated_quote_recipient': ata(fee, QUOTE), 'buyback_fee_recipient': BUYBACK,
            'associated_quote_buyback_fee_recipient': ata(BUYBACK, QUOTE), 'bonding_curve': CURVE,
            'associated_bonding_curve': ata(CURVE), 'associated_base_bonding_curve': ata(CURVE),
            'associated_quote_bonding_curve': ata(CURVE, QUOTE), 'user': user, 'payer': user,
            'associated_user': ata(user), 'associated_base_user': ata(user),
            'associated_quote_user': ata(user, QUOTE), 'creator_vault': vault,
            'associated_creator_vault': ata(vault, QUOTE), 'sharing_config': SHARING,
            'global_volume_accumulator': GLOBAL_VOLUME, 'user_volume_accumulator': USER_VOLUME,
            'associated_user_volume_accumulator': ata(USER_VOLUME, QUOTE), 'fee_config': FEE_CONFIG,
            'fee_program': FEES, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
        }
        if op.endswith('_v3'):
            # The v3 handlers take the buyback recipient's quote account in
            # the `buyback_fee_recipient` slot itself.
            names['buyback_fee_recipient'] = ata(BUYBACK, QUOTE)
        ix = IX[op]
        metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
        amount, limit, trailing = OPS[op]
        data = bytes(ix['discriminator']) + struct.pack('<QQ', amount, limit) + trailing
        vm.expire_blockhash()
        watched = (user, CURVE, fee, BUYBACK, vault)
        before = [self.lamports(key) for key in watched]
        tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], user, [USER], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            return {'error': int(code.group(1)) if code else text}
        token = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0]
        return {
            'error': None, 'delta': [self.lamports(key) - b for key, b in zip(watched, before)],
            'curve_lamports': self.lamports(CURVE), 'curve': bytes(vm.get_account(CURVE).data),
            'events': [line for line in result.logs() if line.startswith('Program data: ')],
            'tokens': (token(ata(user)), token(ata(CURVE)), token(ata(user, QUOTE)), token(ata(CURVE, QUOTE))),
        }


def request(curve, lamports):
    return f'{curve.hex()},{lamports}'


def fixed_cases():
    cases = []
    for op in OPS:
        add = lambda curve, lamports: cases.append(dict(op=op, curve=curve, lamports=lamports))
        for length in LENGTHS:
            # A curve funded to the rent of its own length, and one over-funded.
            add(curve_data(length), rent(length))
            add(curve_data(length), rent(166) + 10**9)
            for fields in PROFILES.values():
                add(curve_data(length, *fields), rent(166) + 10_000_000)
        for length in BOUNDARIES:
            for offset in BOOL_OFFSETS:
                add(curve_data(length, (offset, b'\2')), rent(166))
            add(curve_data(length, complete=1), rent(166))
            add(curve_data(length, (125, struct.pack('<Q', U64))), rent(166))
            add(curve_data(length, (133, struct.pack('<Q', U64))), rent(166))
            # One lamport below the full rent, and below the curve's own rent.
            add(curve_data(length), rent(166) - 1)
            add(curve_data(length), rent(length) // 2)
    return cases


def wrong_discriminator(length):
    return b'\1' * 8 + curve_data(length)[8:]


def random_cases(count=20, seed=159):
    rng = random.Random(seed)
    cases = []
    for op in OPS:
        for _ in range(count):
            length = rng.choice((rng.randrange(0, 180), rng.choice(BOUNDARIES)))
            fields = [f for fields in PROFILES.values() for f in fields if rng.random() < 0.3]
            cases.append(dict(op=op, curve=curve_data(length, *fields, complete=rng.choice((0, 0, 0, 1))),
                              lamports=rng.choice((rent(length), rent(166), rent(166) + rng.randrange(10**8)))))
    return cases


class ShortCurveQuoteCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'short-curve-quote-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.captured = Captured()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(request(item['curve'], item['lamports']) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def check(self, item, answer):
        """Run the case; returns 'ok' when the captured trade succeeded."""
        op, curve, lamports = item['op'], item['curve'], item['lamports']
        if not answer.startswith('ok'):
            short = self.captured.run(op, curve, lamports, False, CREATOR)
            if answer == 'invalid':
                self.assertIn('InvalidAccountData', str(short['error']))
            elif answer == 'bool':
                self.assertIn('BorshIoError', str(short['error']))
            else:
                self.assertEqual(short['error'], int(answer[6:]))
            return 'error'
        _, top_up, image = answer.split(',')
        top_up, image = int(top_up), bytes.fromhex(image)
        mayhem, creator = image[81] == 1, Pubkey.from_bytes(image[49:81])
        short = self.captured.run(op, curve, lamports, mayhem, creator)
        full = self.captured.run(op, image, lamports + top_up, mayhem, creator)
        self.assertEqual(short['error'], full['error'])
        if image[83:115] == bytes(32):
            # The shape does not read the quote mint at this length: the
            # account reads as native and the token-quote route refuses it.
            self.assertEqual(short['error'], MINT_MISMATCH)
            return 'error'
        if short['error'] is not None:
            # The account was read and the rent settled: only the trade itself may fail.
            self.assertNotRegex(str(short['error']), 'InvalidAccountData|BorshIoError|^6024$')
            return 'error'
        self.assertEqual(len(short['curve']), max(len(curve), 166))
        self.assertEqual(short['curve'], full['curve'])
        self.assertEqual(short['events'], full['events'])
        self.assertEqual(short['tokens'], full['tokens'])
        self.assertEqual(short['curve_lamports'], full['curve_lamports'])
        self.assertEqual(short['delta'][0], full['delta'][0] - top_up)
        self.assertEqual(short['delta'][2:], full['delta'][2:])
        return 'ok'

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        outcomes = []
        for item, answer in zip(cases, answers):
            with self.subTest(op=item['op'], length=len(item['curve']), curve=item['curve'][48:].hex(),
                              lamports=item['lamports'], host=answer[:30]):
                outcomes.append(self.check(item, answer))
        return answers, outcomes

    def test_fixed_cases_match_captured_program(self):
        answers, outcomes = self.run_cases(fixed_cases())
        self.assertGreater(outcomes.count('ok'), 300)
        self.assertEqual({a.split(',')[0] for a in answers}, {'ok', 'invalid', 'bool'})
        self.assertTrue(any(int(a.split(',')[1]) > 0 for a in answers if a.startswith('ok')))

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_wrong_discriminator_is_refused_at_every_length(self):
        self.run_cases([dict(op=op, curve=wrong_discriminator(length), lamports=rent(166))
                        for op in ('buy_v2', 'sell_v3') for length in (49, 100, 115, 165, 166)])

    def test_quote_mint_is_read_from_115_bytes(self):
        # The headline boundary: the same stored bytes refuse the trade at
        # 114 bytes and trade at 115, and the 114-byte run's refusal is the
        # mint mismatch, not a read failure.
        for op in OPS:
            short = self.captured.run(op, curve_data(114), rent(166), False, CREATOR)
            self.assertEqual(short['error'], MINT_MISMATCH)
            full = self.captured.run(op, curve_data(115), rent(115), False, CREATOR)
            self.assertIsNone(full['error'])
            self.assertEqual(len(full['curve']), 166)


if __name__ == '__main__':
    unittest.main()
