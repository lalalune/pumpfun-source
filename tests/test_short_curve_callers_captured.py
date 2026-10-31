"""Captured-program checks for non-trade instructions on short `BondingCurve` accounts.

Every case runs `migrate`, `migrate_v2`, `multi_hop_curve_swap`, a curve fee
sweep, a creator fee distribution, `get_minimum_distributable_fee`, or
`set_mayhem_virtual_params` from the captured `evidence/original/pump/deployed.so`
on LiteSVM, through the fixtures of that instruction's existing captured test,
on a short synthetic curve. The bytes also go to
`programs/pump/recovered/short_curve_callers_host.rs`, which predicts the
166-byte account the short one is read as, the rent top-up, and what the caller
does with the account, or the failure. The captured program then runs the
predicted account too, already funded with the top-up, and both runs must leave
the same error and effects, apart from the top-up. The amounts are not
re-modelled here: they come from the captured program on both sides. This shows
matching behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import collections
import hashlib
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.litesvm import LiteSVM as RealVm
from solders.pubkey import Pubkey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_creator_fee_distribution_captured as dist_base  # noqa: E402
import test_creator_fee_distribution_quote_captured as quote_base  # noqa: E402
import test_mayhem_virtual_params_captured as mayhem_base  # noqa: E402
import test_migrate_captured as migrate_base  # noqa: E402
import test_migrate_v2_captured as migrate2_base  # noqa: E402
import test_multi_hop_hop_captured as hop_base  # noqa: E402
import test_sweep_fees_captured as sweep_base  # noqa: E402

PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
              **sweep_base.ELF_SHA256, **mayhem_base.ELF_SHA256}
HOST_SOURCE = ROOT / 'programs/pump/recovered/short_curve_callers_host.rs'

SYSTEM = Pubkey.default()
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
SYSVAR = Pubkey.from_string('Sysvar1111111111111111111111111111111111111')
U64 = 2**64 - 1
LENGTHS = (49, 60, 80, 81, 82, 83, 100, 114, 115, 123, 124, 125, 140, 141, 165, 166, 200)
BOUNDARIES = (49, 80, 81, 82, 83, 114, 115, 123, 124, 125, 140, 141, 165, 166)
EDGES = (60, 114, 115, 141, 166)
BOOL_OFFSETS = (48, 81, 82, 123, 124)
# Tail fields a shape may or may not read. Each stays valid if it is read.
PROFILES = {
    'plain': (),
    'mayhem': ((81, b'\1'),),
    'cashback': ((82, b'\1'),),
    'quote': ((83, bytes([9]) * 32),),
    'creator_bps': ((115, struct.pack('<Q', 500)), (123, b'\1')),
    'holder': ((124, b'\1'),),
    'accrued': ((125, struct.pack('<QQ', 3_000_000, 7_000_000)),),
    'post_fields': ((141, b'\2' + struct.pack('<QQQ', 25_000_000_000, 5, 6)),),
}
# The last length that ignores a profile's fields and the first that reads them.
PROFILE_LENGTHS = {'plain': (), 'mayhem': (81, 82), 'cashback': (82, 83), 'quote': (114, 115), 'creator_bps': (123, 124),
                   'holder': (124, 125), 'accrued': (140, 141), 'post_fields': (165, 166)}


class SharedVm:
    """One VM per base test: a new "VM" only clears what the last case touched."""

    made = {}

    def __new__(cls):
        vm = cls.made.get(cls.owner)
        if vm is None:
            vm = cls.made[cls.owner] = object.__new__(cls)
            vm.real, vm.touched, vm.loaded = RealVm().with_transaction_history(0).with_sigverify(False), set(), set()
        for key in vm.touched:
            account = vm.real.get_account(key)
            if account is not None and not account.executable and account.owner not in (UPGRADEABLE, SYSVAR):
                vm.real.set_account(key, Account(0, b'', SYSTEM))
        vm.touched = set()
        return vm

    def with_transaction_history(self, _):
        return self

    def with_sigverify(self, _):
        return self

    def add_program_from_file(self, key, path):
        if key not in self.loaded:
            self.loaded.add(key)
            self.real.add_program_from_file(key, path)

    def add_program(self, key, data):
        if key not in self.loaded:
            self.loaded.add(key)
            self.real.add_program(key, data)

    def set_account(self, key, account):
        if account.owner == UPGRADEABLE:
            if key not in self.loaded:
                self.loaded.add(key)
                self.real.set_account(key, account)
            return
        self.touched.add(key)
        self.real.set_account(key, account)

    def set_clock(self, clock):
        self.real.set_clock(clock)

    def get_clock(self):
        return self.real.get_clock()

    def get_account(self, key):
        return self.real.get_account(key)

    def airdrop(self, key, lamports):
        self.touched.add(key)
        self.real.set_account(key, Account(lamports, b'', SYSTEM))

    def latest_blockhash(self):
        self.real.expire_blockhash()
        return self.real.latest_blockhash()

    def send_transaction(self, tx):
        self.touched.update(key for key in tx.message.account_keys if key != SYSTEM)
        return self.real.send_transaction(tx)


Route = collections.namedtuple('Route', 'base item host lamports_patch')
ROUTES = {
    'migrate': Route(migrate_base, migrate_base.case(), 'migrate', 'function'),
    'migrate_v1_open': Route(migrate_base, migrate_base.case(complete=0), 'migrate', 'function'),
    'migrate_v2': Route(migrate2_base, migrate2_base.case(), 'migrate_v2', 'function'),
    'migrate_v2_open': Route(migrate2_base, migrate2_base.case(complete=0), 'migrate_v2', 'function'),
    'migrate_v2_spl': Route(migrate2_base, migrate2_base.case(quote='spl'), 'migrate_v2', 'function'),
    'hop_buy': Route(hop_base, hop_base.case(), 'multi_hop', 'constant'),
    'hop_sell': Route(hop_base, hop_base.case(**hop_base.SELL), 'multi_hop', 'constant'),
    'hop_spl': Route(hop_base, hop_base.case(quote='spl'), 'multi_hop', 'constant'),
    'hop_complete': Route(hop_base, hop_base.case(complete=1), 'multi_hop', 'constant'),
    'sweep_creator': Route(sweep_base, sweep_base.case(bucket='creator'), 'sweep_creator', 'item'),
    'sweep_creator_spl': Route(sweep_base, sweep_base.case(bucket='creator', native=False), 'sweep_creator', 'item'),
    'sweep_protocol_spl': Route(sweep_base, sweep_base.case(native=False), 'sweep_protocol', 'item'),
    'distribute': Route(dist_base, dist_base.case(), 'distribute', None),
    'minimum': Route(dist_base, dist_base.case(op='minimum'), 'minimum', None),
    'distribute_v2': Route(quote_base, quote_base.case(), 'distribute_v2', None),
    'mayhem': Route(mayhem_base, mayhem_base.case(), 'mayhem_params', None),
    'mayhem_complete': Route(mayhem_base, mayhem_base.case(complete=True), 'mayhem_params', None),
    'mayhem_failing': Route(mayhem_base, mayhem_base.case(supply=2**63 - 1, irtr=0, vtr=U64, rqr=U64),
                            'mayhem_params', None),
}


def rent(length):
    return (length + 128) * 6960


def full_curve(route):
    base = ROUTES[route].base
    item = ROUTES[route].item
    return (base.curve_bytes if base is mayhem_base else base.curve_data)(item)


def curve_of(route, length, fields=(), complete=None):
    """The route's curve, with tail bytes set before it is cut to `length`."""
    data = bytearray(full_curve(route).ljust(max(length, 166), b'\0'))
    if complete is not None:
        data[48] = complete
    for offset, value in fields:
        data[offset:offset + len(value)] = value
    return bytes(data[:length])


def reserved(image):
    if image[83:115] != bytes(32):
        return 0
    return sum(struct.unpack_from('<Q', image, offset)[0] for offset in (32, 125, 133))


def run(route, curve, lamports):
    r = ROUTES[route]
    base, item = r.base, dict(r.item)
    SharedVm.owner = base.__name__
    patches = dict(LiteSVM=SharedVm)
    patches['curve_bytes' if base is mayhem_base else 'curve_data'] = lambda _: curve
    if r.lamports_patch == 'function':
        patches['curve_lamports'] = lambda _: lamports
    elif r.lamports_patch == 'item':
        item['lamports'] = lamports
    elif r.lamports_patch == 'constant':
        native = item['quote'] == 'sol'
        patches['CURVE_RENT'] = lamports - (item['rqr'] + item['cf'] + item['pf'] if native else 0)
    with mock.patch.multiple(base, **patches):
        result = base.run_captured(item)
    result.pop('logs', None)
    return result


def request(route, curve, lamports):
    return f'{ROUTES[route].host},{curve.hex()},{lamports}'


def add_route(cases, route):
    add = lambda curve, lamports: cases.append(dict(route=route, curve=curve, lamports=lamports))
    full = full_curve(route)
    room = reserved(full) + rent(166) + 10_000_000
    for length in LENGTHS:
        add(curve_of(route, length), reserved(full) + rent(length))
        add(curve_of(route, length), room)
    add(curve_of(route, 200), reserved(full) + rent(166))  # a long account needs its own length's rent
    for name, fields in PROFILES.items():
        for length in PROFILE_LENGTHS[name]:
            add(curve_of(route, length, fields), room + 10_000_000)
    for offset, length in zip(BOOL_OFFSETS * 2, (49, 82, 83, 124, 125, 48, 81, 82, 123, 124)):
        add(curve_of(route, length, ((offset, b'\2'),)), room)
    for length in EDGES:
        add(curve_of(route, length, complete=1 - full[48]), room)
        add(curve_of(route, length), reserved(full) // 2 or 1)  # no lamports at all would be no account
    for length in (140, 141, 166):
        add(curve_of(route, length, ((125, struct.pack('<Q', U64)),)), room)
        add(curve_of(route, length, ((133, struct.pack('<Q', U64)),)), room)


def fixed_cases():
    cases = []
    for route in ROUTES:
        add_route(cases, route)
    return cases


def random_cases(count=8, seed=736):
    rng = random.Random(seed)
    cases = []
    for route in ROUTES:
        full = full_curve(route)
        for _ in range(count):
            length = rng.choice((rng.randrange(0, 180), rng.choice(BOUNDARIES)))
            fields = [f for fields in PROFILES.values() for f in fields if rng.random() < 0.3]
            cases.append(dict(route=route, curve=curve_of(route, length, fields, rng.choice((None, None, 0, 1))),
                              lamports=reserved(full) + rent(rng.choice((length, 166))) + rng.randrange(10**7)))
    return cases


def wrong_discriminator(route, length):
    return b'\1' * 8 + curve_of(route, length)[8:]


class ShortCurveCallersCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'short-curve-callers-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(request(c['route'], c['curve'], c['lamports']) + '\n' for c in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def effects(self, route, result, top_up):
        """Drop the top-up from the effects a successful run reports."""
        result = dict(result)
        if 'delta' in result:
            result['delta'] = dict(result['delta'], payer=result['delta']['payer'] + top_up,
                                   curve=result['delta']['curve'] - top_up)
        if 'curve_quote' in result and route != 'hop_spl':
            result['curve_quote'] -= top_up
        return result

    def check(self, item, answer):
        route, curve, lamports = item['route'], item['curve'], item['lamports']
        host = ROUTES[route].host
        if not answer.startswith('ok'):
            short = run(route, curve, lamports)
            if answer == 'invalid':
                self.assertRegex(str(short['error']), 'InvalidAccountData|invalid_account_data')
            elif answer == 'bool':
                self.assertIn('BorshIoError', str(short['error']))
            else:
                self.assertIn(answer[6:], str(short['error']))
            return 'error'
        _, top_up, role, image = answer.split(',')
        top_up, image = int(top_up), bytes.fromhex(image)
        short = run(route, curve, lamports)
        if role == 'grows' and lamports < reserved(image):
            # The curve is under its reserves: nothing counts towards the rent,
            # and funding the full account would not change that.
            self.assertEqual(top_up, rent(len(image)))
            top_up = 0
        full = run(route, image, lamports + top_up)
        if role == 'stores' and len(curve) < 166 and full['error'] is None:
            self.assertIn('BorshIoError', str(short['error']))
            return 'stores'
        self.assertEqual(str(short['error']), str(full['error']))
        if short['error'] is not None:
            self.assertNotRegex(str(short['error']), 'InvalidAccountData|BorshIoError')
            return 'error'
        self.assertEqual(self.effects(route, short, top_up), self.effects(route, full, 0))
        if role == 'grows' and 'curve' in short:
            stored = short['curve'][1] if isinstance(short['curve'], tuple) else short['curve']
            self.assertEqual(len(stored), max(len(curve), 166))
        return 'ok'

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        outcomes = collections.Counter()
        for item, answer in zip(cases, answers):
            with self.subTest(route=item['route'], length=len(item['curve']), tail=item['curve'][48:].hex(),
                              lamports=item['lamports'], host=answer[:30]):
                outcomes[self.check(item, answer)] += 1
        return outcomes

    def test_fixed_cases_match_captured_program(self):
        outcomes = self.run_cases(fixed_cases())
        self.assertGreater(outcomes['ok'], 300)
        self.assertGreater(outcomes['stores'], 20)

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_wrong_discriminator_is_refused_at_every_length(self):
        cases = [dict(route=route, curve=wrong_discriminator(route, length), lamports=10**10)
                 for route in ('migrate', 'hop_buy', 'sweep_creator', 'distribute', 'mayhem') for length in (49, 124, 166)]
        self.assertEqual(self.run_cases(cases)['error'], len(cases))

    def test_set_mayhem_virtual_params_needs_the_full_account(self):
        # Negative control: the same curve stores at 166 bytes and fails one byte shorter.
        curve = full_curve('mayhem')
        self.assertIsNone(run('mayhem', curve, 0)['error'])
        self.assertIn('BorshIoError', str(run('mayhem', curve[:165], 0)['error']))

    def test_handler_error_beats_the_failed_store(self):
        curve = full_curve('mayhem_failing')
        code = run('mayhem_failing', curve, 0)['error']
        self.assertIsNotNone(code)
        self.assertEqual(run('mayhem_failing', curve[:150], 0)['error'], code)

    def test_top_up_of_a_long_account_is_paid_to_the_last_lamport(self):
        # The twin runs cannot see this one: both are long, so both would pay.
        curve, lamports = curve_of('sweep_creator', 200), reserved(full_curve('sweep_creator')) + rent(166)
        answer = self.host_answers([dict(route='sweep_creator', curve=curve, lamports=lamports)])[0]
        top_up = int(answer.split(',')[1])
        self.assertEqual(top_up, rent(200) - rent(166))
        payer = lambda balance: run('sweep_creator', curve, balance)['delta']['payer']
        self.assertEqual(payer(lamports), payer(lamports + top_up) - top_up)
        self.assertEqual(payer(lamports + top_up), payer(lamports + top_up + 1))
        self.assertEqual(payer(lamports + top_up - 1), payer(lamports + top_up) - 1)

    def test_migrate_grows_the_account_at_the_payers_cost(self):
        curve, lamports = full_curve('migrate')[:124], reserved(full_curve('migrate')) + rent(124)
        answer = self.host_answers([dict(route='migrate', curve=curve, lamports=lamports)])[0]
        self.assertEqual(int(answer.split(',')[1]), rent(166) - rent(124))
        stored_lamports, stored = run('migrate', curve, lamports)['curve']
        self.assertEqual(len(stored), 166)
        self.assertGreater(stored_lamports, 0)


if __name__ == '__main__':
    unittest.main()
