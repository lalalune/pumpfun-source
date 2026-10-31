"""Captured-program checks for the buyback recipient of the v3 trades on
token quotes.

`tests/test_v3_account_admission_captured.py` judges the recipient slot's
faults and an owner entered at the last slot of `Global.buyback_fee_recipients`;
`tests/test_v3_trade_accounting_captured.py` prices the trades and pays the
one fixture recipient. This packet varies the list and the payment together,
on the accounting fixture's fixed trades: the recipient token account's
owner entered at each of the eight slots, entered twice, a different listed
owner than the fixture's, no entry, and the zero owner — plain, whitelisted,
on a mayhem curve, and with a zero buyback split. Amounts never move; the
same inputs go to `programs/pump/recovered/v3_quote_recipients_host.rs`, and
the judgment (paid into the passed account, refused 6057, refused 6062) and
the paid account's balance must agree, with the amount taken from a twin
run of the same trade paying the fixture's own recipient. This shows
matching behavior on these inputs only; it is not a byte-identity claim.

Unconfirmed: recipient accounts of any shape other than the owner's
associated token account (the admission packet's territory), and the native
routes (the trade recipients packet's).
"""
from pathlib import Path
import hashlib
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
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v3_account_admission_captured as adm  # noqa: E402

acct = adm.base
ROOT = Path(__file__).resolve().parents[1]
HOST_SOURCE = ROOT / 'programs/pump/recovered/v3_quote_recipients_host.rs'
ALIEN = adm.ALIEN
SYSTEM = acct.SYSTEM
IXS = tuple(adm.IXS)
LIST = adm.BUYBACK_LIST
ZERO_KEY = bytes(32)

_HOST = None


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'v3_quote_recipients_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(cases):
    text = ''.join(f"{c['zero']},{c['listed']},{c['whitelisted']}\n" for c in cases)
    answers = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    if len(answers) != len(cases):
        raise ValueError(f'host returned {len(answers)} answers for {len(cases)} cases')
    return answers


class Program:
    """One LiteSVM kept across cases, as in the admission packet, also
    reading the two candidate recipient balances around each run."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        for key, path in ((acct.PUMP, acct.PUMP_ELF), (acct.TOKEN, acct.TOKEN_ELF), (acct.TOKEN22, acct.TOKEN22_ELF),
                          (acct.ATA, acct.ATA_ELF)):
            self.vm.add_program_from_file(key, path)
        self.vm.set_clock(Clock(100, acct.TIMESTAMP, acct.EPOCH, acct.EPOCH, acct.TIMESTAMP))
        self.seen = set()

    def balance(self, key):
        account = self.vm.get_account(key)
        if account is None or len(account.data) < 72:
            return 0
        return struct.unpack_from('<Q', bytes(account.data), 64)[0]

    def run(self, fx, passed, other):
        vm = self.vm
        for key in self.seen - set(fx.accounts):
            vm.set_account(key, Account(0, b'', SYSTEM))
        for key, account in fx.accounts.items():
            vm.set_account(key, account)
        self.seen |= set(fx.accounts)
        before = (self.balance(passed), self.balance(other))
        ix = acct.IX[fx.ix]
        metas = [AccountMeta(fx.names[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ix['accounts']]
        data = bytes(ix['discriminator']) + struct.pack('<QQ', *fx.args)
        if fx.ix != 'sell_v3':
            data += bytes([0])
        vm.expire_blockhash()
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(acct.PUMP, data, metas)],
                                               acct.USER.pubkey(), [acct.USER], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        error = None
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            if code:
                error = int(code.group(1))
            else:
                words = re.sub(r'[^A-Za-z]+', ' ', text).split()
                error = words[-1] if words else text
        return dict(error=error, delta=self.balance(passed) - before[0], other=self.balance(other) - before[1])


def set_recipient(fx, owner, entries):
    """Enter `owner` at `entries` of the buyback list (the fixture's own
    entry is cleared) and pass the owner's associated token account."""
    data = bytearray(fx.held('global').data)
    data[LIST:LIST + 32] = ZERO_KEY
    for entry in entries:
        data[LIST + 32 * entry:LIST + 32 * (entry + 1)] = bytes(owner)
    fx.put('global', data=bytes(data))
    key = acct.ata(owner, fx.roles['quote_mint'], fx.roles['program'])
    fx.accounts[key] = Account(acct.TOKEN_RENT, acct.token_bytes(fx.roles['quote_mint'], owner, 0), fx.roles['program'])
    fx.names['buyback_fee_recipient'] = key
    return key


def check(answer, got, twin):
    bad = []
    if answer.startswith('error:'):
        if got['error'] != int(answer[6:]):
            bad.append(f"error {got['error']} != {answer}")
        if got['delta'] != 0 or got['other'] != 0:
            bad.append('a refused trade paid a recipient')
        return bad
    if got['error'] is not None:
        return [f"captured failed with {got['error']}"]
    want = twin['delta'] if answer == 'ok,1' else 0
    if got['delta'] != want:
        bad.append(f"passed account paid {got['delta']} != {want}")
    if got['other'] != 0:
        bad.append("the fixture's recipient was paid instead")
    return bad


class V3QuoteRecipientsCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = Program()

    def run_case(self, ix, quote, over, owner, entries):
        """One recipient variation and its twin paying the fixture recipient."""
        twin_fx = adm.Fixture(ix, quote, **over)
        twin = self.program.run(twin_fx, twin_fx.roles['recipient'], twin_fx.roles['recipient'])
        self.assertIsNone(twin['error'], (ix, quote, over, 'twin'))
        fx = adm.Fixture(ix, quote, **over)
        passed = set_recipient(fx, owner, entries)
        got = self.program.run(fx, passed, fx.roles['recipient'])
        case = dict(zero=int(owner == SYSTEM), listed=int(owner != SYSTEM and bool(entries)),
                    whitelisted=int(bool(over.get('whitelisted'))))
        return case, got, twin

    def run_matrix(self, specs):
        cases, runs = [], []
        for spec in specs:
            case, got, twin = self.run_case(*spec)
            cases.append(case)
            runs.append((spec, got, twin))
        for (spec, got, twin), answer in zip(runs, model(cases)):
            with self.subTest(spec=spec):
                self.assertEqual(check(answer, got, twin), [], answer)

    def test_owner_at_each_list_entry(self):
        specs = [(ix, quote, {}, ALIEN, (entry,)) for ix in IXS for quote in ('spl', 't22', 'wsol') for entry in range(8)]
        self.assertEqual(len(specs), 72)
        self.run_matrix(specs)

    def test_unlisted_and_zero_owner(self):
        specs = [(ix, quote, {}, ALIEN, ()) for ix in IXS for quote in ('spl', 't22', 'wsol')]
        specs += [(ix, quote, {}, SYSTEM, (3,)) for ix in IXS for quote in ('spl', 't22', 'wsol')]
        self.run_matrix(specs)

    def test_owner_entered_twice(self):
        specs = [(ix, quote, {}, ALIEN, (2, 5)) for ix in IXS for quote in ('spl', 't22')]
        self.run_matrix(specs)

    def test_contexts_judge_the_same(self):
        specs = []
        for over in ({'whitelisted': 1}, {'mayhem': 1}, {'buyback_bps': 0}):
            for ix in IXS:
                for quote in ('spl', 't22'):
                    specs.append((ix, quote, over, ALIEN, (3,)))
                    specs.append((ix, quote, over, ALIEN, ()))
                    specs.append((ix, quote, over, SYSTEM, (3,)))
        self.assertEqual(len(specs), 54)
        self.run_matrix(specs)

    def test_every_elf_digest_is_pinned(self):
        for path, digest in adm.ELF_SHA256.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest, path)

    def test_checker_rejects_tampered_answers(self):
        case, got, twin = self.run_case('buy_v3', 'spl', {}, ALIEN, (3,))
        answer = model([case])[0]
        self.assertEqual(answer, 'ok,1')
        self.assertEqual(check(answer, got, twin), [])
        for bent in ('ok,0', 'error:6057', 'error:6062', 'error:6000'):
            self.assertNotEqual(check(bent, got, twin), [], bent)
        self.assertNotEqual(check(answer, dict(got, delta=got['delta'] + 1), twin), [])
        self.assertNotEqual(check(answer, dict(got, other=1), twin), [])
        case, got, twin = self.run_case('buy_v3', 'spl', {}, ALIEN, ())
        answer = model([case])[0]
        self.assertEqual(answer, 'error:6057')
        self.assertEqual(check(answer, got, twin), [])
        for bent in ('ok,1', 'ok,0', 'error:6062'):
            self.assertNotEqual(check(bent, got, twin), [], bent)


if __name__ == '__main__':
    unittest.main()
