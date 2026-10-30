"""Captured-program checks for one recovered `multi_hop_curve_swap` hop.

Every case runs Pump `multi_hop_curve_swap` from the captured
`evidence/original/pump/deployed.so` (upgradeable loader) on LiteSVM with a
single curve hop: a native-SOL curve (quote WSOL) or an SPL-token quote
curve, buying with the quote or selling the base, under each of the four
hop fee flags. On mainnet only pump_amm calls the instruction, signing for
its `global_config` PDA; here signature verification is off so that PDA can
sit in a signer slot, and every other check runs unchanged. FeeConfig is
plain account data (no pump_fees CPI). Account state is synthetic (IDL
layouts). The same inputs go to
`programs/pump/recovered/multi_hop_hop_host.rs`, and the error, the curve's
reserves and fee counters afterwards, the base tokens moved, the quote the
curve pays or keeps, and the buyback recipient's receipt must agree. Buys
that would cross into the post-complete fill are left out (the host answers
`unmodelled`). This shows matching behavior on these inputs only; it is not
a byte-identity claim.
"""
from pathlib import Path
import hashlib
import json
import random
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/multi_hop_hop_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
PUMP_AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
SYSTEM = Pubkey.default()
SWAP = next(i for i in IDL['instructions'] if i['name'] == 'multi_hop_curve_swap')
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}

USER = Keypair.from_seed(bytes([233]) * 32)
CREATOR = Pubkey.from_bytes(bytes([64]) * 32)
MINT = Pubkey.from_bytes(bytes([76]) * 32)
QUOTE = Pubkey.from_bytes(bytes([77]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([102]) * 32)
TS = 1_800_000_000
CURVE_RENT = 2_046_240
WSOL_RENT = 2_039_280
SUPPLY = 10**15
# (protocol, creator) basis points: the single SOL fee tier and the flat fees.
TIER_BPS = (95, 30)
FLAT_BPS = (90, 20)


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(seeds, program)[0]


def ata(owner, mint, program=TOKEN):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA)


GLOBAL = pda([b'global'])
FEE_CONFIG = pda([b'fee_config', bytes(PUMP)], FEES)
AMM_CONFIG = pda([b'global_config'], PUMP_AMM)
CURVE = pda([b'bonding-curve', bytes(MINT)])


def mint_data(supply=SUPPLY, decimals=6):
    return struct.pack('<I32sQBBI32s', 0, bytes(32), supply, decimals, 1, 0, bytes(32))


def token_data(mint, owner, amount, native=None):
    tag, value = (0, 0) if native is None else (1, native)
    return struct.pack('<32s32sQI32sBIQQI32s', bytes(mint), bytes(owner), amount, 0, bytes(32), 1, tag, value,
                       0, 0, bytes(32))


def global_data(buyback_bps):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    struct.pack_into('<QQQQQ', data, 73, 1_073_000_000_000_000, 30_000_000_000, 793_100_000_000_000, SUPPLY, 95)
    struct.pack_into('<Q', data, 154, 30)
    data[450] = 1
    data[451:483] = bytes([92]) * 32   # whitelist_pda
    data[515] = 1
    data[741:773] = bytes(BUYBACK)
    struct.pack_into('<QQ', data, 997, buyback_bps, 30_000_000_000)
    return bytes(data)


def fee_config_data(length, table_empty):
    bump = Pubkey.find_program_address([b'fee_config', bytes(PUMP)], FEES)[1]
    tiers = () if table_empty else ((0,) + TIER_BPS,)
    data = (bytes([143, 52, 146, 187, 219, 123, 76, 155]) + bytes([bump]) + bytes([93]) * 32
            + struct.pack('<QQQ', 0, *FLAT_BPS) + struct.pack('<I', len(tiers)))
    for threshold, protocol, creator in tiers:
        data += threshold.to_bytes(16, 'little') + struct.pack('<QQQ', 0, protocol, creator)
    data += struct.pack('<I', 0) + struct.pack('<QQQ', 0, 0, 0)
    return data.ljust(length, b'\0')[:length]


def curve_data(item):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, item['vtr'], item['vqr'], item['rtr'], item['rqr'], SUPPLY)
    data[48] = item['complete']
    data[49:81] = bytes(CREATOR) if item['creator'] else bytes(32)
    data[81], data[82] = item['mayhem'], item['cashback']
    if item['quote'] == 'spl':
        data[83:115] = bytes(QUOTE)
    struct.pack_into('<QQ', data, 125, item['cf'], item['pf'])
    return bytes(data)


SELL = dict(buy=0, vtr=973_000_000_000_000, vqr=130_000_000_000, rtr=693_100_000_000_000, rqr=100_000_000_000)
DEFAULTS = dict(buy=1, quote='sol', amount=10**9, flags=(3,), remaining=5, vtr=1_073_000_000_000_000,
                vqr=30_000_000_000, rtr=793_100_000_000_000, rqr=0, complete=0, mayhem=0, cashback=0, creator=1,
                cf=0, pf=0, fee_len=2512, table_empty=0, buyback_bps=5000, user_base=10**15, curve_quote=None)


def case(**changes):
    unknown = set(changes) - set(DEFAULTS)
    assert not unknown, unknown
    item = dict(DEFAULTS, **changes)
    if item['curve_quote'] is None:
        item['curve_quote'] = item['rqr'] + item['cf'] + item['pf']
    return item


def host_line(item):
    bps = TIER_BPS if item['quote'] == 'sol' else FLAT_BPS
    flags = ':'.join(map(str, item['flags'])) or '-'
    return ','.join(map(str, [item['buy'], int(item['quote'] == 'sol'), item['amount'], flags, item['remaining'],
                              item['vtr'], item['vqr'], item['rtr'], item['rqr'], item['complete'], item['mayhem'],
                              item['cashback'], item['creator'], item['cf'], item['pf'], item['fee_len'],
                              item['table_empty'], bps[0], bps[1], item['buyback_bps'], item['user_base'],
                              item['curve_quote']]))


def hop_metas(quote):
    keys = [MINT, quote, CURVE, ata(CURVE, MINT), ata(CURVE, quote)]
    return [AccountMeta(k, False, i >= 2) for i, k in enumerate(keys)]


def run_captured(item, index=0):
    vm = LiteSVM().with_transaction_history(0).with_sigverify(False)
    programdata = pda([bytes(PUMP)], UPGRADEABLE)
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + PUMP_ELF.read_bytes(),
                                        UPGRADEABLE, False))
    vm.set_account(PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    vm.set_clock(Clock(1000 + index, 0, 0, 0, TS))
    native = item['quote'] == 'sol'
    quote = WSOL if native else QUOTE
    user_quote, user_base = ata(USER.pubkey(), quote), ata(USER.pubkey(), MINT)
    recipient = ata(BUYBACK, quote)
    curve_lamports = CURVE_RENT + (item['rqr'] + item['cf'] + item['pf'] if native else 0)
    state = {GLOBAL: (10**9, PUMP, global_data(item['buyback_bps'])),
             FEE_CONFIG: (10**9, FEES, fee_config_data(item['fee_len'], item['table_empty'])),
             USER.pubkey(): (10**13, SYSTEM, b''), MINT: (10**9, TOKEN, mint_data()),
             WSOL: (10**9, TOKEN, mint_data(0, 9)), QUOTE: (10**9, TOKEN, mint_data(10**16)),
             CURVE: (curve_lamports, PUMP, curve_data(item)),
             ata(CURVE, MINT): (10**9, TOKEN, token_data(MINT, CURVE, item['rtr'])),
             user_base: (10**9, TOKEN, token_data(MINT, USER.pubkey(), item['user_base']))}
    if native:
        state[user_quote] = (WSOL_RENT, TOKEN, token_data(WSOL, USER.pubkey(), 0, WSOL_RENT))
        state[recipient] = (WSOL_RENT, TOKEN, token_data(WSOL, BUYBACK, 0, WSOL_RENT))
    else:
        state[user_quote] = (10**9, TOKEN, token_data(QUOTE, USER.pubkey(), 10**15))
        state[recipient] = (10**9, TOKEN, token_data(QUOTE, BUYBACK, 0))
        state[ata(CURVE, QUOTE)] = (10**9, TOKEN, token_data(QUOTE, CURVE, item['curve_quote']))
    for key, (lamports, owner, data) in state.items():
        vm.set_account(key, Account(lamports, data, owner))
    source, destination = (user_quote, user_base) if item['buy'] else (user_base, user_quote)
    metas = [AccountMeta(GLOBAL, False, False), AccountMeta(FEE_CONFIG, False, False),
             AccountMeta(AMM_CONFIG, True, False), AccountMeta(USER.pubkey(), True, True),
             AccountMeta(USER.pubkey(), True, False), AccountMeta(source, False, True),
             AccountMeta(destination, False, True), AccountMeta(recipient, False, True),
             AccountMeta(TOKEN, False, False), AccountMeta(TOKEN22, False, False), AccountMeta(SYSTEM, False, False),
             AccountMeta(pda([b'__event_authority']), False, False), AccountMeta(PUMP, False, False)]
    assert [m.pubkey for m in metas[:3]] == [GLOBAL, FEE_CONFIG, AMM_CONFIG] and len(metas) == len(SWAP['accounts'])
    metas += (hop_metas(quote) * 2)[:item['remaining']]
    data = bytes(SWAP['discriminator']) + struct.pack('<QI', item['amount'], len(item['flags'])) + bytes(item['flags'])
    ixs = [set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)]
    tx = Transaction.new_unsigned(Message.new_with_blockhash(ixs, USER.pubkey(), vm.latest_blockhash()))
    tx.partial_sign([USER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)

    def amount(key):
        return struct.unpack_from('<Q', bytes(vm.get_account(key).data), 64)[0]
    curve = vm.get_account(CURVE)
    return {'error': str(result.err()) if failed else None, 'curve': bytes(curve.data),
            'curve_quote': curve.lamports - curve_lamports if native else amount(ata(CURVE, QUOTE)) - item['curve_quote'],
            'user_base': amount(user_base) - item['user_base'],
            'recipient': (vm.get_account(recipient).lamports - WSOL_RENT) if native else amount(recipient)}


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    # Pre-loop argument checks, then hop admission.
    add(amount=0)
    add(amount=0, flags=(4,), remaining=4)
    add(remaining=0)
    add(remaining=4)
    add(remaining=6)
    add(remaining=4, flags=())
    add(flags=())
    add(flags=(3, 3))
    add(flags=(4,))
    add(remaining=10, flags=(3,))
    add(mayhem=1)
    add(mayhem=1, complete=1)
    add(mayhem=1, cashback=1, flags=(2,))
    add(mayhem=1, cashback=1, flags=(1,))
    add(complete=1)
    add(complete=1, cashback=1)
    add(cashback=1, flags=(2,))
    add(cashback=1, flags=(3,))
    add(cashback=1, flags=(1,))
    add(cashback=1, flags=(0,))
    add(fee_len=2511)
    add(fee_len=2511, flags=(0,))
    add(table_empty=1, flags=(0,))
    add(table_empty=1, **SELL)
    # Native and SPL buys and sells under every flag.
    for quote in ('sol', 'spl'):
        for flag in range(4):
            add(quote=quote, flags=(flag,))
            add(quote=quote, flags=(flag,), amount=123_456_789, **SELL)
            add(quote=quote, flags=(flag,), creator=0, cf=7, pf=11)
    # Small budgets: fees, the net trim, and a zero base.
    for amount in (1, 2, 50, 100, 101, 102, 125, 126, 127, 200, 10_000):
        add(amount=amount)
    add(amount=1, flags=(0,))
    add(amount=2, flags=(0,))
    add(amount=3, flags=(0,))
    add(amount=36, flags=(0,))
    add(amount=37, flags=(0,))
    add(amount=1, flags=(1,), quote='spl')
    add(amount=111, flags=(1,), quote='spl')
    # Sells: zero quote, user short, reserves short.
    add(amount=1, **SELL)
    add(amount=8, **SELL)
    add(amount=8, flags=(0,), **SELL)
    add(amount=10**15 + 1, **SELL)
    add(amount=2 * 10**14, flags=(0,), **dict(SELL, rqr=10**9))
    add(amount=10**12, quote='spl', curve_quote=10, **SELL)
    # Buyback split and fee counters.
    add(buyback_bps=0)
    add(buyback_bps=10_000)
    add(buyback_bps=3333, amount=987_654_321)
    add(buyback_bps=10_000, quote='spl', **SELL)
    add(cf=2**64 - 1, quote='spl', curve_quote=0)
    add(cf=2**64 - 1, flags=(1,), quote='spl', curve_quote=0)
    add(pf=2**64 - 10**6, flags=(1,), buyback_bps=0, quote='spl', curve_quote=0)
    add(pf=2**64 - 10**6, flags=(1,), buyback_bps=10_000, quote='spl', curve_quote=0)
    return cases


def random_cases(count=40, seed=6390):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        sell = rng.random() < 0.5
        base = dict(SELL) if sell else {}
        base.update(quote=rng.choice(['sol', 'spl']), flags=(rng.randrange(4),), creator=int(rng.random() < 0.8),
                    buyback_bps=rng.choice([0, 5000, 10_000, rng.randrange(10_001)]),
                    cf=rng.randrange(10**9), pf=rng.randrange(10**9),
                    amount=rng.choice([rng.randrange(1, 1000), rng.randrange(10**6, 5 * 10**10)]) if not sell
                    else rng.choice([rng.randrange(1, 100), rng.randrange(10**9, 10**14)]))
        cases.append(case(**base))
    return cases


class MultiHopHopCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'multi-hop-hop-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, item, answer, captured):
        if answer.startswith('error:'):
            self.assertIn(f'InstructionErrorCustom({answer[6:]})', str(captured['error']))
            self.assertEqual(captured['curve'], curve_data(item))
            return
        self.assertIsNone(captured['error'])
        vtr, vqr, rtr, rqr, cf, pf, base, output, buyback = map(int, answer.split(',')[1:])
        after = bytearray(curve_data(item))
        struct.pack_into('<QQQQ', after, 8, vtr, vqr, rtr, rqr)
        struct.pack_into('<QQ', after, 125, cf, pf)
        self.assertEqual(captured['curve'], bytes(after))
        flag = item['flags'][0]
        paid = buyback if flag & 1 else 0
        if item['buy']:
            self.assertEqual(captured['user_base'], base)
            self.assertEqual(captured['curve_quote'], item['amount'] - paid)
        else:
            self.assertEqual(captured['user_base'], -base)
            self.assertEqual(captured['curve_quote'], -output - paid)
        self.assertEqual(captured['recipient'], paid)

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        modelled = 0
        for index, (item, answer) in enumerate(zip(cases, answers)):
            if answer == 'unmodelled':
                continue
            modelled += 1
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item, index))
        return modelled

    def test_fixed_cases_match_captured_program(self):
        self.assertEqual(self.run_cases(fixed_cases()), len(fixed_cases()))

    def test_seeded_random_cases_match_captured_program(self):
        self.assertGreaterEqual(self.run_cases(random_cases()), 35)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {'ok', 'error:1', 'error:6005', 'error:6020', 'error:6022', 'error:6024',
                                    'error:6027', 'error:6041', 'error:6042', 'error:6094', 'error:6096',
                                    'error:6097', 'error:6106', 'error:6108'})

    def test_checker_rejects_shifted_base(self):
        # Negative control: a passing buy and sell must fail once the host's base is off by one.
        for item in (case(), case(amount=123_456_789, **SELL)):
            answer = self.host_answers([item])[0]
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            fields = answer.split(',')
            for delta in (-1, 1):
                fields_shifted = fields[:7] + [str(int(fields[7]) + delta)] + fields[8:]
                with self.subTest(buy=item['buy'], delta=delta), self.assertRaises(AssertionError):
                    self.assert_matches(item, ','.join(fields_shifted), captured)


if __name__ == '__main__':
    unittest.main()
