"""Captured-program checks for the panic sites of the Pump volume accumulator.

The model and test files of `claim_token_incentives`,
`admin_update_token_incentives` and `claim_cashback_v2` stop at "the program
panicked". Here each of those cases, and the v2 cashback trades, runs from the
captured `evidence/original/pump/deployed.so` on LiteSVM, and the logged
`panicked at <file>:<line>:<col>:` location and message must equal the answer
of `programs/pump/recovered/incentive_panics_host.rs`. The location table of
`volume_accumulator.rs` read out of the ELF must equal the model's list of
reached and dead sites, and the fixed cases must reach every site listed as
reached. The fixtures come from the existing captured tests. This shows
matching behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_buy_v2_captured as buy  # noqa: E402
import test_claim_cashback_v2_captured as cashback  # noqa: E402
import test_sell_v2_captured as sell  # noqa: E402
import test_token_incentives_captured as incentives  # noqa: E402
import test_token_schedule_captured as schedule  # noqa: E402
import test_v2_token_quote_captured as quote  # noqa: E402

PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/incentive_panics_host.rs'
SOURCE = 'programs/pump/src/token_incentives/volume_accumulator.rs'
PANIC = re.compile(r'panicked at ' + re.escape(SOURCE) + r':(\d+):(\d+):\n(.*)', re.S)
U64 = 2**64 - 1
I64 = 2**63 - 1
N, D = schedule.NOW, schedule.DAY
START = incentives.START
EARNED, STABLE_EARNED = 74, 90


class SharedVm:
    """One VM for every case: programs load once, each case clears the last one's accounts."""
    inner = None
    logs = ()
    touched = []
    rewrite = {}
    extra = {}

    def __init__(self):
        cls = SharedVm
        if cls.inner is None:
            cls.inner = LiteSVM().with_sigverify(True).with_transaction_history(0)
            cls.loaded = set()
        for key in cls.touched:
            cls.inner.set_account(key, Account(0, b'', Pubkey.default()))
        cls.touched = []

    def with_sigverify(self, _):
        return self

    def with_transaction_history(self, _):
        return self

    def add_program_from_file(self, key, path):
        if key not in SharedVm.loaded:
            SharedVm.loaded.add(key)
            SharedVm.inner.add_program_from_file(key, path)

    def set_account(self, key, account):
        SharedVm.touched.append(key)
        if key in SharedVm.rewrite:
            account = Account(account.lamports, SharedVm.rewrite[key](bytes(account.data)), account.owner)
        SharedVm.inner.set_account(key, account)

    def send_transaction(self, tx):
        for key, account in SharedVm.extra.items():
            self.set_account(key, account)
        result = SharedVm.inner.send_transaction(tx)
        SharedVm.logs = tuple((result.meta() if hasattr(result, 'meta') else result).logs())
        return result

    def __getattr__(self, name):
        return getattr(SharedVm.inner, name)


class QuoteVm:
    """Wraps the token-quote test's VM to rewrite the accounts of a case."""

    def __init__(self, inner):
        self.inner = inner

    def set_account(self, key, account):
        if key in SharedVm.rewrite and account.data:
            account = Account(account.lamports, SharedVm.rewrite[key](bytes(account.data)), account.owner)
        self.inner.set_account(key, account)

    def __getattr__(self, name):
        return getattr(self.inner, name)


def outcome(error):
    """The answer the captured run gives, in the host's text form."""
    for line in SharedVm.logs:
        match = PANIC.search(line)
        if match:
            return f'panic:{match.group(1)}:{match.group(2)}:{match.group(3)}'
    if error is None:
        return 'ok'
    assert isinstance(error, int), error
    return f'error:{error}'


def run_claim(item):
    result = incentives.run_captured(item)
    SharedVm.touched.append(incentives.ata(incentives.USER))
    return outcome(result['error'])


def run_schedule(item):
    return outcome(schedule.run_captured(item)['error'])


def claim_line(item):
    days = ';'.join(f'{d}:{s}:{v}' for d, s, v in item['days'])
    return (f"claim,{item['now']},{item['start']},{item['end']},{item['secs']},{item['vault']},{item['unclaimed']},"
            f"{item['claimed']},{item['volume']},{item['last_update']},{days}")


def schedule_line(item):
    return (f"schedule,{N},{item['old_start']},{item['old_end']},{item['start']},{item['end']},{item['seconds']},"
            f"{item['day']},{item['supply']}")


def claim_cases():
    add = incentives.case
    cases = [c for c in incentives.fixed_cases() + incentives.random_cases(300, 310955) if c['op'] == 'claim']
    # Each site beside the case one step short of it.
    for volume in (1, 2):
        cases.append(add(unclaimed=U64 - 1, volume=volume, days=((1, 1, 1),)))
    for claimed in (U64 - 40, U64 - 39):
        cases.append(add(unclaimed=40, claimed=claimed, volume=0))
    for last_day in (29, 30, 31):
        cases.append(add(now=START + 32 * D, end=START + 40 * D, last_update=START + last_day * D + 1))
    for now in (START + 30 * D - 1, START + 30 * D, START + 45 * D):
        cases.append(add(now=now, end=START + 50 * D, last_update=now))
    cases.append(add(now=START + 31 * D, end=START + 30 * D, last_update=START + 31 * D))
    cases.append(add(now=START + 31 * D, end=START + 31 * D, last_update=START + 31 * D))
    cases.append(add(now=START + 5, end=START, last_update=START + 1))
    # A negative day length only trips the cast once the zero check passes.
    cases.append(add(secs=-D))
    cases.append(add(now=START - 1, secs=-D, last_update=START - 2, unclaimed=1))
    cases.append(add(end=-1, last_update=START + 5))
    cases.append(add(now=START - 1, end=-1, last_update=START - 2))
    cases.append(add(now=START + 2, end=START + 1, last_update=START + 1, secs=1))
    # The pre-start reset clears the claimed total the unwrap would add to.
    cases.append(add(now=START - 1, last_update=START - 2, unclaimed=2, claimed=U64))
    cases.append(add(now=START - 1, last_update=START, unclaimed=2, claimed=U64))
    return cases


def schedule_cases():
    add = schedule.case
    cases = schedule.fixed_cases() + schedule.random_cases(300, 310956)
    for seconds in (I64 // 30, I64 // 30 + 1, -(I64 // 30), -(I64 // 30) - 1):
        cases.append(add(start=N + 10, end=N + 20, seconds=seconds))
    # A stored negative start skips the past-start check and the range overflows.
    for start, end in ((-5, I64), (-1, I64), (-1, I64 - 1), (-5, N + 10)):
        cases.append(add(old_start=start, start=start, end=end))
    for days in (29, 30, 31):
        cases.append(add(old_start=N + 100, old_end=N + 100 + days * D, supply=7, day=30))
    for today, days in ((5, 29), (5, 30), (5, 31), (29, 31), (30, 31), (31, 31), (31, 40)):
        cases.append(add(old_start=N - today * D, old_end=N + (days - today) * D, supply=7, day=30))
    cases.append(add(old_start=N - 31 * D, old_end=N + 9 * D, supply=7, day=31))
    cases.append(add(old_start=N - 31 * D, old_end=N + 9 * D, supply=7, day=29))
    cases.append(add(old_start=N - 31 * D, old_end=N, supply=7, day=30))
    cases.append(add(old_start=N - 31 * D, old_end=N - 1, supply=7, day=30))
    cases.append(add(old_start=N, old_end=N, seconds=0, supply=7, day=30))
    cases.append(add(old_start=N - 1, old_end=N, seconds=0, supply=7, day=3))
    cases.append(add(old_start=N + 1, old_end=N, seconds=0, supply=7, day=3))
    cases.append(add(old_start=N, old_end=N - 1, supply=7, day=3))
    cases.append(add(old_start=N, start=N, end=N + 10))
    cases.append(add(old_start=N + 1, old_end=-1, supply=7, day=3))
    cases.append(add(old_start=N, old_end=-1, supply=7, day=3))
    cases.append(add(seconds=-1, supply=7, day=3, old_start=N + 1, old_end=N + 2))
    return cases


def uva(data, offset, value):
    data = bytearray(data)
    struct.pack_into('<Q', data, offset, value)
    return bytes(data)


def cashback_curve(data):
    return data[:82] + b'\1' + data[83:]


def run_v2(route, earned):
    """One native v2 cashback trade with `earned` already stored; returns (error, cashback paid)."""
    module = sell if route == 'sell' else buy
    key = module.UVA if route == 'sell' else module.USER_VOLUME
    item = (sell.case(10**12, 0) if route == 'sell'
            else buy.case(10**9, 10**12) if route == 'buy' else buy.case(10**9, 1, op='exact'))
    SharedVm.rewrite = {module.CURVE: cashback_curve}
    head = buy.ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(module.USER.pubkey()) + bytes(97)
    if route == 'sell':
        SharedVm.extra = {key: Account(10**9, uva(head, EARNED, earned), sell.PUMP)}
    else:
        SharedVm.rewrite[key] = lambda data: uva(data, EARNED, earned)
    try:
        error = module.run_captured(item)['error']
    finally:
        SharedVm.rewrite, SharedVm.extra = {}, {}
    if isinstance(error, str) and 'ProgramFailedToComplete' in error:
        error = None
    stored = struct.unpack_from('<Q', bytes(SharedVm.inner.get_account(key).data), EARNED)[0]
    return error, stored - earned


def run_quote(kind, op, earned):
    """One token-quote v2 cashback trade with the stable total already stored."""
    SharedVm.rewrite = {quote.USER_VOLUME: lambda data: uva(data, STABLE_EARNED, earned)}
    try:
        result = quote.run_captured(quote.default_case(quote=kind, op=op, cashback=1))
    finally:
        SharedVm.rewrite = {}
    SharedVm.logs = tuple(result['logs'])
    stored = struct.unpack_from('<Q', result['after'][quote.USER_VOLUME][1], STABLE_EARNED)[0]
    return (None if result['error'] == 'panic' else result['error']), stored - earned


def elf_locations():
    """(line, col) of each panic Location of volume_accumulator.rs in .data.rel.ro."""
    data = PUMP_ELF.read_bytes()
    table_start = struct.unpack_from('<Q', data, 0x28)[0]
    size, count = struct.unpack_from('<HH', data, 0x3a)
    sections = [struct.unpack_from('<IIQQQQ', data, table_start + i * size) for i in range(count)]
    # Every writable-relocated table holds string pointers in the high half of the first word.
    start, length = next((s[4], s[5]) for s in sections if s[1] == 1 and s[3] == 1824528)
    found = set()
    for offset in range(start, start + length - 24, 8):
        _, pointer, name_len, high, line, col = struct.unpack_from('<IIIIII', data, offset)
        if high == 0 and name_len == len(SOURCE) and data[pointer:pointer + name_len] == SOURCE.encode():
            found.add((line, col))
    return found


class IncentivePanicsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == ELF_SHA256
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'incentive-panics-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.patches = [mock.patch.object(m, 'LiteSVM', SharedVm) for m in (incentives, schedule, cashback, sell, buy)]
        for patch in cls.patches:
            patch.start()
        cls.reached = set()
        quote._VM = QuoteVm(quote.fresh_vm())

    @classmethod
    def tearDownClass(cls):
        for patch in cls.patches:
            patch.stop()
        cls.tmp.cleanup()

    def host_answers(self, lines):
        text = ''.join(line + '\n' for line in lines)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def sites(self):
        reached, dead = self.host_answers(['sites'])[0].split('|')
        parse = lambda text: {tuple(map(int, s.split(':'))) for s in text.split(';')}
        return parse(reached), parse(dead)

    def compare(self, lines, runs):
        answers = self.host_answers(lines)
        self.assertEqual(len(answers), len(lines))
        for line, answer, run in zip(lines, answers, runs):
            with self.subTest(case=line):
                self.assertEqual(run(), answer)
            if answer.startswith('panic:'):
                type(self).reached.add(tuple(map(int, answer.split(':')[1:3])))
        return answers

    def test_01_claim_sites(self):
        cases = claim_cases()
        self.compare([claim_line(c) for c in cases], [lambda c=c: run_claim(c) for c in cases])

    def test_02_schedule_sites(self):
        cases = schedule_cases()
        self.compare([schedule_line(c) for c in cases], [lambda c=c: run_schedule(c) for c in cases])

    def test_03_cashback_claim_sites(self):
        lines, runs = [], []
        for native, field, amount_field in ((True, 'claimed', 'extra'), (False, 'stable_claimed', 'uva_ata')):
            for amount in (1, 500_000, 10**12):
                for total in (0, U64 - amount, U64 - amount + 1, U64):
                    item = cashback.case(native=native, **{field: total, amount_field: amount})
                    lines.append(f'claimed,{int(native)},{total},{amount}')
                    runs.append(lambda c=item: outcome(cashback.run_captured(c)['error']))
        self.compare(lines, runs)

    def test_04_cashback_earned_sites(self):
        lines, runs = [], []
        routes = [(lambda t, r=r: run_v2(r, t), 1) for r in ('sell', 'buy', 'exact')]
        routes += [(lambda t, k=k, o=o: run_quote(k, o, t), 0) for k in ('spl', 'usdc', 'wsol', 't22')
                   for o in ('sell', 'buy', 'exact')]
        checked = 0
        for run, native in routes:
            error, amount = run(0)
            self.assertIsNone(error)
            self.assertGreater(amount, 0)
            for total in (U64 - amount, U64 - amount + 1, U64):
                lines.append(f'earned,{native},{total},{amount}')
                runs.append(lambda t=total, r=run: outcome(r(t)[0]))
                checked += 1
        self.compare(lines, runs)
        self.assertEqual(checked, 45)

    def test_05_every_listed_site_is_reached(self):
        reached, _ = self.sites()
        for test in (self.test_01_claim_sites, self.test_02_schedule_sites, self.test_03_cashback_claim_sites,
                     self.test_04_cashback_earned_sites):
            if not type(self).reached >= reached:
                test()
        self.assertEqual(type(self).reached, reached)

    def test_06_site_list_matches_the_elf_table(self):
        reached, dead = self.sites()
        self.assertFalse(reached & dead)
        self.assertEqual(reached | dead, elf_locations())

    def test_07_checker_rejects_a_wrong_site(self):
        # Negative control: the same panic with a neighbouring column or index is not equal.
        item = incentives.case(now=START + 31 * D, end=START + 40 * D, last_update=START + 31 * D)
        answer = self.host_answers([claim_line(item)])[0]
        self.assertEqual(run_claim(item), answer)
        self.assertNotEqual(run_claim(item), answer.replace('429:43', '429:42'))
        self.assertNotEqual(run_claim(item), answer[:-1] + '0')


if __name__ == '__main__':
    unittest.main()
