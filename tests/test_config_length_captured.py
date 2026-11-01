"""Captured-program checks for the stored shape of Pump's list accounts.

Every case takes a fixture of an existing captured test and rewrites one account
just as the fixture stores it: `QuoteControl` under the five Anchor-typed quote
control commands and under the in-place scan of `create_v2`, pump_fees'
`SharingConfig` under `migrate_bonding_curve_creator` and the fee distributions,
and `holder_rewards` under `distribute_fee_to_holders`. The run goes through the
captured `evidence/original/pump/deployed.so` on LiteSVM and
`programs/pump/recovered/config_length_host.rs` predicts the outcome. Where the
host answers `pass`, the run must equal a run on an honest account holding the
same rows. This shows matching behavior on these inputs only; it is not a
byte-identity claim.
"""
from pathlib import Path
import collections
import hashlib
import re
import subprocess
import struct
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_create_v2_captured as create_base
import test_creator_assignment_captured as assign_base
import test_creator_fee_distribution_captured as dist_base
import test_creator_fee_distribution_quote_captured as quote_base
import test_holder_distribution_captured as holder_base
import test_quote_control_captured as control_base

PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/config_length_host.rs'

SYSTEM = Pubkey.default()
SYSVAR = Pubkey.from_string('Sysvar1111111111111111111111111111111111111')
FOREIGN = Pubkey.from_bytes(bytes([9]) * 32)
PUMP = control_base.PUMP
HEADER, ROW = 108, 40
SHARING_HEADER, SHARING_ROW = 80, 34
FILLER_ID = 100
KEYS = {FILLER_ID + i: Pubkey.from_bytes(i.to_bytes(4, 'big') * 8) for i in range(1, 1300)}
HOLDERS = [Pubkey.from_bytes(i.to_bytes(2, 'big') * 16) for i in range(1, 1000)]
OPS = {'add': 4, 'remove': 2, 'reserves': 3, 'admin': control_base.OUTSIDER,
       'reserves_admin': control_base.OUTSIDER}
REWARDS_SHAPE = {}


class SharedVm:
    """LiteSVM with the programs loaded once per base test."""
    vm = None
    fresh = True
    loaded = set()
    touched = set()
    last = None

    def __init__(self):
        c = SharedVm
        if c.vm is None:
            c.vm, c.fresh, c.loaded, c.touched = LiteSVM(), True, set(), set()
        for key in c.touched:
            account = c.vm.get_account(key)
            if account is not None and not account.executable and account.owner != SYSVAR:
                c.vm.set_account(key, Account(0, b'', SYSTEM))
        c.touched = set()
        c.vm.expire_blockhash()

    def with_sigverify(self, value):
        if SharedVm.fresh:
            SharedVm.vm = SharedVm.vm.with_sigverify(value)
        return self

    def with_transaction_history(self, value):
        if SharedVm.fresh:
            SharedVm.vm = SharedVm.vm.with_transaction_history(value)
        return self

    def add_program_from_file(self, key, path):
        SharedVm.fresh = False
        if key not in SharedVm.loaded:
            SharedVm.loaded.add(key)
            SharedVm.vm.add_program_from_file(key, path)

    def set_account(self, key, account):
        SharedVm.touched.add(key)
        if key == holder_base.REWARDS and REWARDS_SHAPE:
            account = Account(account.lamports, bytes(REWARDS_SHAPE['len']), REWARDS_SHAPE['owner'])
        SharedVm.vm.set_account(key, account)

    def send_transaction(self, tx):
        SharedVm.touched |= set(tx.message.account_keys)
        SharedVm.last = SharedVm.vm.send_transaction(tx)
        return SharedVm.last

    def __getattr__(self, name):
        return getattr(SharedVm.vm, name)


def outcome(result):
    """The host's spelling of a captured result."""
    error = result['error']
    if error is None:
        return 'pass'
    if isinstance(error, int):
        return f'error:{error}'
    logs = ' '.join(SharedVm.last.meta().logs())
    if 'memory allocation failed, out of memory' in logs:
        return 'oom'
    text = str(SharedVm.last.err())
    if 'InvalidArgument' in text:
        return 'argument'
    if 'ExternalAccountLamportSpend' in text:
        return 'spend'
    code = re.search(r'Custom\((\d+)\)', text)
    return f'error:{code.group(1)}' if code else text[:80]


def replay(base, run):
    SharedVm.vm = None
    with mock.patch.object(base, 'LiteSVM', SharedVm):
        yield from run()


# QuoteControl under the Anchor-typed commands.
def control_rows(count):
    return ((2, 100), (3, 200), *((FILLER_ID + i, 7) for i in range(1, max(0, count - 1))))[:count]


def control_stored(rows, count, length, disc=True):
    body = control_base.serialize(control_base.ADMIN, control_base.RESERVES_ADMIN, rows)
    data = bytearray((body + bytes([0xEE]) * length)[:max(length, 0)])
    if length >= HEADER:
        data[104:108] = struct.pack('<I', count)
    if not disc and length >= 8:
        data[:8] = control_base.ACCOUNT_DISC['Global']
    return bytes(data)


def control_case(op, count, length):
    rows = control_rows(count) if HEADER + ROW * count <= length else ()
    return control_base.case(op, OPS[op], 9, signer=control_base.GLOBAL_AUTHORITY, mints=rows, len=length,
                             lamports=control_base.rent(max(length, 2000)))


def control_grid():
    lengths = (1, 7, 8, 9, 100, 104, 107, 108, 109, 147, 148, 187, 188, 189, 300)
    for length in lengths:
        for count in (0, 1, 2, 3, 2**32 - 1):
            yield max(4, count if count < 10 else 4), count, length, True
    yield 2, 2, 188, False
    yield 2, 2, 7, False
    yield 2, 2, 8, False
    yield 2, 2, 300, False
    for stored in (101, 102, 103, 204, 205, 255, 256, 257, 407, 408, 409, 410, 500, 816, 1000):
        yield stored, stored, HEADER + ROW * stored, True
        yield stored, stored, HEADER + ROW * stored + 39, True
    # A low count over more stored bytes than the heap could hold.
    yield 500, 2, HEADER + ROW * 500, True
    yield 1000, 408, HEADER + ROW * 1000, True
    # The count outruns the bytes on either side of the limit.
    for stored in (407, 408, 409, 410):
        for count in (stored + 1, stored + 100, 2**32 - 1):
            yield stored, count, HEADER + ROW * stored, True


def control_runs():
    m = control_base
    with mock.patch.dict(m.KEYS, KEYS):
        for op in OPS:
            for stored, count, length, disc in control_grid():
                data = control_stored(control_rows(stored), count, length, disc)
                item = control_case(op, count, length)
                with mock.patch.object(m, 'control_bytes', lambda i: data):
                    result = m.run_captured(item)
                label = outcome(result)
                twin = m.run_captured(item) if label != 'oom' and HEADER + ROW * count <= length else None
                yield dict(group='control', op=op, length=length, count=count,
                           line=f'typed,control,{length},{int(disc)},{count},1,1', result=result, twin=twin,
                           label=label, head=HEADER + ROW * count)


# The in-place scan of create_v2.
def scan_data(rows, count, length=None, disc=True):
    mint = bytes(create_base.CONTROLLED)
    body = b''.join((mint if row == 'mint' else bytes(KEYS[FILLER_ID + i + 1])) + struct.pack('<Q', 1000 + i)
                    for i, row in enumerate(rows))
    head = control_base.ACCOUNT_DISC['QuoteControl' if disc else 'Global'] + bytes(create_base.USER.pubkey()) * 2
    data = head + bytes(32) + struct.pack('<I', count) + body
    return data if length is None else data[:length]


def scan_cases():
    one, far = ['mint'], ['x'] * 999 + ['mint']
    for length in (0, 1, 7, 8, 100, 103, 104, 107):
        yield one, 1, length, True, 0
    yield [], 0, None, True, None
    yield one, 0, None, True, 0
    yield one, 2, None, True, 0
    yield one, 2**32 - 1, None, True, 0
    yield one, 2**31, None, True, 0
    yield one, 1, None, False, 0
    yield one, 1, 108, True, 0
    yield one, 1, 147, True, 0
    yield one + ['x'], 2, 187, True, 0
    yield one + ['x'], 1, None, True, 0
    yield ['x', 'mint'], 1, None, True, 1
    yield ['x', 'mint'], 2, None, True, 1
    yield ['x', 'mint', 'mint'], 3, None, True, 1
    yield ['x', 'x', 'x'], 3, None, True, None
    yield ['x'] * 10 + ['mint'], 11, None, True, 10
    # Past the 408 rows a typed command can read.
    yield ['x'] * 408 + ['mint'], 409, None, True, 408
    yield far, 1000, None, True, 999
    yield far, 999, None, True, 999


def scan_runs():
    m = create_base
    for rows, count, length, disc, first in scan_cases():
        data = scan_data(rows, count, length, disc)
        with mock.patch.object(m, 'control_data', lambda entries: data):
            result = m.run_captured(m.case(quote='listed'))
        account = SharedVm.vm.get_account(m.CURVE)
        reserves = struct.unpack_from('<Q', bytes(account.data), 16)[0] if result['error'] is None else None
        yield dict(group='scan', op='create_v2', length=len(data), count=count, result=result, reserves=reserves,
                   line=f"scan,{len(data)},{int(disc)},{count},{'-' if first is None else first}",
                   label=outcome(result))


# SharingConfig under the Anchor-typed readers.
def migrate_item(rows, flawed=False):
    return assign_base.case('migrate', curve_creator=2, holders=tuple((1, 0) for _ in range(rows)))


def distribution_item(base, op, rows, flawed=False):
    extra = dict(config_mint='other') if flawed else {}
    holders = [base.holder(1) for _ in range(rows)]
    if op == 'quote':
        return base.case(holders=holders, remaining=min(2 * rows, 20), **extra)
    return base.case(op=op, holders=holders, remaining=min(rows, 20), **extra)


SHARING_SLOTS = (
    ('migrate', assign_base, 'sharing_bytes', 'migrate', migrate_item),
    ('distribute', dist_base, 'sharing_data', 'distribute', lambda *k: distribution_item(dist_base, 'distribute', *k)),
    ('minimum', dist_base, 'sharing_data', 'distribute', lambda *k: distribution_item(dist_base, 'minimum', *k)),
    ('quote', quote_base, 'sharing_data', 'quote', lambda *k: distribution_item(quote_base, 'quote', *k)),
)


def sharing_stored(honest, count, rows, pad, cut, disc, status, revoked):
    data = bytearray(honest[:SHARING_HEADER - 4] + struct.pack('<I', count)
                     + honest[SHARING_HEADER:SHARING_HEADER + SHARING_ROW * rows] + bytes(pad))
    if not disc:
        data[:8] = assign_base.ACCOUNT_DISC['Global']
    if not status:
        data[10] = 2
    if not revoked:
        data[75] = 2
    return bytes(data if cut is None else data[:cut])


def sharing_shapes():
    plain = (True, True, True, False)
    for cut in (0, 1, 7, 8, 9, 42, 75, 76, 79, 80, 100, 113):
        yield (1, 1, 0, cut) + plain
    yield (3, 3, 0, 181) + plain
    for pad in (0, 1, 33, 34, 100):
        yield (3, 3, pad, None) + plain
    yield (2, 3, 0, None) + plain
    yield (0, 3, 0, None) + plain
    yield (4, 3, 0, None) + plain
    yield (4, 3, 33, None) + plain
    yield (2**32 - 1, 3, 0, None) + plain
    yield 3, 3, 0, None, False, True, True, False
    yield 3, 3, 0, 7, False, True, True, False
    yield 3, 3, 0, 8, False, True, True, False
    yield 3, 3, 0, None, True, False, True, False
    yield 3, 3, 0, None, True, True, False, False
    yield 3, 3, 0, None, False, False, False, False
    yield 2**32 - 1, 3, 0, None, True, False, True, False
    for rows in (120, 121, 240, 241, 242, 479, 480, 481, 482, 900):
        yield (rows, rows, 0, None) + plain
    for rows in (240, 241, 479, 480, 481):
        yield (2**32 - 1, rows, 0, None) + plain
        yield (rows + 1, rows, 0, None) + plain
    yield (3, 900, 0, None) + plain
    # A failing constraint stops the call ahead of the handler's allocations.
    for rows in (240, 241, 480):
        yield rows, rows, 0, None, True, True, True, True
    yield 481, 481, 0, None, True, True, True, True


def sharing_runs(name, base, attribute, slot, build):
    with mock.patch.object(base, 'HOLDERS', HOLDERS) if hasattr(base, 'HOLDERS') else mock.patch.object(
            base, 'ROOT', base.ROOT):
        for count, rows, pad, cut, disc, status, revoked, flawed in sharing_shapes():
            if flawed and slot == 'migrate':
                continue
            full = getattr(base, attribute)(build(max(min(count, 900), rows), flawed))
            data = sharing_stored(full, count, rows, pad, cut, disc, status, revoked)
            fits = len(data) >= SHARING_HEADER and count <= (len(data) - SHARING_HEADER) // SHARING_ROW
            item = build(count if fits and count <= 900 else 3, flawed)
            with mock.patch.object(base, attribute, lambda i: data):
                result = base.run_captured(item)
            label = outcome(result)
            twin = base.run_captured(item) if label != 'oom' else None
            line = f'typed,{slot},{len(data)},{int(disc)},{count},{int(status and revoked)},{int(not flawed)}'
            yield dict(group='sharing', op=name, length=len(data), count=count, result=result, twin=twin,
                       line=line, label=label)


# holder_rewards.
def rewards_runs():
    m = holder_base
    for owner, system in ((SYSTEM, 1), (PUMP, 0), (FOREIGN, 0)):
        for length in (0, 1, 8, 100):
            for entries, amount in ((((0, 1000),), 1000), (((0, 0),), 0), ((), 0), (((0, 1000), (1, 1)), 1000)):
                for lamports in (10**9, m.FLOOR, m.FLOOR - 1):
                    item = m.case(*entries, lamports=lamports)
                    REWARDS_SHAPE.clear()
                    twin = m.run_captured(item)
                    REWARDS_SHAPE.update(len=length, owner=owner)
                    result = m.run_captured(item)
                    label = outcome(result)
                    REWARDS_SHAPE.clear()
                    yield dict(group='rewards', op='distribute_fee_to_holders', length=length, count=len(entries),
                               result=result, twin=twin, line=f'rewards,{system},{length},{amount}', label=label,
                               twin_label=None)


class ConfigLengthCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == ELF_SHA256
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'config-length-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = str(host)
        cls.rows = list(replay(control_base, control_runs)) + list(replay(create_base, scan_runs))
        for name, base, attribute, slot, build in SHARING_SLOTS:
            cls.rows += replay(base, lambda: sharing_runs(name, base, attribute, slot, build))
        cls.rows += replay(holder_base, rewards_runs)
        text = ''.join(row['line'] + '\n' for row in cls.rows)
        out = subprocess.run([str(host)], input=text, capture_output=True, text=True, check=True).stdout
        cls.answers = out.splitlines()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check(self, row, answer):
        result, twin = row['result'], row.get('twin')
        if row['group'] == 'scan':
            if answer.startswith('found:'):
                self.assertEqual(row['label'], 'pass')
                self.assertEqual(row['reserves'], 1000 + int(answer[6:]))
            else:
                self.assertEqual(row['label'], 'error:6063' if answer == 'missing' else answer)
            return
        if answer != 'pass':
            self.assertEqual(row['label'], answer)
            return
        if row['group'] == 'control':
            self.assertEqual(result['error'], twin['error'])
            if result['error'] is None:
                self.assertEqual(result['events'], twin['events'])
                self.assertEqual(result['delta'], twin['delta'])
                grown = ROW if row['op'] == 'add' else 0
                self.assertEqual(result['account'][2][:row['head'] + grown], twin['account'][2][:row['head'] + grown])
        else:
            self.assertEqual(result, twin)

    def test_a_malformed_column_or_request_is_refused(self):
        # `.ok()` read a malformed `first` column as "no row", and the
        # catchalls ran quote-distribute or rewards for any unknown token.
        for line in ('scan,408,1,1,not-a-row', 'typed,nonsense,408,1,1,1,1', 'nonsense,0,100,5'):
            with self.subTest(line=line):
                run = subprocess.run([self.host], input=line + '\n', capture_output=True, text=True)
                self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_every_case_matches_captured_program(self):
        self.assertEqual(len(self.answers), len(self.rows))
        bad = collections.Counter()
        for row, answer in zip(self.rows, self.answers):
            try:
                self.check(row, answer)
            except AssertionError:
                bad[(row['group'], row['op'], answer, row['label'])] += 1
        self.assertEqual(bad, collections.Counter())

    def test_cases_reach_every_answer(self):
        seen = collections.defaultdict(set)
        for row, answer in zip(self.rows, self.answers):
            seen[row['group']].add(re.sub(r':\d+$', '', answer) if answer.startswith('found') else answer)
        self.assertEqual(seen['control'], {'pass', 'oom', 'error:3001', 'error:3002', 'error:3003'})
        self.assertEqual(seen['sharing'], {'pass', 'oom', 'error:3001', 'error:3002', 'error:3003'})
        self.assertEqual(seen['scan'], {'found', 'missing', 'error:6075'})
        self.assertEqual(seen['rewards'], {'pass', 'argument', 'spend'})
        self.assertGreaterEqual(len(self.rows), 500)

    def test_limits_sit_on_the_row_counts(self):
        # The scan reads a row no typed command can load.
        scan = [row for row, answer in zip(self.rows, self.answers) if answer == 'found:999']
        self.assertTrue(scan)
        typed = {(r['op'], r['count']): a for r, a in zip(self.rows, self.answers)
                 if r['group'] == 'control' and r['length'] == HEADER + ROW * r['count']}
        for op in OPS:
            self.assertEqual(typed[(op, 408)], 'pass')
            self.assertEqual(typed[(op, 409)], 'oom')


if __name__ == '__main__':
    unittest.main()
