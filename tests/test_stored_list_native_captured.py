"""Captured-program checks for the stored shape of `SharingConfig` under native `distribute_creator_fees_v2`.

`tests/test_config_length_captured.py` reads the stored shapes of the list
accounts and leaves this route out, because its base model
(`distribution_v2_native_admission.rs`) was not on main yet. Every case here
takes the native distribution fixture of
`tests/test_creator_fee_distribution_captured.py`, run as the v2 instruction
on a native coin like `tests/test_distribution_v2_native_admission_captured.py`,
and rewrites the `SharingConfig` account as stored: another length, a count
that disagrees with the bytes, a bad discriminator or header field. The run
goes through the captured `evidence/original/pump/deployed.so` on LiteSVM and
`programs/pump/recovered/stored_list_native_host.rs` predicts the outcome.
Where the host answers `pass`, the run must equal a run on an honest account
holding the same rows. This shows matching behavior on these inputs only; it
is not a byte-identity claim.
"""
from pathlib import Path
import collections
import hashlib
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_creator_fee_distribution_captured as base

DEPS = ROOT / 'evidence/dependencies'
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    DEPS / 'spl_token/deployed.so': '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    DEPS / 'associated_token/deployed.so': '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/stored_list_native_host.rs'

ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
FEE_PAYER = Keypair.from_seed(bytes([242]) * 32)
IX = base.IX['distribute_creator_fees_v2']
SHARING_HEADER, SHARING_ROW = 80, 34
KEYS = [Pubkey.from_bytes(i.to_bytes(4, 'big') * 8) for i in range(1, 1300)]
FLAWS = {'creator': dict(curve_creator='other'), 'mint': dict(config_mint='other')}


class Harness:
    """One VM. Each run clears the last run's accounts and writes its own."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(base.PUMP, PUMP_ELF)
        for name, key in (('spl_token', base.TOKEN), ('associated_token', ATA)):
            self.vm.add_program_from_file(key, DEPS / name / 'deployed.so')
        self.vm.set_clock(base.Clock(100, base.TIMESTAMP, 0, 0, base.TIMESTAMP))
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def run(self, item, sharing_bytes):
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        self.put(FEE_PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        vault_ata = Pubkey.find_program_address([bytes(base.VAULT), bytes(base.TOKEN), bytes(WSOL)], ATA)[0]
        keys = {'payer': base.PAYER.pubkey(), 'mint': base.MINT, 'bonding_curve': base.CURVE,
                'sharing_config': base.SHARING, 'creator_vault': base.VAULT, 'system_program': base.SYSTEM,
                'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP,
                'creator_vault_quote_token_account': vault_ata, 'quote_mint': WSOL,
                'quote_token_program': base.TOKEN, 'associated_token_program': ATA}
        accounts = {
            base.PAYER.pubkey(): Account(10**12, b'', base.SYSTEM),
            base.MINT: Account(10**9, base.mint_data(), base.TOKEN),
            WSOL: Account(10**9, base.mint_data(), base.TOKEN),
            base.OTHER_MINT: Account(10**9, base.mint_data(), base.TOKEN),
            base.CURVE: Account(10**9, base.curve_data(item), base.PUMP),
            base.SHARING: Account(10**9, sharing_bytes, base.FEES),
            base.VAULT: Account(item['vault'], b'', base.SYSTEM),
        }
        remaining = []
        for i, h in enumerate(item['holders'][:item['remaining']]):
            address = base.holder_key(i, h)
            remaining.append(address)
            accounts[address] = Account(h['lamports'], b'', base.SYSTEM)
        for key, account in accounts.items():
            self.put(key, account)
        metas = [AccountMeta(keys[a['name']], a['name'] == 'payer', a.get('writable', False)) for a in IX['accounts']]
        metas += [AccountMeta(key, False, True) for key in remaining]
        tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), Instruction(base.PUMP, bytes(IX['discriminator']) + bytes([0]), metas)],
            FEE_PAYER.pubkey(), [FEE_PAYER, base.PAYER], self.vm.latest_blockhash())
        before = self.vm.get_account(base.VAULT).lamports
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            logs = ' '.join(result.meta().logs())
            if 'memory allocation failed, out of memory' in logs:
                return 'oom'
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            if code:
                return f'error:{code.group(1)}'
            if 'InvalidAccountData' in text:
                return 'error:invalid_account_data'
            return f'error:{text[:80]}'
        after = self.vm.get_account(base.VAULT).lamports
        events = [line for line in result.logs() if line.startswith('Program data: ')]
        digest = hashlib.sha256('\n'.join(events).encode()).hexdigest()[:12]
        return f'ok,{before - after},{digest}'


def sharing_stored(honest, count, rows, pad, cut, disc, status, revoked):
    data = bytearray(honest[:SHARING_HEADER - 4] + struct.pack('<I', count)
                     + honest[SHARING_HEADER:SHARING_HEADER + SHARING_ROW * rows] + bytes(pad))
    if not disc:
        data[:8] = base.ACCOUNT_DISC['Global']
    if not status:
        data[10] = 2
    if not revoked:
        data[75] = 2
    return bytes(data if cut is None else data[:cut])


def make_item(n_holders, flaw):
    holders = [base.holder(1) for _ in range(n_holders)]
    return base.case(holders=holders, remaining=min(n_holders, 20), **FLAWS.get(flaw, {}))


def shapes():
    # (count, rows stored, pad, cut, disc ok, status ok, revoked ok, flaw)
    plain = (True, True, True, '')
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
    yield 3, 3, 0, None, False, True, True, ''
    yield 3, 3, 0, 7, False, True, True, ''
    yield 3, 3, 0, 8, False, True, True, ''
    yield 3, 3, 0, None, True, False, True, ''
    yield 3, 3, 0, None, True, True, False, ''
    yield 3, 3, 0, None, False, False, False, ''
    yield 2**32 - 1, 3, 0, None, True, False, True, ''
    for rows in (120, 121, 240, 241, 242, 479, 480, 481, 482, 900):
        yield (rows, rows, 0, None) + plain
    for rows in (240, 241, 479, 480, 481):
        yield (2**32 - 1, rows, 0, None) + plain
        yield (rows + 1, rows, 0, None) + plain
    yield (3, 900, 0, None) + plain
    yield (2, 500, 0, None) + plain
    yield (240, 900, 0, None) + plain
    yield (241, 900, 0, None) + plain
    # A failing constraint does not stop the call ahead of the heap limit.
    for flaw in ('creator', 'mint'):
        for rows in (240, 241, 480, 481):
            yield rows, rows, 0, None, True, True, True, flaw


def run_shapes(harness):
    out = []
    for count, rows, pad, cut, disc, status, revoked, flaw in shapes():
        full = base.sharing_data(make_item(max(min(count, 900), rows), flaw))
        data = sharing_stored(full, count, rows, pad, cut, disc, status, revoked)
        fits = len(data) >= SHARING_HEADER and count <= (len(data) - SHARING_HEADER) // SHARING_ROW
        item = make_item(count if fits and count <= 900 else 3, flaw)
        label = harness.run(item, data)
        twin = harness.run(item, base.sharing_data(item)) if label != 'oom' else None
        line = f'native,{len(data)},{int(disc)},{count},{int(status and revoked)}'
        out.append(dict(count=count, rows=rows, pad=pad, cut=cut, flaw=flaw, line=line, label=label, twin=twin))
    return out


class StoredListNativeCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'stored-list-native-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host
        # Keep the enlarged key vocabulary local to this fixture. Importing
        # this module must not change the ordinary distribution test suite.
        with mock.patch.object(base, 'HOLDERS', KEYS):
            cls.rows = run_shapes(Harness())
        text = ''.join(row['line'] + '\n' for row in cls.rows)
        cls.answers = subprocess.run([str(host)], input=text, capture_output=True, text=True,
                                     check=True).stdout.splitlines()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check(self, row, answer):
        if answer != 'pass':
            self.assertEqual(row['label'], answer)
            return
        self.assertEqual(row['label'], row['twin'])

    def test_every_case_matches_captured_program(self):
        self.assertEqual(len(self.answers), len(self.rows))
        bad = collections.Counter()
        for row, answer in zip(self.rows, self.answers):
            try:
                self.check(row, answer)
            except AssertionError:
                bad[(row['count'], row['rows'], row['flaw'], answer, row['label'])] += 1
        self.assertEqual(bad, collections.Counter())

    def test_cases_reach_every_answer(self):
        self.assertEqual(set(self.answers), {'pass', 'oom', 'error:3001', 'error:3002', 'error:3003'})
        self.assertGreaterEqual(len(self.rows), 60)

    def test_limits_sit_on_the_row_counts(self):
        by_shape = {(r['count'], r['rows'], r['flaw']): (a, r) for r, a in zip(self.rows, self.answers)}
        # 240 stored rows decode and reach the handler; 241 run out of heap.
        answer, row = by_shape[(240, 240, '')]
        self.assertEqual(answer, 'pass')
        self.assertNotEqual(row['label'], 'oom')
        self.assertEqual(by_shape[(241, 241, '')][0], 'oom')
        # The limit is ahead of the creator and mint constraints.
        for flaw in ('creator', 'mint'):
            self.assertEqual(by_shape[(241, 241, flaw)][0], 'oom')
            answer, row = by_shape[(240, 240, flaw)]
            self.assertEqual(answer, 'pass')
            self.assertEqual(row['label'], 'error:6053' if flaw == 'creator' else 'error:6004')
        # The decode limit: a count past the bytes is 3003 at 480 rows stored
        # and runs out of memory at 481, where the rows no longer fit the heap.
        self.assertEqual(by_shape[(2**32 - 1, 480, '')][0], 'error:3003')
        self.assertEqual(by_shape[(2**32 - 1, 481, '')][0], 'oom')
        # Rows past the count are not read: 241 stated over 900 stored is the
        # handler limit, 240 stated is not.
        self.assertEqual(by_shape[(241, 900, '')][0], 'oom')
        self.assertEqual(by_shape[(240, 900, '')][0], 'pass')

    def test_checker_rejects_a_changed_answer(self):
        row = next(r for r in self.rows
                   if r['count'] == 3 and r['rows'] == 3 and r['pad'] == 0 and r['cut'] is None and not r['flaw'])
        self.check(row, 'pass')
        with self.assertRaises(AssertionError):
            self.check(row, 'oom')
        big = next(r for r in self.rows if r['count'] == 241 and r['rows'] == 241 and not r['flaw'])
        with self.assertRaises(AssertionError):
            self.check(big, 'pass')


if __name__ == '__main__':
    unittest.main()
