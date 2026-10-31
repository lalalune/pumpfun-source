"""Captured-program checks for the account admission of the v3 trades.

Every case runs `sell_v3`, `buy_v3` or `buy_exact_quote_in_v3` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token,
Token-2022 and Associated Token programs, on native, wSOL, SPL and Token-2022
quote routes. One account set is the expected one from
`tests/test_v3_trade_accounting_captured.py`. A case changes it by one, two or
three faults: wrong address, owner, data, mutability, program or trade gate.

The same faults go to `programs/pump/recovered/v3_account_admission_host.rs`,
which names the first stop. When the model says the trade passes, the captured
run must match a twin without the account faults: same error, or the same curve
bytes and events. Amounts are not modelled here; they belong to the accounting
models. This shows matching behavior on these inputs only; it is not a
byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import itertools
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
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v3_trade_accounting_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = {
    ROOT / 'evidence/original/pump/deployed.so': '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    ROOT / 'evidence/dependencies/spl_token/deployed.so': '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ROOT / 'evidence/dependencies/spl_token_2022/deployed.so': '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ROOT / 'evidence/dependencies/associated_token/deployed.so': '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/v3_account_admission_host.rs'

PAYER = Keypair.from_seed(bytes([239]) * 32)
ALIEN = Pubkey.from_bytes(bytes([62]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([63]) * 32)
USER = base.USER.pubkey()
SYSTEM = base.SYSTEM
IXS = {'sell_v3': 'sell', 'buy_v3': 'buy', 'buy_exact_quote_in_v3': 'exact'}
QUOTES = ('sol', 'wsol', 'spl', 't22')
SLOTS = ('global', 'base_mint', 'quote_mint', 'base_token_program', 'quote_token_program', 'bonding_curve',
         'associated_base_bonding_curve', 'associated_quote_bonding_curve', 'user', 'associated_base_user',
         'associated_quote_user', 'user_volume_accumulator', 'fee_config', 'buyback_fee_recipient', 'system_program',
         'event_authority', 'program')
BUYBACK_LIST = 741  # eight keys in Global, the last at entry 7
DEFAULT_ARGS = {'sell_v3': (10**12, 0), 'buy_v3': (10**12, 10**15), 'buy_exact_quote_in_v3': (10**9, 1)}


def wrong(slot):
    return Pubkey.from_bytes(bytes([100 + SLOTS.index(slot)]) * 32)


class Fixture:
    """The expected accounts of one trade; faults edit them before the run."""

    def __init__(self, ix, quote, **over):
        self.ix, self.quote = ix, quote
        c = base.default_case(quote=quote, buy=int(ix != 'sell_v3'), **over)
        r = self.roles = base.roles(c)
        self.accounts = {
            base.GLOBAL: Account(10**9, base.global_bytes(c), base.PUMP),
            base.FEE_CONFIG: Account(10**9, base.fee_config_bytes(c), base.FEES),
            USER: Account(10**12, b'', SYSTEM),
            PAYER.pubkey(): Account(10**12, b'', SYSTEM),
            base.BUYBACK: Account(10**9, b'', SYSTEM),
            base.BASE: Account(10**9, base.mint_bytes(c['mint_supply'], 6), base.TOKEN),
            r['quote_mint']: Account(10**9, base.mint_bytes(10**18, 9 if r['native'] else 6, c['tf']), r['program']),
            base.CURVE: Account(c['curve_lamports'], base.curve_bytes(c, r['curve_field']), base.PUMP),
            r['curve_base']: Account(base.TOKEN_RENT, base.token_bytes(base.BASE, base.CURVE, c['curve_base']), base.TOKEN),
            r['user_base']: Account(base.TOKEN_RENT, base.token_bytes(base.BASE, USER, c['user_base']), base.TOKEN),
        }
        if not r['native']:
            for key, owner, amount in ((r['curve_quote'], base.CURVE, c['rqr']), (r['user_quote'], USER, c['user_quote']),
                                       (r['recipient'], base.BUYBACK, 0)):
                self.accounts[key] = Account(base.TOKEN_RENT, base.token_bytes(r['quote_mint'], owner, amount), r['program'])
        accumulator = bytearray(137)
        accumulator[:8] = base.ACCOUNT_DISC['UserVolumeAccumulator']
        accumulator[8:40] = bytes(USER)
        self.accounts[base.USER_VOLUME] = Account(base.rent(137), bytes(accumulator), base.PUMP)
        self.names = {
            'global': base.GLOBAL, 'base_mint': base.BASE, 'quote_mint': r['quote_mint'], 'base_token_program': base.TOKEN,
            'quote_token_program': r['program'], 'bonding_curve': base.CURVE,
            'associated_base_bonding_curve': r['curve_base'], 'associated_quote_bonding_curve': r['curve_quote'],
            'user': USER, 'associated_base_user': r['user_base'], 'associated_quote_user': r['user_quote'],
            'user_volume_accumulator': base.USER_VOLUME, 'fee_config': base.FEE_CONFIG,
            'buyback_fee_recipient': r['recipient'], 'system_program': SYSTEM, 'event_authority': base.EVENT_AUTHORITY,
            'program': base.PUMP,
        }
        self.read_only, self.unsigned = set(), False
        self.args = DEFAULT_ARGS[ix]

    def held(self, slot):
        return self.accounts.get(self.names[slot])

    def put(self, slot, data=None, owner=None):
        account = self.held(slot)
        self.accounts[self.names[slot]] = Account(account.lamports, bytes(account.data) if data is None else data,
                                                  account.owner if owner is None else owner)

    def token_field(self, slot, offset, key):
        data = bytearray(self.held(slot).data)
        data[offset:offset + 32] = bytes(key)
        self.put(slot, data=bytes(data))


def slot_fault(slot, kind):
    def apply(fx):
        if kind == 'readonly':
            fx.read_only.add(slot)
        elif fx.held(slot) is None and kind != 'key':
            return  # a native quote account does not exist to fault
        elif kind == 'key':
            fx.accounts[wrong(slot)] = fx.held(slot) or Account(10**9, b'', SYSTEM)
            fx.names[slot] = wrong(slot)
        elif kind == 'owner':
            fx.put(slot, owner=ALIEN)
        elif kind == 'missing':
            del fx.accounts[fx.names[slot]]
        elif kind == 'disc':
            fx.put(slot, data=bytes([fx.held(slot).data[0] ^ 0xff]) + bytes(fx.held(slot).data)[1:])
        elif kind == 'short':
            fx.put(slot, data=bytes(fx.held(slot).data)[:4])
        elif kind == 'mint':
            fx.token_field(slot, 0, OTHER_MINT)
        elif kind == 'auth':
            fx.token_field(slot, 32, ALIEN)
    return apply


def resize(slot, size):
    def apply(fx):
        fx.put(slot, data=bytes(fx.held(slot).data)[:size].ljust(size, b'\0'))
    return apply


def accumulator_absent(lamports, data=b''):
    def apply(fx):
        fx.accounts[base.USER_VOLUME] = Account(lamports, data, SYSTEM)
    return apply


def accumulator_user(fx):
    fx.put('user_volume_accumulator', data=bytes(fx.held('user_volume_accumulator').data[:8]) + bytes(ALIEN)
           + bytes(fx.held('user_volume_accumulator').data[40:]))


def fee_config_bump(fx):
    data = bytearray(fx.held('fee_config').data)
    data[8] ^= 1
    fx.put('fee_config', data=bytes(data))


def other_quote_program(moved):
    def apply(fx):
        program = base.TOKEN if fx.names['quote_token_program'] == base.TOKEN22 else base.TOKEN22
        fx.names['quote_token_program'] = program
        if moved:
            fx.names['associated_quote_bonding_curve'] = base.ata(base.CURVE, fx.names['quote_mint'], program)
    return apply


def program_key(slot, key):
    def apply(fx):
        fx.names[slot] = key
    return apply


def plain_account(slot):
    def apply(fx):
        fx.accounts[wrong(slot)] = Account(10**9, b'', SYSTEM)
        fx.names[slot] = wrong(slot)
    return apply


def unsigned(fx):
    fx.unsigned = True


def wsol_mint(fx):
    if fx.quote in ('spl', 't22'):
        fx.names['quote_mint'] = base.WSOL
        fx.accounts[base.WSOL] = Account(10**9, base.mint_bytes(10**18, 9), base.TOKEN)


def recipient_owner(owner, entry=None):
    """Pay the buyback to `owner`, entered at `entry` of the Global list."""
    def apply(fx):
        if entry is not None and fx.held('global') and len(fx.held('global').data) > 997:
            data = bytearray(fx.held('global').data)
            data[BUYBACK_LIST + 32 * entry:BUYBACK_LIST + 32 * (entry + 1)] = bytes(owner)
            fx.put('global', data=bytes(data))
        if fx.roles['native']:
            fx.names['buyback_fee_recipient'] = owner
            if owner != SYSTEM:
                fx.accounts.setdefault(owner, Account(10**9, b'', SYSTEM))
            return
        mint, program = fx.roles['quote_mint'], fx.roles['program']
        key = base.ata(owner, mint, program)
        fx.accounts[key] = Account(base.TOKEN_RENT, base.token_bytes(mint, owner, 0), program)
        fx.names['buyback_fee_recipient'] = key
    return apply


def trade_args(sell, buy, exact):
    def apply(fx):
        fx.args = {'sell_v3': sell, 'buy_v3': buy, 'buy_exact_quote_in_v3': exact}[fx.ix]
    return apply


def no_change(fx):
    pass


FAULTS = {}  # name -> (fixture overrides, edit)


def fault(name, edit=no_change, **over):
    FAULTS[name] = (over, edit)


for slot_name, kinds in {
    'global': 'key owner missing disc short',
    'base_mint': 'key owner missing short',
    'quote_mint': 'key owner missing short',
    'bonding_curve': 'key owner missing disc short readonly',
    'associated_base_bonding_curve': 'key owner missing short readonly mint auth',
    'associated_quote_bonding_curve': 'key owner missing short readonly mint auth',
    'associated_base_user': 'key owner missing short readonly mint auth',
    'associated_quote_user': 'key owner missing short readonly mint auth',
    'user_volume_accumulator': 'key owner disc readonly',
    'fee_config': 'key owner missing disc short',
    'buyback_fee_recipient': 'key owner missing short readonly mint auth',
}.items():
    for fault_kind in kinds.split():
        fault(f'{slot_name}.{fault_kind}', slot_fault(slot_name, fault_kind))
fault('user.unsigned', unsigned)
fault('uva.len8', resize('user_volume_accumulator', 8))
fault('uva.len136', resize('user_volume_accumulator', 136))
fault('uva.short', resize('user_volume_accumulator', 4))
fault('uva.absent', accumulator_absent(0))
fault('uva.funded', accumulator_absent(10**7))
fault('uva.sysdata', accumulator_absent(10**9, b'\1\2'))
fault('uva.user', accumulator_user)
fault('fee_config.bump', fee_config_bump)
fault('fee_config.len100', resize('fee_config', 100))
fault('base_token_program.t22', program_key('base_token_program', base.TOKEN22))
fault('base_token_program.ata', program_key('base_token_program', base.ATA))
fault('base_token_program.plain', plain_account('base_token_program'))
fault('quote_token_program.other', other_quote_program(False))
fault('quote_token_program.moved', other_quote_program(True))
fault('quote_token_program.ata', program_key('quote_token_program', base.ATA))
fault('quote_token_program.plain', plain_account('quote_token_program'))
fault('quote_mint.wsol', wsol_mint)
fault('system_program.ata', program_key('system_program', base.ATA))
fault('system_program.plain', plain_account('system_program'))
fault('event_authority.key', slot_fault('event_authority', 'key'))
fault('program.token', program_key('program', base.TOKEN))
fault('program.plain', plain_account('program'))
fault('buyback_fee_recipient.listed', recipient_owner(ALIEN, 7))
fault('buyback_fee_recipient.unlisted', recipient_owner(ALIEN))
fault('buyback_fee_recipient.zero', recipient_owner(SYSTEM))
fault('h.complete', complete=1)
fault('h.cashback', cashback=1)
fault('h.zero', trade_args((0, 0), (0, 10**15), (10**9, 0)))
fault('h.zero_quote', trade_args(DEFAULT_ARGS['sell_v3'], DEFAULT_ARGS['buy_v3'], (0, 1)))
fault('h.over', trade_args((10**14, 0), DEFAULT_ARGS['buy_v3'], DEFAULT_ARGS['buy_exact_quote_in_v3']), user_base=1)
fault('h.mayhem_over', trade_args(DEFAULT_ARGS['sell_v3'], (8 * 10**14, 10**16), DEFAULT_ARGS['buy_exact_quote_in_v3']), mayhem=1)
fault('h.overflow', rqr=2**64 - 1, protocol_fees=1, curve_lamports=10**10)
fault('h.limit', trade_args((10**12, 10**15), (10**12, 0), (10**9, 10**15)))
fault('h.empty_tiers', tiers=[])
fault('fee_config.len2511', resize('fee_config', 2511))

# Trade-argument faults overwrite each other, so a case holds at most one.
ARGUMENT_FAULTS = {'h.zero', 'h.zero_quote', 'h.over', 'h.limit', 'h.mayhem_over'}
TOKEN_SLOTS = {'associated_base_bonding_curve', 'associated_quote_bonding_curve', 'associated_base_user',
               'associated_quote_user', 'buyback_fee_recipient'}
SHARED_KINDS = {'key', 'owner', 'readonly', 'mint', 'auth', 'short', 'disc'}


def split(name):
    slot, kind = name.split('.')
    if slot == 'uva':
        slot = 'user_volume_accumulator'
    if name == 'quote_token_program.moved':
        slot = 'associated_quote_bonding_curve'
    return slot, kind


def compatible(a, b):
    """Whether two faults describe one account set."""
    if a in ARGUMENT_FAULTS and b in ARGUMENT_FAULTS:
        return False
    if a.startswith('quote_token_program.') and b.startswith('quote_token_program.'):
        return False  # two swaps cancel out
    (slot_a, kind_a), (slot_b, kind_b) = split(a), split(b)
    if slot_a != slot_b or slot_a == 'h':
        return True
    if not {kind_a, kind_b} <= SHARED_KINDS:
        return False
    if slot_a == 'user_volume_accumulator':
        return True
    return slot_a in TOKEN_SLOTS and not ('short' in (kind_a, kind_b) and {kind_a, kind_b} & {'mint', 'auth'})


def build(ix, quote, names, context=()):
    over = dict(context)
    for name in names:
        over.update(FAULTS[name][0])
    fx = Fixture(ix, quote, **over)
    for name in names:
        FAULTS[name][1](fx)
    return fx


class Program:
    """One LiteSVM kept across cases; a run costs a few milliseconds."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        for key, path in ((base.PUMP, base.PUMP_ELF), (base.TOKEN, base.TOKEN_ELF), (base.TOKEN22, base.TOKEN22_ELF),
                          (base.ATA, base.ATA_ELF)):
            self.vm.add_program_from_file(key, path)
        self.vm.set_clock(Clock(100, base.TIMESTAMP, base.EPOCH, base.EPOCH, base.TIMESTAMP))
        self.seen = set()

    def run(self, fx):
        vm = self.vm
        for key in self.seen - set(fx.accounts):
            vm.set_account(key, Account(0, b'', SYSTEM))
        for key, account in fx.accounts.items():
            vm.set_account(key, account)
        self.seen |= set(fx.accounts)
        ix = base.IX[fx.ix]
        metas = [AccountMeta(fx.names[a['name']], bool(a.get('signer')) and not (a['name'] == 'user' and fx.unsigned),
                             bool(a.get('writable')) and a['name'] not in fx.read_only) for a in ix['accounts']]
        data = bytes(ix['discriminator']) + struct.pack('<QQ', *fx.args)
        if fx.ix != 'sell_v3':
            data += bytes([0])
        payer = PAYER if fx.unsigned else base.USER
        vm.expire_blockhash()
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(base.PUMP, data, metas)],
                                               payer.pubkey(), [payer], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            if code:
                return dict(error=int(code.group(1)))
            words = re.sub(r'[^A-Za-z]+', ' ', text).split()
            return dict(error=words[-1] if words else text)
        curve = vm.get_account(base.CURVE)
        events = [line for line in result.logs() if line.startswith('Program data: ')]
        return dict(error=None, curve=bytes(curve.data) if curve else None, events=events)


def host_line(ix, quote, names):
    tokens = [IXS[ix], 'native' if quote == 'sol' else 'token']
    for name in names:
        if name in ('h.limit', 'h.empty_tiers', 'fee_config.len2511'):
            continue  # pricing faults: the twin carries them
        if name == 'h.zero_quote' and ix != 'buy_exact_quote_in_v3':
            continue
        if name == 'h.over' and ix != 'sell_v3':
            continue
        if name == 'h.mayhem_over':
            if ix == 'buy_v3':
                tokens.append('h.over')
            continue
        if name == 'quote_mint.wsol':
            if quote in ('spl', 't22'):
                tokens.append('quote_mint.key')
            continue
        tokens.append(name)
    return ' '.join(tokens)


def twin_names(names):
    return tuple(sorted(n for n in names if n.startswith('h.') or n == 'fee_config.len2511'))


def verdict(answer, captured, twin):
    """Why a captured run disagrees with the model's answer, or None."""
    if answer == 'pass' or answer.startswith('transfer:'):
        if twin['error'] is not None:
            return None if captured['error'] == twin['error'] else f"twin failed with {twin['error']}"
        if answer != 'pass':
            return None if captured['error'] == int(answer[9:]) else 'transfer code'
        if captured['error'] is not None:
            return 'expected a pass'
        same = captured['curve'] == twin['curve'] and captured['events'] == twin['events']
        return None if same else 'differs from the twin'
    want = 'InvalidAccountData' if answer == 'data' else int(answer[6:])
    return None if captured['error'] == want else f'expected {want}'


PAIR_ROUTES = (('sell_v3', 'spl'), ('buy_v3', 'sol'), ('buy_exact_quote_in_v3', 't22'))


def single_cases():
    return [(ix, q, (name,), ()) for ix in IXS for q in QUOTES for name in FAULTS]


def context_cases():
    # The handlers' admission does not depend on who pays no fee. A whitelisted
    # Mayhem curve resyncs its reserves, which is pricing, so it stays out.
    return [(ix, q, (name,), context) for context in ((('mayhem', 1),), (('whitelisted', 1),))
            for ix in IXS for q in QUOTES for name in FAULTS
            if not (FAULTS[name][0].get('mayhem') and context[0][0] == 'whitelisted')]


def pair_cases():
    pairs = [p for p in itertools.combinations(FAULTS, 2) if compatible(*p)]
    return [(ix, q, pair, ()) for ix, q in PAIR_ROUTES for pair in pairs]


def triple_cases(count=1500, seed=31031):
    rng = random.Random(seed)
    names, out = list(FAULTS), []
    while len(out) < count:
        picks = tuple(rng.sample(names, 3))
        if all(compatible(a, b) for a, b in itertools.combinations(picks, 2)):
            out.append((rng.choice(list(IXS)), rng.choice(QUOTES), picks, ()))
    return out


class V3AccountAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'v3-account-admission-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)], check=True)
        cls.program = Program()
        cls.twins = {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def answers(self, cases):
        text = ''.join(host_line(ix, q, names) + '\n' for ix, q, names, _ in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(len(out), len(cases))
        return out

    def twin(self, ix, quote, names, context):
        key = (ix, quote, twin_names(names), context)
        if key not in self.twins:
            self.twins[key] = self.program.run(build(ix, quote, key[2], context))
        return self.twins[key]

    def compare(self, cases):
        wrong_cases = []
        for case, answer in zip(cases, self.answers(cases)):
            ix, quote, names, context = case
            captured = self.program.run(build(ix, quote, names, context))
            reason = verdict(answer, captured, self.twin(*case))
            if reason:
                wrong_cases.append((case, answer, captured['error'], reason))
        self.assertEqual(wrong_cases[:20], [], f'{len(wrong_cases)} of {len(cases)} differ')

    def test_expected_accounts_pass(self):
        cases = [(ix, q, (), ()) for ix in IXS for q in QUOTES]
        self.assertEqual(set(self.answers(cases)), {'pass'})
        for ix, q, _, _ in cases:
            self.assertIsNone(self.program.run(build(ix, q, ()))['error'], (ix, q))

    def test_one_fault_matches_captured_program(self):
        self.compare(single_cases())

    def test_one_fault_on_mayhem_and_whitelisted_trades(self):
        self.compare(context_cases())

    def test_fault_pairs_keep_the_captured_order(self):
        self.compare(pair_cases())

    def test_seeded_fault_triples_match_captured_program(self):
        self.compare(triple_cases())

    def test_checker_rejects_a_different_outcome(self):
        # Negative control: each kind of answer fails on another captured outcome.
        passed = dict(error=None, curve=b'a', events=['e'])
        self.assertIsNone(verdict('pass', passed, passed))
        self.assertTrue(verdict('pass', dict(passed, curve=b'b'), passed))
        self.assertTrue(verdict('pass', dict(error=6005), passed))
        self.assertTrue(verdict('error:6005', dict(error=6004), passed))
        self.assertTrue(verdict('data', dict(error=3003), passed))
        self.assertTrue(verdict('transfer:3', passed, passed))
        self.assertTrue(verdict('pass', dict(error=None, curve=b'a', events=['e']), dict(error=6003)))

    def test_cases_cover_every_stop(self):
        answers = set(self.answers(single_cases()))
        self.assertEqual(answers, {
            'pass', 'data', 'transfer:3', 'transfer:4', 'error:0', 'error:2000', 'error:2006', 'error:2009', 'error:2014',
            'error:2015', 'error:2019', 'error:2023', 'error:3001', 'error:3002', 'error:3003', 'error:3007', 'error:3008',
            'error:3010', 'error:3012', 'error:6004', 'error:6005', 'error:6010', 'error:6020', 'error:6021', 'error:6022',
            'error:6023', 'error:6024', 'error:6041', 'error:6057', 'error:6062', 'error:6094',
        })


if __name__ == '__main__':
    unittest.main()
