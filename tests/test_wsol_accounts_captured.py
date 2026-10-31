"""Captured-program checks for curves quoted in wrapped SOL on real token accounts.

The base tests of `sell_v2`, `buy_v2`, `buy_exact_quote_in_v2`,
`sweep_protocol_fee`, `sweep_creator_fee` and `distribute_creator_fees_v2` hold
plain token accounts, also on a wrapped-SOL quote. Here each of their cases runs
again from the captured `evidence/original/pump/deployed.so` on LiteSVM, with
every wrapped-SOL account in its real shape (`is_native` set, lamports =
reserve + amount), with and without lamports sent to it unsynced. The base
models must still give the whole answer, and
`programs/pump/recovered/wsol_accounts_host.rs` must give the lamports and the
reserve of every such account after the call. This shows matching behavior on
these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_creator_fee_distribution_quote_captured as distribution
import test_sweep_fees_captured as sweep
import test_v2_token_quote_captured as trades

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = dict(trades.ELF_SHA256)
HOST_SOURCE = ROOT / 'programs/pump/recovered/wsol_accounts_host.rs'
TOKEN = trades.TOKEN
WSOL = trades.WSOL
UNSYNCED = (0, 777)


class NativeVm:
    """LiteSVM with real wrapped-SOL accounts, shown to the base test as plain ones."""
    unsynced = 0
    seen = []

    def __init__(self):
        self.vm = LiteSVM()
        self.fixture = {}

    def with_sigverify(self, value):
        self.vm = self.vm.with_sigverify(value)
        return self

    def with_transaction_history(self, count):
        self.vm = self.vm.with_transaction_history(count)
        return self

    def __getattr__(self, name):
        return getattr(self.vm, name)

    def set_account(self, key, account):
        data = bytes(account.data)
        if account.owner == TOKEN and len(data) >= 165 and data[:32] == bytes(WSOL) and account.lamports:
            amount = struct.unpack_from('<Q', data, 64)[0]
            self.fixture[key] = NativeVm.unsynced
            data = data[:109] + struct.pack('<IQ', 1, account.lamports) + data[121:]
            account = Account(account.lamports + amount + NativeVm.unsynced, data, account.owner)
        else:
            self.fixture.pop(key, None)
        self.vm.set_account(key, account)

    def get_account(self, key):
        account = self.vm.get_account(key)
        if account is None or account.owner != TOKEN or len(account.data) < 165:
            return account
        data = bytes(account.data)
        if data[:32] != bytes(WSOL) or data[109] != 1:
            return account
        reserve, amount = struct.unpack_from('<Q', data, 113)[0], struct.unpack_from('<Q', data, 64)[0]
        unsynced = self.fixture.get(key)
        NativeVm.seen.append((None if unsynced is None else reserve, amount, unsynced or 0, account.lamports, reserve))
        return Account(account.lamports - amount - (unsynced or 0), data[:109] + bytes(12) + data[121:], account.owner)


def wsol_ata(wallet, mint=WSOL, program=TOKEN):
    return Pubkey.find_program_address([bytes(wallet), bytes(program), bytes(mint)], sweep.ATA)[0]


def trade_cases():
    labelled = trades.fixed_cases() + trades.random_cases()
    cases = [c[1] if isinstance(c, tuple) else c for c in labelled]
    return [c for c in cases if c['quote'] == 'wsol']


def sweep_cases():
    with mock.patch.object(sweep, 'QUOTE_MINT', WSOL):
        cases = sweep.fixed_cases() + sweep.random_cases()
    return [c for c in cases if not c['native'] and c['quote_mint'] != 'native']


def distribution_cases():
    # A wrapped-SOL balance cannot exceed the lamports that exist.
    cases = distribution.fixed_cases() + distribution.random_cases()
    return [c for c in cases if c['vault_tokens'] is None or c['vault_tokens'] <= 10**18]


class WsolAccountsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        trades.program_images()
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'wsol-accounts-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        NativeVm.seen = []

    def check_lamports(self):
        rows = NativeVm.seen
        self.assertGreater(len(rows), 0)
        text = ''.join(f"{'new' if r[0] is None else r[0]},{r[1]},{r[2]}\n" for r in rows)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(len(out), len(rows))
        self.assertEqual(out, [f'{r[3]},{r[4]}' for r in rows])

    def test_v2_trades_on_real_wrapped_sol_accounts(self):
        cases = trade_cases()
        self.assertGreater(len(cases), 150)
        answers = trades.model(cases)
        trades._VM = None
        with mock.patch.object(trades, 'LiteSVM', NativeVm):
            for unsynced in UNSYNCED:
                NativeVm.unsynced = unsynced
                trades._VM = None
                for case, answer in zip(cases, answers):
                    with self.subTest(case=trades.host_line(case), unsynced=unsynced):
                        self.assertEqual(trades.check(case, trades.run_captured(case), answer), [])
        trades._VM = None
        self.check_lamports()

    def test_sweeps_on_real_wrapped_sol_accounts(self):
        cls = sweep.SweepFeesCapturedTests
        cls.setUpClass()
        self.addCleanup(cls.tearDownClass)
        runner = cls('host_answers')
        with mock.patch.multiple(sweep, QUOTE_MINT=WSOL, LiteSVM=NativeVm):
            cases = sweep_cases()
            self.assertGreater(len(cases), 60)
            answers = runner.host_answers(cases)
            for unsynced in UNSYNCED:
                NativeVm.unsynced = unsynced
                for item, answer in zip(cases, answers):
                    with self.subTest(case=sweep.host_line(item), unsynced=unsynced):
                        runner.check(item, answer)
        self.check_lamports()

    def test_distribution_on_real_wrapped_sol_accounts(self):
        cls = distribution.CreatorFeeDistributionQuoteCapturedTests
        cls.setUpClass()
        self.addCleanup(cls.tearDownClass)
        runner = cls('host_answers')
        ata = distribution.ata
        with mock.patch.multiple(distribution, QUOTE=WSOL, LiteSVM=NativeVm, ata=lambda wallet, mint=WSOL: ata(wallet, mint)):
            cases = distribution_cases()
            self.assertGreater(len(cases), 60)
            answers = runner.host_answers(cases)
            for unsynced in UNSYNCED:
                NativeVm.unsynced = unsynced
                for item, answer in zip(cases, answers):
                    with self.subTest(case=item, unsynced=unsynced):
                        runner.check(item, answer)
        self.check_lamports()

    def test_checker_rejects_a_lamport_change(self):
        # Negative control: a row whose lamports or reserve differ by one must fail.
        NativeVm.seen = [(2_039_280, 5, 0, 2_039_285, 2_039_280), (None, 0, 0, 2_039_280, 2_039_280)]
        self.check_lamports()
        for row in ((2_039_280, 5, 0, 2_039_286, 2_039_280), (2_039_280, 5, 777, 2_039_285, 2_039_280),
                    (None, 0, 0, 2_039_280, 2_039_281)):
            NativeVm.seen = [row]
            with self.subTest(row=row), self.assertRaises(AssertionError):
                self.check_lamports()


if __name__ == '__main__':
    unittest.main()
