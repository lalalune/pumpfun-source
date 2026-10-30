"""Captured-program checks for the recovered `buy_v2` and `buy_exact_quote_in_v2`.

Every case runs Pump `buy_v2` or `buy_exact_quote_in_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured Pump Fees,
SPL Token, and Associated Token programs, against synthetic accounts on the
native (WSOL quote mint) path. The same inputs go to
`programs/pump/recovered/buy_v2_host.rs`, and the error code, lamport
movements, stored curve, token delivery, and TradeEvent fields must agree.
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/buy_v2_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
TRADE_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'TradeEvent'))

USER = Keypair.from_seed(bytes([211]) * 32)
CREATOR = Pubkey.from_bytes(bytes([12]) * 32)
FEE_RECIPIENT = Pubkey.from_bytes(bytes([13]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([14]) * 32)
MINT = Pubkey.from_bytes(bytes([15]) * 32)
STRANGER = Pubkey.from_bytes(bytes([77]) * 32)


def pda(*seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)


GLOBAL = pda(b'global')[0]
CURVE = pda(b'bonding-curve', bytes(MINT))[0]
EVENT_AUTHORITY = pda(b'__event_authority')[0]
GLOBAL_VOLUME = pda(b'global_volume_accumulator')[0]
USER_VOLUME = pda(b'user_volume_accumulator', bytes(USER.pubkey()))[0]
FEE_CONFIG, FEE_CONFIG_BUMP = pda(b'fee_config', bytes(PUMP), program=FEES)
SHARING = pda(b'sharing-config', bytes(MINT), program=FEES)[0]
VAULT = pda(b'creator-vault', bytes(CREATOR))[0]
DEFAULT_VAULT = pda(b'creator-vault', bytes(32))[0]

TX_FEE = 5000
USER_LAMPORTS = 10**16
CURVE_RENT = 2_046_960
TOKEN_RENT = 2_039_280
VT, VS, RT, SUPPLY = 1_073_000_000_000_000, 30_000_000_000, 793_100_000_000_000, 10**15
MCAP = SUPPLY * VS // VT
U64 = 2**64 - 1


def ata(owner, mint=MINT):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]


def mint_data(supply, decimals=6):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(owner, amount):
    return (bytes(MINT) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def global_data(buyback_bps, configurable):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[41:73] = bytes(FEE_RECIPIENT)
    data[741:773] = bytes(BUYBACK)
    struct.pack_into('<Q', data, 997, buyback_bps)
    data[1045] = int(configurable)
    return bytes(data)


def fee_config_data(tiers):
    data = bytearray(ACCOUNT_DISC['FeeConfig']) + bytes([FEE_CONFIG_BUMP]) + bytes(32) + bytes(24)
    data += struct.pack('<I', len(tiers))
    for threshold, protocol, creator in tiers:
        data += threshold.to_bytes(16, 'little') + struct.pack('<QQQ', 0, protocol, creator)
    data += struct.pack('<I', 0) + bytes(24)
    return bytes(data).ljust(4104, b'\0')


def curve_data(case):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, case['vt'], case['vs'], case['rt'], case['rs'], case['supply'])
    data[48] = int(case['complete'])
    data[49:81] = bytes(CREATOR if case['creator'] else SYSTEM)
    struct.pack_into('<Q', data, 115, case['creator_bps'])
    return bytes(data)


DEFAULTS = dict(op='buy', vt=VT, vs=VS, rt=RT, rs=0, supply=SUPPLY, complete=False, creator=True,
                creator_bps=0, configurable=False, buyback=0, vault=0, trailing=b'',
                tiers=((0, 95, 30),), fee_ok=True, buyback_ok=True)


def case(arg0, arg1, **changes):
    item = dict(DEFAULTS, **changes)
    item['args'] = (arg0, arg1)
    return item


def decode_trade(data):
    offset = 8 + 32
    def take(fmt):
        nonlocal offset
        value = struct.unpack_from(fmt, data, offset)[0]
        offset += struct.calcsize(fmt)
        return value
    event = {}
    event['sol_amount'], event['token_amount'] = take('<Q'), take('<Q')
    offset += 1 + 32 + 8
    event['virtual_sol'], event['virtual_token'] = take('<Q'), take('<Q')
    event['real_sol'], event['real_token'] = take('<Q'), take('<Q')
    offset += 32
    event['fee_bps'], event['fee'] = take('<Q'), take('<Q')
    offset += 32
    event['creator_bps'], event['creator_fee'] = take('<Q'), take('<Q')
    event['track_volume'] = data[offset]
    offset += 1 + 32
    name_len = take('<I')
    event['ix_name'] = data[offset:offset + name_len].decode()
    offset += name_len + 1 + 16
    event['buyback_bps'], event['buyback_fee'] = take('<Q'), take('<Q')
    return event


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.add_program_from_file(FEES, FEES_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(ATA, ATA_ELF)
    vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
    vault = VAULT if item['creator'] else DEFAULT_VAULT
    accounts = {
        USER.pubkey(): Account(USER_LAMPORTS, b'', SYSTEM),
        GLOBAL: Account(10**9, global_data(item['buyback'], item['configurable']), PUMP),
        MINT: Account(10**9, mint_data(item['supply']), TOKEN),
        WSOL: Account(10**9, mint_data(0, 9), TOKEN),
        CURVE: Account(CURVE_RENT + item['rs'], curve_data(item), PUMP),
        ata(CURVE): Account(TOKEN_RENT, token_data(CURVE, item['rt']), TOKEN),
        ata(USER.pubkey()): Account(TOKEN_RENT, token_data(USER.pubkey(), 0), TOKEN),
        FEE_CONFIG: Account(10**9, fee_config_data(item['tiers']), FEES),
        GLOBAL_VOLUME: Account(10**9, ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP),
        USER_VOLUME: Account(10**9, ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(USER.pubkey()) + bytes(97), PUMP),
    }
    if item['vault']:
        accounts[vault] = Account(item['vault'], b'', SYSTEM)
    for key, account in accounts.items():
        vm.set_account(key, account)
    fee_recipient = FEE_RECIPIENT if item['fee_ok'] else STRANGER
    buyback = BUYBACK if item['buyback_ok'] else STRANGER
    names = {
        'global': GLOBAL, 'base_mint': MINT, 'quote_mint': WSOL, 'base_token_program': TOKEN,
        'quote_token_program': TOKEN, 'associated_token_program': ATA, 'fee_recipient': fee_recipient,
        'associated_quote_fee_recipient': ata(fee_recipient, WSOL), 'buyback_fee_recipient': buyback,
        'associated_quote_buyback_fee_recipient': ata(buyback, WSOL), 'bonding_curve': CURVE,
        'associated_base_bonding_curve': ata(CURVE), 'associated_quote_bonding_curve': ata(CURVE, WSOL),
        'user': USER.pubkey(), 'associated_base_user': ata(USER.pubkey()),
        'associated_quote_user': ata(USER.pubkey(), WSOL), 'creator_vault': vault,
        'associated_creator_vault': ata(vault, WSOL), 'sharing_config': SHARING,
        'global_volume_accumulator': GLOBAL_VOLUME, 'user_volume_accumulator': USER_VOLUME,
        'associated_user_volume_accumulator': ata(USER_VOLUME, WSOL), 'fee_config': FEE_CONFIG,
        'fee_program': FEES, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
    }
    ix = IX['buy_v2' if item['op'] == 'buy' else 'buy_exact_quote_in_v2']
    metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
    watched = (USER.pubkey(), CURVE, FEE_RECIPIENT, BUYBACK, vault)
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [lamports(key) for key in watched]
    data = bytes(ix['discriminator']) + struct.pack('<QQ', *item['args']) + item['trailing']
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], USER.pubkey(), [USER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    delta = dict(zip(('user', 'curve', 'recipient', 'buyback', 'vault'),
                     (lamports(k) - b for k, b in zip(watched, before))))
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    stored = vm.get_account(CURVE).data
    return {
        'error': None, 'delta': delta, 'events': len(events),
        'trade': decode_trade(next(e for e in events if e[:8] == TRADE_EVENT)),
        'reserves': struct.unpack_from('<QQQQ', stored, 8), 'complete': stored[48],
        'user_tokens': struct.unpack_from('<Q', vm.get_account(ata(USER.pubkey())).data, 64)[0],
    }


def host_line(item):
    fields = [item['op'], item['vt'], item['vs'], item['rt'], item['rs'], int(item['complete']), int(item['creator']),
              item['creator_bps'], item['supply'], int(item['configurable']), item['buyback'], item['vault'],
              *item['args'], item['trailing'].hex(), ';'.join(f'{t}:{p}:{c}' for t, p, c in item['tiers']),
              int(item['fee_ok']), int(item['buyback_ok'])]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    cases = []
    add = lambda *a, **k: cases.append(case(*a, **k))
    bad_fee, bad_buyback = dict(fee_ok=False), dict(buyback_ok=False)
    # Ordinary buys, vault rent top-up, creator handling, and buyback split.
    add(10**9, 10**12)
    add(1, 10)
    for vault in (1, 890_879, 890_880, 10**9):
        add(10**9, 10**12, vault=vault)
    add(10**9, 10**12, creator=False)
    for buyback in (1, 5_000, 10_000, 10_001):
        add(10**9, 10**12, buyback=buyback)
    add(10**11, 10**13, buyback=10_001)
    add(10**9, 10**12, buyback=20_000)
    # Fee-tier choice by pre-trade market cap and the creator-bps override.
    add(10**9, 10**12, tiers=((0, 95, 30), (MCAP, 50, 20)))
    add(10**9, 10**12, tiers=((0, 95, 30), (MCAP + 1, 50, 20)))
    add(10**9, 10**12, tiers=())
    add(10**9, 10**12, creator_bps=500, configurable=True)
    add(10**9, 10**12, tiers=((0, U64, 30),))
    # Slippage bound, curve arithmetic failures, and guard order.
    add(10**9, 28_309)
    add(10**9, 28_310)
    add(6, 10**12, vt=5, rt=10)
    add(5, 10**12, vt=5, rt=10)
    add(10**9, U64, vs=U64, vt=10**9 + 1)
    add(0, 10**12)
    add(10**9, 10**12, complete=True)
    add(RT + 1, U64)
    # The single partial_fill byte: no track_volume byte precedes it.
    add(RT + 1, U64, trailing=b'\1')
    add(10**18, 85_000_000_000, trailing=b'\1')
    add(10**9, 10**12, rt=0, trailing=b'\1')
    add(10**9, 10**12, trailing=b'\0\1')
    add(10**9, 10**12, trailing=b'\1\7')
    add(10**9, 10**12, trailing=b'\2')
    # Recipient checks run after the entry guards and before pricing.
    add(10**9, 10**12, **bad_fee)
    add(10**9, 10**12, **bad_buyback)
    add(10**9, 10**12, fee_ok=False, buyback_ok=False)
    add(10**9, 10**12, complete=True, **bad_fee)
    add(0, 10**12, **bad_fee)
    add(RT + 1, U64, **bad_buyback)
    add(10**9, 1, **bad_buyback)
    add(6, 10**12, vt=5, rt=10, **bad_fee)
    add(10**9, 10**12, tiers=(), **bad_buyback)
    add(10**9, 10**12, trailing=b'\2', **bad_fee)
    # buy_exact_quote_in_v2.
    exact = lambda *a, **k: add(*a, op='exact', **k)
    exact(10**9, 1)
    exact(10**9, 1, creator=False)
    exact(10**9, 1, vault=890_880)
    exact(10**9, 1, buyback=5_000)
    exact(10**9, 1, tiers=((0, 0, 0),))
    exact(10**9, 1, creator_bps=9_000, configurable=True)
    exact(10**9, 1, tiers=((0, U64, 30),))
    exact(10**9, 1, tiers=((0, 30, U64),), creator=False)
    exact(10**9, 1, tiers=())
    exact(10**9, 1, vt=0)
    exact(10**9, 1, complete=True)
    exact(0, 0)
    exact(0, 1)
    exact(10**9, 0)
    for spendable in (1, 2, 50, 101):
        exact(spendable, 1)
    exact(108, 1)
    exact(14, 1, tiers=((0, 9_000, 9_000),))
    exact(10**9, 10**15)
    exact(10**11, 1)
    exact(10**11, 1, trailing=b'\1')
    exact(86_067_975_000, 1, trailing=b'\1')
    exact(86_080_000_000, 1, trailing=b'\1')
    exact(10**11, 1, trailing=b'\3')
    exact(0, 1, **bad_fee)
    exact(0, 1, **bad_buyback)
    exact(1, 1, **bad_fee)
    exact(10**9, 10**15, **bad_buyback)
    exact(10**9, 1, vt=0, **bad_buyback)
    exact(10**9, 1, fee_ok=False, buyback_ok=False)
    return cases


def random_cases(count=50, seed=2555):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        vt = rng.choice((VT, rng.randrange(10**6, 10**16), rng.randrange(2, 10**4)))
        rt = rng.randrange(0, vt)
        vs = rng.choice((VS, rng.randrange(1, 10**12)))
        supply = rng.choice((SUPPLY, rng.randrange(0, 10**16)))
        mcap = supply * vs // vt
        tiers = [(0, rng.randrange(0, 300), rng.randrange(0, 200))]
        for _ in range(rng.randrange(0, 3)):
            tiers.append((rng.choice((mcap, mcap + 1, max(mcap - 1, 0), rng.randrange(0, 2 * mcap + 2))),
                          rng.randrange(0, 300), rng.randrange(0, 200)))
        common = dict(vt=vt, vs=vs, rt=rt, supply=supply, tiers=tuple(tiers), creator=rng.random() < 0.8,
                      creator_bps=rng.choice((0, rng.randrange(1, 1_000))), configurable=rng.random() < 0.5,
                      buyback=rng.choice((0, rng.randrange(0, 10_001))), vault=rng.choice((0, 1, 890_880)),
                      trailing=rng.choice((b'', b'\0', b'\1', b'\1\1')),
                      fee_ok=rng.random() < 0.9, buyback_ok=rng.random() < 0.9)
        if rng.random() < 0.5:
            amount = rng.choice((rng.randrange(1, rt + 2), rng.randrange(1, 10**6)))
            cases.append(case(amount, rng.choice((U64, rng.randrange(0, 10**12))), **common))
        else:
            cases.append(case(rng.randrange(1, 10**12), rng.choice((1, rng.randrange(1, 10**13))), op='exact', **common))
    return cases


class BuyV2CapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'buy-v2-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def check(self, item, answer):
        self.assert_matches(item, answer, run_captured(item))

    def assert_matches(self, item, answer, captured):
        if answer == 'panic':
            self.assertIn('ProgramFailedToComplete', str(captured['error']))
            return
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        (tokens, sol, protocol_bps, protocol_fee, creator_bps, creator_fee, buyback_fee, vault_credit,
         vt, vs, rt, rs, complete) = map(int, answer.split(',')[1:])
        self.assertEqual(captured['delta'], {
            # Signed after - before: the buyer pays, every receiver is credited.
            'user': -(TX_FEE + sol + protocol_fee + vault_credit), 'curve': sol,
            'recipient': protocol_fee - buyback_fee, 'buyback': buyback_fee, 'vault': vault_credit,
        })
        self.assertEqual(captured['reserves'], (vt, vs, rt, rs))
        self.assertEqual(captured['complete'], complete)
        self.assertEqual(captured['user_tokens'], tokens)
        self.assertEqual(captured['events'], 2 if complete else 1)
        self.assertEqual(captured['trade'], {
            'sol_amount': sol, 'token_amount': tokens, 'virtual_sol': vs, 'virtual_token': vt,
            'real_sol': rs, 'real_token': rt, 'fee_bps': protocol_bps, 'fee': protocol_fee,
            'creator_bps': creator_bps, 'creator_fee': creator_fee, 'track_volume': 0,
            'ix_name': 'buy' if item['op'] == 'buy' else 'buy_exact_quote_in',
            'buyback_bps': item['buyback'], 'buyback_fee': buyback_fee,
        })

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.check(item, answer)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_reversed_balance_movements(self):
        # Negative control: a captured run that passes must fail once any one
        # balance movement is reversed (debit <-> credit of the same size).
        item = case(10**9, 10**12, buyback=5_000)
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(item, answer, captured)
        for key in ('user', 'curve', 'recipient', 'buyback', 'vault'):
            with self.subTest(reversed=key):
                self.assertNotEqual(captured['delta'][key], 0)
                flipped = dict(captured, delta=dict(captured['delta'], **{key: -captured['delta'][key]}))
                with self.assertRaises(AssertionError):
                    self.assert_matches(item, answer, flipped)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes - {'ok', 'panic'}, {
            'error:6000', 'error:6002', 'error:6005', 'error:6020', 'error:6021', 'error:6024',
            'error:6025', 'error:6026', 'error:6041', 'error:6042', 'error:6057', 'error:102',
        })
        self.assertIn('panic', outcomes)
        self.assertTrue(any(a.startswith('ok') and a.endswith(',1') for a in answers))


if __name__ == '__main__':
    unittest.main()
