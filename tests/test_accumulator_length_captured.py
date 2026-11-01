"""Captured-program checks for the stored length of the volume accumulators.

Every case replays a fixed case of an existing captured test, on the captured
`evidence/original/pump/deployed.so` under LiteSVM, with the user or global
accumulator rewritten to another length just as the fixture stores it. The run
on the standard length is the twin: `programs/pump/recovered/accumulator_length_host.rs`
says whether that outcome holds, turns into an error code, or pays another
amount. A successful run must also leave the bytes past the decoded fields
alone. This shows matching behavior on these inputs only; it is not a
byte-identity claim.
"""
from pathlib import Path
import collections
import hashlib
import importlib
import json
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
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/accumulator_length_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
USER_DISC, GLOBAL_DISC = DISC['UserVolumeAccumulator'], DISC['GlobalVolumeAccumulator']
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
SYSVAR = Pubkey.from_string('Sysvar1111111111111111111111111111111111111')

USER_LEN, USER_DECODED, GLOBAL_LEN = 137, 106, 544
USER_LENGTHS = (0, 1, 7, 8, 40, 73, 98, 105, 106, 107, 114, 136, 137, 138, 200, 1000)
GLOBAL_LENGTHS = (0, 7, 8, 64, 543, 544, 545, 700)
TAIL = bytes((i * 91 + 7) % 256 for i in range(2000))
PER_MODULE = 7

SHAPE = {'target': None, 'length': None, 'inject': None, 'fund': False}
SEEN = {}


class SharedVm:
    """LiteSVM with the programs loaded once; the fixture still writes through
    `set_account`, and sees the accumulator at its standard length."""
    vm = None
    fresh = True
    loaded = set()
    touched = set()

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
        SEEN.clear()

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
        data = bytes(account.data)
        kind = {USER_DISC: 'user', GLOBAL_DISC: 'global'}.get(data[:8]) if account.owner == PUMP else None
        if kind:
            SEEN[kind] = (key, data)
            if SHAPE['target'] == kind:
                data = reshape(kind, data, SHAPE['length'])
                extra = rent(len(data)) - rent(USER_LEN) if kind == 'user' and SHAPE['fund'] else 0
                account = Account(account.lamports + max(extra, 0), data, account.owner, account.executable,
                                  account.rent_epoch)
        SharedVm.vm.set_account(key, account)

    def get_account(self, key):
        account = SharedVm.vm.get_account(key)
        for kind, (seen, stored) in SEEN.items():
            if seen == key and account is not None:
                head = bytes(account.data)[:USER_DECODED if kind == 'user' else GLOBAL_LEN]
                return Account(account.lamports, head + stored[len(head):], account.owner, account.executable,
                               account.rent_epoch)
        return account

    def send_transaction(self, tx):
        SharedVm.touched |= set(tx.message.account_keys)
        if SHAPE['inject']:
            key, data = SHAPE['inject']
            self.set_account(key, Account(10**8, data, PUMP))
        return SharedVm.vm.send_transaction(tx)

    def __getattr__(self, name):
        return getattr(SharedVm.vm, name)


def rent(length):
    return (128 + length) * 6_960


def reshape(kind, data, length):
    if kind == 'user':
        return (data[:USER_DECODED] + TAIL)[:length].ljust(length, b'\0')
    return data[:length].ljust(length, b'\0')


def stored_user():
    return SharedVm.vm.get_account(SEEN['user'][0]) if 'user' in SEEN else None


def plain(value):
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return str(value) if isinstance(value, Pubkey) else value


# What each base test's instruction does with the two accounts.
def legacy_buy_reads(m, item):
    return 'init', True


def legacy_cashback_reads(m, item):
    if item['side'] == 'buy':
        return 'init', True
    fee_due = item['cashback'] and m.creator_quote(item)[1] > 0
    return ('sell' if fee_due and item['slots'][0] == 'uva' else 'ignored'), False


def lifecycle_reads(m, item):
    return {'init': 'init', 'close': 'load', 'extend': 'extend'}[item['op']], False


def claim_v2_reads(m, item):
    return ('claim' if item['native'] else 'load'), False


MODULES = {
    'legacy_buy': legacy_buy_reads,
    'legacy_cashback': legacy_cashback_reads,
    'buy_v2': legacy_buy_reads,
    'sell_v2': lambda m, item: ('init', False),
    'v3_trade_accounting': lambda m, item: ('init', False),
    'v3_exact_quote': lambda m, item: ('init', False),
    'token_incentives': lambda m, item: ('load', True),
    'claim_cashback': lambda m, item: ('claim', False),
    'claim_cashback_v2': claim_v2_reads,
    'account_lifecycle': lifecycle_reads,
}


def eligible(error):
    """Handler and token program outcomes; account-load failures of the fixture
    itself say nothing about this account's length."""
    return error is None or error == 1 or error == 2000 or (isinstance(error, int) and error >= 6000)


def sell_v2_user(m):
    data = bytearray(USER_LEN)
    data[:8] = USER_DISC
    data[8:40] = bytes(m.USER.pubkey())
    return m.UVA, bytes(data)


def run(m, item):
    result = m.run_captured(item)
    user = stored_user()
    return result, (None if user is None else (user.lamports, bytes(user.data)))


def replay(name, reads):
    """Yield one row per (base case, target, length)."""
    SharedVm.vm = None
    m = importlib.import_module(f'test_{name}_captured')
    with mock.patch.object(m, 'LiteSVM', SharedVm):
        SHAPE.update(target=None, length=None, inject=sell_v2_user(m) if name == 'sell_v2' else None)
        chosen, codes = [], collections.Counter()
        for item in m.fixed_cases():
            item = item[1] if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) else item
            SHAPE.update(target=None, length=None)
            twin, end = run(m, item)
            user = SEEN.get('user')
            if not eligible(twin['error']) or user is None or len(user[1]) != USER_LEN:
                continue
            if 'global' in SEEN and len(SEEN['global'][1]) != GLOBAL_LEN:
                continue
            read, global_read = reads(m, item)
            if read == 'claim' and twin['error'] == 6024:  # the overflow follows the amount, which moves with the length
                continue
            chosen.append((codes[(twin['error'], read)], item, twin, end, read, global_read))
            codes[(twin['error'], read)] += 1
        chosen.sort(key=lambda row: row[0])
        for _, item, twin, end, read, global_read in chosen[:PER_MODULE]:
            for target, lengths in (('user', USER_LENGTHS), ('global', GLOBAL_LENGTHS)):
                for length in lengths:
                    start = start_lamports(m, item) if read == 'claim' else 0
                    SHAPE.update(target=target, length=length, fund=read == 'sell')
                    result, after = run(m, item)
                    if target == 'user':
                        line = f"user,{read},{length},{start},{'-' if twin['error'] is None else twin['error']}"
                    else:
                        line = f'global,{int(global_read)},{length}'
                    yield name, line, plain(twin), plain(result), after, read, target, length, start, end
    SHAPE.update(target=None, length=None, inject=None)


def start_lamports(m, item):
    """Accumulator lamports the fixture stores for a claim."""
    SHAPE.update(target=None, length=None)
    keep = dict(SHAPE)
    sent = []
    real = SharedVm.send_transaction

    def capture(self, tx):
        sent.append(SharedVm.vm.get_account(SEEN['user'][0]).lamports)
        return real(self, tx)

    with mock.patch.object(SharedVm, 'send_transaction', capture):
        m.run_captured(item)
    SHAPE.update(keep)
    return sent[0]


class AccumulatorLengthCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == ELF_SHA256
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'accumulator-length-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = str(host)
        cls.rows = [row for name, reads in MODULES.items() for row in replay(name, reads)]
        text = ''.join(row[1] + '\n' for row in cls.rows)
        out = subprocess.run([str(host)], input=text, capture_output=True, text=True, check=True).stdout
        cls.answers = out.splitlines()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check(self, row, answer):
        _, _, twin, result, after, read, target, length, start, end = row
        if answer.startswith('error:'):
            self.assertEqual(result['error'], int(answer[6:]))
        elif answer.startswith('paid:'):
            self.assertIsNone(result['error'])
            self.assertEqual(after[0], start - int(answer[5:]))
        elif read == 'extend' and target == 'user':
            self.assertEqual(result['error'], twin['error'])
        else:
            self.assertEqual(result, twin)
        if target == 'user' and result['error'] is None and after and after[1] and read != 'extend':
            self.assertEqual(after[1][USER_DECODED:], reshape('user', bytes(USER_DECODED), length)[USER_DECODED:])

    def test_a_malformed_twin_or_read_is_refused(self):
        # `.ok()` read a malformed twin column as "the twin succeeded", and the
        # catchall read any unknown token as `extend`; both answers are real.
        for line in ('user,claim,137,1000000,not-a-code', 'user,nonsense,137,1000000,-'):
            with self.subTest(line=line):
                run = subprocess.run([self.host], input=line + '\n', capture_output=True, text=True)
                self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_every_replay_matches_captured_program(self):
        self.assertEqual(len(self.answers), len(self.rows))
        bad = collections.Counter()
        for row, answer in zip(self.rows, self.answers):
            with self.subTest(module=row[0], line=row[1], host=answer, got=row[3].get('error')):
                try:
                    self.check(row, answer)
                except AssertionError:
                    bad[(row[0], row[1].split(',')[1], row[1].split(',')[2], answer, str(row[3].get('error')))] += 1
                    raise
        self.assertEqual(bad, collections.Counter())

    def test_cases_reach_every_answer(self):
        kinds = collections.Counter(a.split(':')[0] if a != 'same' else 'same' for a in self.answers)
        self.assertGreaterEqual(len(self.rows), 500)
        codes = {a for a in self.answers if a.startswith('error:')}
        self.assertEqual(codes, {'error:0', 'error:2019', 'error:3001', 'error:3003', 'error:6010', 'error:6073'})
        self.assertGreater(kinds['paid'], 0)
        self.assertGreater(kinds['same'], 0)

    def test_every_module_reaches_a_length_failure(self):
        hit = {row[0] for row, a in zip(self.rows, self.answers) if a.startswith('error:')}
        self.assertEqual(hit, set(MODULES))


if __name__ == '__main__':
    unittest.main()
