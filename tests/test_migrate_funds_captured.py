"""Captured-program checks for the funding rules of Pump `migrate`.

The fixture of `tests/test_migrate_captured.py`, with what it keeps fixed set
free: curve account length, curve lamports, the fee buckets, the base balance
and a `pool_migration_fee` below 10,000,000. Every case runs on the captured
`evidence/original/pump/deployed.so` with the no-op pump_amm of that test, and
on `programs/pump/recovered/migrate_funds_host.rs`. The error, the pump_amm
CPIs, the event, the curve and the user's lamports must agree. Account state
is synthetic (IDL layouts). This shows matching behavior on these inputs only;
it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_migrate_captured as base

ELF_SHA256 = {base.PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = base.ROOT / 'programs/pump/recovered/migrate_funds_host.rs'
USER = base.USER.pubkey()
USER_LAMPORTS = 10**12
TX_FEE = 5_000
RENT_166 = 2_046_240
STATIC = {base.PUMP, base.PUMP_AMM, base.TOKEN, base.TOKEN22, base.ATA, base.SYSTEM, base.RENT}
FIXED_OK = 205
FIXTURE = dict(size=166, cf=0, pf=0, base_balance=0)
original_curve_data, original_token_data, original_lamports, RealVm = base.curve_data, base.token_data, base.curve_lamports, base.LiteSVM


def case(**changes):
    extra = {k: changes.pop(k) for k in list(changes) if k in FIXTURE}
    return {**base.case(**changes), **FIXTURE, **extra}


def curve_lamports(item):
    return original_lamports(item) + (item['cf'] + item['pf'] if item['lamports'] is None else 0)


def curve_data(item):
    data = bytearray(original_curve_data(item))
    struct.pack_into('<QQ', data, 125, item['cf'], item['pf'])
    return bytes(data[:item['size']]).ljust(item['size'], b'\0')


class SharedVm:
    """One LiteSVM for all cases, so the programs load once."""
    made = None

    def __new__(cls):
        if cls.made is None:
            cls.made = super().__new__(cls)
            cls.made.vm = RealVm().with_transaction_history(0)
            cls.made.loaded = set()
        return cls.made

    def __init__(self):
        self.vm.expire_blockhash()
        for key in set(base.ACCOUNTS.values()) - STATIC:
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))

    def __getattr__(self, name):
        return getattr(self.vm, name)

    def with_transaction_history(self, _):
        return self

    def set_account(self, key, account):
        if account.executable or account.owner == base.UPGRADEABLE:
            if key in self.loaded:
                return
            self.loaded.add(key)
        self.vm.set_account(key, account)

    def add_program(self, key, data):
        if key not in self.loaded:
            self.loaded.add(key)
            self.vm.add_program(key, data)


def run_captured(item):
    def token_data(mint, owner, amount):
        return original_token_data(mint, owner, item['base_balance'] if owner == base.CURVE and mint == base.MINT else amount)
    with mock.patch.multiple(base, LiteSVM=SharedVm, curve_data=curve_data, token_data=token_data, curve_lamports=curve_lamports):
        got = base.run_captured(item)
    user = SharedVm.made.vm.get_account(USER)
    return dict(got, user=user.lamports - USER_LAMPORTS + TX_FEE)


def host_line(item):
    return (f"{base.host_line(item)};{item['size']},{curve_lamports(item)},{item['cf']},{item['pf']},{item['base_balance']}")


def create_pool(quote, base_amount, flags, creator=True):
    return (base.AMM_IX['create_pool'] + struct.pack('<HQQ', 0, base_amount, quote) + (bytes(base.CREATOR) if creator == 1 else bytes(32))
            + struct.pack('<BBQBB', *flags))


def as_read(item):
    """The curve bytes the program writes back: what it could not read is zero."""
    size = item['size']
    read = dict(item)
    if size < 82:
        read['mayhem'] = 0
    if size < 83:
        read['cashback'] = 0
    if size < 115:
        read['quote_set'] = 0
    if size < 124:
        read.update(cfb=0, can_edit=0)
    if size < 125:
        read['holder'] = 0
    if size < 141:
        read.update(cf=0, pf=0)
    if size < 166:
        read['pcqi'] = 0
    data = bytearray(curve_data(dict(read, size=max(size, 166))))
    if size < 81:
        data[49:81] = bytes(32)
    return data


def unchanged(item, got):
    return got['curve'] == (curve_lamports(item), curve_data(item)) and got['events'] == [] and got['user'] == 0


def check(item, answer, got):
    """List mismatches between one host answer and one captured run."""
    bad = []
    error = str(got['error'])
    if answer in ('borsh', 'invalid-data', 'lamports', 'below-rent') or answer.startswith(('error:', 'after-pool:')):
        wanted = {'borsh': 'BorshIoError', 'invalid-data': 'InvalidAccountData', 'lamports': 'ArithmeticOverflow',
                  'below-rent': 'InsufficientFundsForRent'}.get(answer)
        cpis = 0
        if wanted is None:
            parts = answer.split(':')
            wanted = f'InstructionErrorCustom({parts[1]})'
            if parts[0] == 'after-pool':
                cpis = 1 + int(parts[3])
                sent = struct.unpack_from('<Q', got['cpis'][0], 10)[0] if got['cpis'] else None
                if sent != int(parts[2]):
                    bad.append(f'create_pool base {sent} != {parts[2]}')
        if wanted not in error:
            bad.append(f'error {error} != {answer}')
        if len(got['cpis']) != cpis and answer != 'below-rent':
            bad.append(f"cpis {len(got['cpis'])} != {cpis}")
        # The runtime refuses a below-rent transaction once the program has run,
        # so its logs stay but nothing else does.
        settled = dict(got, events=[]) if answer == 'below-rent' else got
        if not unchanged(item, settled):
            bad.append('failed transaction changed the curve or the user')
        return bad
    if got['error'] is not None:
        return [f'captured failed with {error}']
    fields = answer.split(',')
    if fields[0] == 'noop':
        if got['cpis'] or got['events']:
            bad.append('noop sent something')
        after = as_read(item)
        expected = max(curve_lamports(item), curve_lamports(item) + int(fields[1]))
        if got['curve'] != (expected, bytes(after)):
            bad.append(f"noop curve {got['curve'][0]} != {expected}")
        if got['user'] != -int(fields[1]):
            bad.append('noop user')
        return bad
    quote, mayhem, cashback, cfb, can_edit, holder, boost, lamports, base_amount, paid, creator = map(int, fields[1:])
    want = [create_pool(quote, base_amount, (mayhem, cashback, cfb, can_edit, holder), creator)] + ([base.AMM_IX['init_boost']] if boost else [])
    if got['cpis'] != want:
        bad.append('create_pool or init_boost bytes')
    after = as_read(item)
    struct.pack_into('<QQQQ', after, 8, 0, 0, 0, 0)
    if got['curve'] != ((lamports, bytes(after)) if lamports else None):
        bad.append(f"curve {got['curve'] and got['curve'][0]} != {lamports}")
    if got['user'] != -paid:
        bad.append(f"user {got['user']} != {-paid}")
    if len(got['events']) != 1 or struct.unpack_from('<QQQ', got['events'][0], 72) != (base_amount, quote, item['fee']):
        bad.append('event')
    return bad


def cases():
    out = [case()]
    add = lambda **k: out.append(case(**k))
    zero = dict(vtr=0, vqr=0, rtr=0, rqr=0)
    flags = dict(cashback=1, cfb=123, can_edit=1, holder=1, pcqi=1_000)
    for fee in (0, 1, 7_000_000, 8_157_119, 8_157_120, 8_157_121, 9_999_999, 10_000_000):
        add(fee=fee)
        add(fee=fee, faults='W')
        add(fee=fee, complete=0)
        add(fee=fee, **zero)
        add(fee=fee, rqr=fee, pcqi=0)
        add(fee=fee, rqr=fee - 1 if fee else 0)
    # The fee is taken from the lamports before the quote is worked out.
    add(fee=85_005_359_056, slack=0, lamports=1)
    add(fee=8_157_120, rqr=8_157_119, lamports=1)
    add(fee=8_157_119, rqr=8_157_118, lamports=1)
    add(fee=10**7, rqr=base.U64 - 1, pcqi=5, lamports=1)
    add(fee=10**7, rqr=base.U64 - 1, pcqi=5, lamports=10**12)
    add(fee=10**7, rqr=5, pcqi=0, lamports=10**12)
    add(fee=8_157_119, rqr=5, pcqi=0, lamports=10**12)
    for slack in (0, 1, 1_000, 2_046_239, 2_046_240, 2_046_241, 3_000_000):
        add(slack=slack)
        add(slack=slack, remaining=2)
        add(slack=slack, mayhem=1)
        add(slack=slack, pcqi=1_000)
        add(slack=slack, pcqi=2_046_240)
        add(slack=slack, pcqi=1)
        add(slack=slack, cf=9, pf=11)
        add(slack=slack, complete=0)
        if slack:
            add(slack=slack, **zero)
        add(slack=slack, faults='P')
        add(slack=slack, cf=9, pf=11, pcqi=1_000)
    for lamports in (1, 10**6, 85_000_000_000, 85_005_359_055, 85_005_359_056, 85_005_359_057, 85_007_405_295, 85_007_405_296, 85_007_405_297):
        add(lamports=lamports, slack=0)
        add(lamports=lamports, slack=0, pcqi=20_000_000)
        add(lamports=lamports, slack=0, complete=0)
        add(lamports=lamports, slack=0, base_balance=5)
    add(rqr=base.U64, lamports=1, cf=1)
    add(rqr=1, lamports=1, cf=base.U64, pf=1)
    add(rqr=1, lamports=1, cf=base.U64, pf=1, complete=0)
    add(rqr=1, lamports=1, cf=base.U64, pf=1, faults='W')
    add(rqr=1, lamports=1, pf=base.U64, cf=1, **dict(vtr=0, vqr=0, rtr=0))
    for size in (8, 40, 48, 49, 50, 80, 81, 82, 83, 84, 100, 114, 115, 116, 122, 123, 124, 125, 126, 132, 133, 140, 141, 149, 150, 157, 158, 165, 166, 167, 300):
        add(size=size)
        add(size=size, slack=10**9)
        add(size=size, mayhem=1, **flags)
        add(size=size, cf=7, pf=9, **flags)
        add(size=size, quote_set=1)
        add(size=size, complete=0)
        add(size=size, **zero)
        add(size=size, remaining=2, config=(949, 1, 1))
        add(size=size, complete=2)
    for balance in (1, 1_000, 10**15, base.U64):
        add(base_balance=balance)
        add(base_balance=balance, remaining=2)
        add(base_balance=balance, config=(949, 1, 1))
        add(base_balance=balance, config=(949, 1, 1), remaining=1)
        add(base_balance=balance, mayhem=1)
        add(base_balance=balance, fee=8_157_119)
        add(base_balance=balance, rqr=1)
        add(base_balance=balance, complete=0)
        add(base_balance=balance, **zero)
        add(base_balance=balance, slack=0)
    return out


def random_cases(count=300, seed=20261031):
    rng = random.Random(seed)
    out = []
    for _ in range(count):
        fee = rng.choice([0, 8_157_119, 8_157_120, 10_000_000, rng.randrange(10**7, 10**10)])
        out.append(case(fee=fee, rqr=rng.choice([fee, fee + 1, rng.randrange(10**7, 10**12)]), pcqi=rng.choice([0, 0, rng.randrange(10**9)]),
                        slack=rng.choice([1, 10**6, RENT_166, 10**7]), cf=rng.choice([0, rng.randrange(10**6)]), pf=rng.choice([0, rng.randrange(10**6)]),
                        size=rng.choice([49, 81, 82, 83, 115, 123, 124, 125, 141, 150, 166, 166, 166, 200]), mayhem=int(rng.random() < .2), cashback=rng.randrange(2),
                        cfb=rng.randrange(10_001), can_edit=rng.randrange(2), holder=rng.randrange(2), complete=rng.choice([1, 1, 1, 1, 0]),
                        config=rng.choice([None, (949, 1, 1), (949, 1, 0)]), remaining=rng.randrange(4), base_balance=rng.choice([0, 0, 0, rng.randrange(10**12)])))
    return out


class MigrateFundsCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'migrate-funds-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def answers(self, items):
        text = ''.join(host_line(item) + '\n' for item in items)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(len(out), len(items))
        return out

    def run_all(self, items):
        answers = self.answers(items)
        bad = []
        for item, answer in zip(items, answers):
            problems = check(item, answer, run_captured(item))
            if problems:
                bad.append((host_line(item), answer, problems[:2]))
        self.assertEqual(bad[:12], [], f'{len(bad)} of {len(items)}')
        return answers

    def test_fixed_cases(self):
        items = cases()
        self.assertEqual(len(items), 492)
        answers = self.run_all(items)
        outcomes = {a.split(',')[0].rsplit(':', 2)[0] if a.startswith('after-pool') else a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {'after-pool:11', 'after-pool:6027', 'below-rent', 'borsh', 'error:1', 'error:2006', 'error:6000', 'error:6006',
                                    'error:6024', 'error:6063', 'invalid-data', 'lamports', 'noop', 'ok'})
        self.assertEqual(sum(a.startswith('ok') for a in answers), FIXED_OK)

    def test_random_cases(self):
        items = random_cases()
        self.assertEqual(len(items), 300)
        self.assertEqual(sum(a.startswith('ok') for a in self.run_all(items)), 76)

    def test_checker_rejects_wrong_outcomes(self):
        short = case(slack=1)
        item = case(base_balance=7)
        got = run_captured(short)
        answer = self.answers([short])[0]
        self.assertEqual(check(short, answer, got), [])
        fields = answer.split(',')
        for i in range(1, len(fields)):
            bent = fields[:i] + [str(int(fields[i]) + 1)] + fields[i + 1:]
            self.assertNotEqual(check(short, ','.join(bent), got), [], i)
        self.assertNotEqual(check(short, 'error:1', got), [])
        got = run_captured(item)
        self.assertEqual(check(item, 'after-pool:11:7:0', got), [])
        self.assertNotEqual(check(item, 'after-pool:11:8:0', got), [])
        self.assertNotEqual(check(item, 'after-pool:11:7:1', got), [])
        self.assertNotEqual(check(item, 'after-pool:12:7:0', got), [])
        self.assertNotEqual(check(item, 'below-rent', got), [])


if __name__ == '__main__':
    unittest.main()
