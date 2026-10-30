"""Captured-program checks for PumpSwap `update_buyback_config`.

Each case builds a synthetic `GlobalConfig` (899-, 932- or 941-byte layout, or
something broken), an `Option<u64>` argument and zero or more remaining
accounts after the four fixed metas (`admin`, `global_config`,
`event_authority`, `program`), runs the instruction on `evidence/original/pump_amm/deployed.so` in
LiteSVM, and feeds the same bytes to
`programs/pump-amm/recovered/update_buyback_config_host.rs`. Owners and the
signer and writable flags are worked out here from the metas actually passed.
The error (custom code or runtime error) and the committed config bytes must
agree; config metadata stays unchanged and failed transactions roll back its
bytes. No event is logged or self-CPI'd. This is matching behaviour on these
inputs only, not a byte-identity claim.
"""
from pathlib import Path
import hashlib
from functools import cache
import random
import re
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
AMM_ELF = ROOT / 'evidence/original/pump_amm/deployed.so'
AMM_SHA256 = '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7'
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/update_buyback_config_host.rs'

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.default()
CONFIG_DISC = hashlib.sha256(b'account:GlobalConfig').digest()[:8]
IX = hashlib.sha256(b'global:update_buyback_config').digest()[:8]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
GLOBAL_CONFIG = Pubkey.find_program_address([b'global_config'], AMM)[0]
PAYER = Keypair.from_seed(bytes([231]) * 32)
ADMIN = Keypair.from_seed(bytes([232]) * 32)
OTHER = Keypair.from_seed(bytes([233]) * 32)
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
RECIPIENTS = [Pubkey.from_bytes(bytes([100 + i]) * 32) for i in range(10)]
LENGTHS = (907, 940, 949)
MAYHEM, CASHBACK, BUYBACK_RECIPIENTS, BPS, BOOST_ON, CFC = 417, 642, 643, 899, 939, 940


def config_bytes(c):
    """A config with every non-bool byte set to a pattern, so a stray write shows."""
    n = c.get('length', 949)
    data = bytearray((i * 41 + 7) % 256 for i in range(max(n, 949)))
    data[:8] = CONFIG_DISC
    data[8:40] = bytes(c.get('admin', ADMIN.pubkey()))
    data[MAYHEM] = c.get('mayhem', 0)
    data[CASHBACK] = c.get('cashback', 1)
    data[BOOST_ON] = c.get('boost', 1)
    data[CFC] = c.get('cfc', 0)
    for at, value in c.get('patches', ()):
        data[at:at + len(value)] = value
    return bytes(data[:n])


def args_bytes(c):
    if 'args' in c:
        return bytes.fromhex(c['args'])
    bps = c.get('bps')
    return b'\0' if bps is None else b'\1' + struct.pack('<Q', bps)


def setup(c):
    config_key = c.get('config_key', GLOBAL_CONFIG)
    signer = c.get('signer', ADMIN)
    metas = [AccountMeta(signer.pubkey(), not c.get('unsigned'), False),
             AccountMeta(config_key, False, not c.get('readonly'))]
    if not c.get('omit_event_metas'):
        metas += [AccountMeta(c.get('event_key', EVENT_AUTHORITY), False, False),
                  AccountMeta(c.get('program_key', AMM), False, False)]
    metas += [AccountMeta(k, False, False) for k in c.get('recipients', ())]
    metas = metas[:c.get('count', len(metas))]
    data = IX + args_bytes(c) + bytes.fromhex(c.get('trailing', ''))
    accounts = {config_key: Account(10**9, config_bytes(c), c.get('owner', AMM))}
    signers = [signer] if metas and metas[0].is_signer else []
    return config_key, accounts, metas, data, signers


def host_line(c):
    config_key, accounts, metas, data, _ = setup(c)
    config = accounts[config_key]
    flags = [len(metas) > 0 and metas[0].is_signer, config.owner == AMM, len(metas) > 1 and metas[1].is_writable,
             len(metas) > 2 and metas[2].pubkey == EVENT_AUTHORITY]
    signer = metas[0].pubkey if metas else ADMIN.pubkey()
    remaining = b''.join(bytes(m.pubkey) for m in metas[4:])
    return ','.join([str(min(len(metas), 4)), ''.join('1' if f else '0' for f in flags), data[8:].hex(),
                     bytes(config.data).hex(), bytes(signer).hex(), remaining.hex()])


def read_captured_image(path):
    image = path.read_bytes()
    if hashlib.sha256(image).hexdigest() != AMM_SHA256:
        raise ValueError('captured AMM hash mismatch')
    return image


@cache
def captured_image():
    return read_captured_image(AMM_ELF)


def run_captured(c):
    config_key, accounts, metas, data, signers = setup(c)
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program(AMM, captured_image())
    vm.airdrop(PAYER.pubkey(), 10**10)
    for key, account in accounts.items():
        vm.set_account(key, account)
    before = {k: vm.get_account(k) for k in accounts}
    tx = Transaction.new_signed_with_payer([Instruction(AMM, data, metas)], PAYER.pubkey(), [PAYER] + signers,
                                           vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = [l for l in meta.logs() if l.startswith('Program data: ')]
    cpi = [ix for group in meta.inner_instructions() for ix in group]
    after = {k: vm.get_account(k) for k in accounts}
    unchanged = all(
        (after[k].lamports, after[k].owner, after[k].executable, after[k].rent_epoch)
        == (before[k].lamports, before[k].owner, before[k].executable, before[k].rent_epoch)
        and (not failed or bytes(after[k].data) == bytes(before[k].data))
        and len(after[k].data) == len(before[k].data)
        for k in accounts)
    out = {'events': events, 'cpi': cpi, 'unchanged': unchanged}
    if failed:
        text = str(result.err())
        custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
        out['error'] = int(custom.group(1)) if custom else re.search(r'Fieldless\((\w+)\)', text).group(1)
        return out
    out.update(error=None, config=bytes(after[config_key].data))
    return out


EIGHT = RECIPIENTS[:8]


def fixed_cases():
    k = lambda **kw: dict(kw)
    cases = []
    for bps in (None, 0, 1, 2500, 9999, 10_000):
        for recipients in ((), EIGHT):
            cases.append(k(bps=bps, recipients=recipients))
    # Out-of-range basis points, with and without recipients and with a bad recipient list.
    for bps in (10_001, 65_535, 2**32, 2**63, 2**64 - 1):
        cases += [k(bps=bps), k(bps=bps, recipients=EIGHT), k(bps=bps, recipients=EIGHT[:3]),
                  k(bps=bps, recipients=[SYSTEM] + EIGHT[1:])]
    # Arguments are decoded first: a tag above 1 or a short payload is 102.
    cases += [k(args=''), k(args='02'), k(args='ff'), k(args='01'), k(args='01' + '00' * 7),
              k(args='02', unsigned=True), k(args='', count=0), k(args='01', owner=SYSTEM),
              k(trailing='ffeeddcc'), k(bps=5, trailing='aa'), k(args='00' + '01' * 8)]
    # Recipient count: only 0 or 8.
    cases += [k(recipients=RECIPIENTS[:n]) for n in (1, 2, 7, 9, 10)]
    cases += [k(bps=7, recipients=RECIPIENTS[:n]) for n in (1, 7, 9)]
    # Recipient contents.
    for at in (0, 3, 7):
        zero = list(EIGHT)
        zero[at] = SYSTEM
        cases += [k(recipients=zero), k(bps=1, recipients=zero)]
    cases += [k(recipients=[SYSTEM] * 8), k(recipients=[EIGHT[0]] * 8),
              k(recipients=EIGHT[:7] + [EIGHT[0]]), k(recipients=EIGHT[:6] + [EIGHT[5], EIGHT[7]]),
              k(recipients=[SYSTEM] + EIGHT[1:7] + [EIGHT[1]]), k(recipients=EIGHT[:7] + [SYSTEM]),
              k(recipients=[EIGHT[0], SYSTEM, EIGHT[0]] + EIGHT[3:]),
              k(recipients=[ADMIN.pubkey(), GLOBAL_CONFIG, AMM, PUMP] + EIGHT[4:]),
              k(recipients=list(reversed(EIGHT))), k(recipients=RECIPIENTS[2:10])]
    # Layout versions: the program reads all three, but writes back the 941 layout.
    for n in LENGTHS:
        cases += [k(length=n), k(length=n, bps=10), k(length=n, recipients=EIGHT), k(length=n + 1, bps=10),
                  k(length=n - 1), k(length=n, signer=OTHER), k(length=n, readonly=True),
                  k(length=n, bps=10_001), k(length=n, recipients=EIGHT[:2])]
    cases += [k(length=n) for n in (0, 7, 8, 100, 906, 948, 950, 1024)]
    cases += [k(length=1024, bps=3, recipients=EIGHT, patches=[(949, b'\xab' * 75)])]
    cases += [k(patches=[(0, b'\0')]), k(patches=[(7, b'\0')]), k(length=7, owner=SYSTEM)]
    # Bools are checked on load, only in the fields the version has.
    for at, versions in ((MAYHEM, LENGTHS), (CASHBACK, LENGTHS), (BOOST_ON, (940, 949)), (CFC, (949,))):
        for n in versions:
            cases += [k(length=n, patches=[(at, bytes([v]))]) for v in (2, 255)]
    cases += [k(length=939, patches=[(BOOST_ON, b'\x02')]), k(length=948, patches=[(CFC, b'\x07')])]
    # A bad bool fails on load, before `has_one` or the handler could fail.
    cases += [k(length=n, signer=OTHER, patches=[(BOOST_ON, b'\x02')]) for n in (940, 949)]
    cases += [k(length=949, bps=10_001, patches=[(CFC, b'\x02')])]
    # Owners, keys, signers and check order.
    cases += [k(owner=o) for o in (SYSTEM, PUMP)]
    cases += [k(config_key=STRAY), k(config_key=STRAY, bps=4, recipients=EIGHT), k(unsigned=True),
              k(readonly=True), k(signer=OTHER), k(admin=OTHER), k(admin=SYSTEM)]
    cases += [k(count=n, recipients=EIGHT) for n in range(5)]
    cases += [k(count=n) for n in range(4)]
    # The event authority is checked by seeds after `has_one`; the program meta is not checked.
    cases += [k(event_key=STRAY), k(event_key=AMM), k(event_key=GLOBAL_CONFIG, bps=1), k(program_key=STRAY),
              k(program_key=EVENT_AUTHORITY, bps=9, recipients=EIGHT), k(program_key=SYSTEM),
              k(event_key=STRAY, signer=OTHER), k(event_key=STRAY, readonly=True), k(event_key=STRAY, bps=10_001),
              k(event_key=STRAY, recipients=EIGHT[:3]), k(event_key=STRAY, length=907),
              k(count=3, signer=OTHER), k(count=3, readonly=True), k(count=3, length=100), k(count=2, owner=SYSTEM),
              k(count=3, patches=[(MAYHEM, b'\x02')])]
    cases += [k(count=1, unsigned=True), k(count=1, owner=SYSTEM), k(count=0, bps=10_001)]
    cases += [k(unsigned=True, owner=SYSTEM), k(owner=SYSTEM, readonly=True), k(readonly=True, signer=OTHER),
              k(readonly=True, length=100), k(readonly=True, patches=[(CASHBACK, b'\x02')]),
              k(signer=OTHER, bps=10_001), k(signer=OTHER, recipients=EIGHT[:3]), k(readonly=True, bps=10_001),
              k(signer=OTHER, length=907), k(length=907, recipients=[SYSTEM] * 8),
              k(length=940, recipients=EIGHT[:7] + [EIGHT[0]]), k(signer=OTHER, length=100)]
    # Existing values are overwritten wholesale.
    cases += [k(bps=b, patches=[(BPS, struct.pack('<Q', old))]) for b in (0, 10_000) for old in (0, 10_000, 2**64 - 1)]
    cases += [k(patches=[(BPS, struct.pack('<Q', 2**64 - 1))]),
              k(recipients=EIGHT, patches=[(BUYBACK_RECIPIENTS, b''.join(bytes(r) for r in EIGHT))])]
    return cases


def random_cases():
    rng = random.Random(20261030)
    cases = []
    for _ in range(200):
        c = {'mayhem': rng.randint(0, 1), 'cashback': rng.randint(0, 1), 'boost': rng.randint(0, 1),
             'cfc': rng.randint(0, 1)}
        r = rng.random()
        if r < 0.3:
            c['bps'] = None
        elif r < 0.75:
            c['bps'] = rng.randint(0, 10_000)
        elif r < 0.95:
            c['bps'] = rng.choice([10_001, rng.randint(10_001, 2**64 - 1)])
        else:
            c['args'] = rng.choice(['', '02', '01aa', 'ff00'])
        r = rng.random()
        if r < 0.45:
            pool = RECIPIENTS + [SYSTEM, ADMIN.pubkey()]
            picks = rng.sample(RECIPIENTS, 8)
            if rng.random() < 0.25:
                picks[rng.randrange(8)] = rng.choice(pool)
            c['recipients'] = picks
        elif r < 0.6:
            c['recipients'] = rng.sample(RECIPIENTS, rng.choice([1, 3, 7, 9, 10]))
        if rng.random() < 0.3:
            c['length'] = rng.choice([906, 907, 920, 939, 940, 945, 948, 949, 949, 960])
        if rng.random() < 0.1:
            c['patches'] = [(rng.choice([MAYHEM, CASHBACK, BOOST_ON, CFC]), bytes([rng.choice([2, 255])]))]
        for flag, p in (('unsigned', 0.05), ('readonly', 0.05)):
            if rng.random() < p:
                c[flag] = True
        if rng.random() < 0.06:
            c['signer'] = OTHER
        if rng.random() < 0.06:
            c['owner'] = rng.choice([SYSTEM, PUMP])
        if rng.random() < 0.08:
            c[rng.choice(['config_key', 'event_key', 'program_key'])] = STRAY
        if rng.random() < 0.04:
            c['count'] = rng.randint(0, 5)
        cases.append(c)
    return cases


class PumpAmmUpdateBuybackConfigCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured_image()
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'update-buyback-config-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(c) + '\n' for c in cases)
        answers = subprocess.run([str(self.host)], input=text, capture_output=True, text=True,
                                 check=True).stdout.splitlines()
        self.assertEqual(len(answers), len(cases))
        return answers

    def assert_matches(self, answer, captured):
        self.assertTrue(captured['unchanged'])
        self.assertEqual(captured['events'], [])
        self.assertEqual(captured['cpi'], [])
        if answer.startswith('error:'):
            code = answer[6:]
            self.assertEqual(captured['error'], int(code) if code.isdigit() else code)
            return
        self.assertTrue(answer.startswith('ok,'), 'unknown model outcome')
        self.assertIsNone(captured['error'])
        self.assertEqual(captured['config'], bytes.fromhex(answer[3:]))

    def run_cases(self, cases):
        for c, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=repr(c), host=answer[:80]):
                self.assert_matches(answer, run_captured(c))

    def test_rejects_wrong_image_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'wrong.so'
            wrong.write_bytes(b'not the captured AMM')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                read_captured_image(wrong)

    def test_admitted_image_is_used_after_source_path_moves(self):
        case = {'bps': 10, 'recipients': EIGHT}
        expected = run_captured(case)
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'replacement.so'
            wrong.write_bytes(b'wrong ELF')
            with patch(__name__ + '.AMM_ELF', wrong):
                self.assertEqual(run_captured(case), expected)

    def test_two_fixed_account_layout_is_rejected_by_captured_program(self):
        # This is the AdminGlobal-shaped list, not a truncation of the four-meta list.
        case = {'omit_event_metas': True, 'recipients': EIGHT, 'bps': 10}
        metas = setup(case)[2]
        self.assertEqual(len(metas), 10)
        self.assertEqual([meta.pubkey for meta in metas[2:]], EIGHT)
        answer = self.host_answers([case])[0]
        self.assertEqual(answer, 'error:2006')
        self.assert_matches(answer, run_captured(case))
        missing = {'omit_event_metas': True}
        self.assertEqual(len(setup(missing)[2]), 2)
        answer = self.host_answers([missing])[0]
        self.assertEqual(answer, 'error:3005')
        self.assert_matches(answer, run_captured(missing))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: each captured run must fail once the error or a config byte moves.
        samples = ({'bps': 10, 'recipients': EIGHT}, {'bps': None}, {'bps': 10_001}, {'recipients': EIGHT[:3]},
                   {'length': 940, 'bps': 1})
        flip = lambda h, i: h[:2 * i] + format(int(h[2 * i:2 * i + 2], 16) ^ 1, '02x') + h[2 * i + 2:]
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured)
            tampered = [dict(captured, unchanged=False), dict(captured, events=['Program data: AA==']),
                        dict(captured, cpi=['x'])]
            for t in tampered:  # metadata, a stray event or a CPI
                with self.assertRaises(AssertionError):
                    self.assert_matches(answer, t)
            if answer.startswith('ok,'):
                texts = ['ok,' + flip(answer[3:], at) for at in (BPS, BPS + 7, BUYBACK_RECIPIENTS, 898, 907, 948)]
                texts += ['error:6056']
            else:
                texts = [t for t in ('error:6005', 'error:6056', 'error:BorshIoError', 'ok,' + config_bytes(c).hex())
                         if t != answer]
            for text in texts:
                with self.subTest(case=repr(c), tampered=text[:40]), self.assertRaises(AssertionError):
                    self.assert_matches(text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        cases = fixed_cases()
        answers = self.host_answers(cases)
        self.assertEqual({a for a in answers if a.startswith('error:')}, {
            'error:102', 'error:2000', 'error:2006', 'error:3005', 'error:3007', 'error:3010', 'error:6005', 'error:6054',
            'error:6055', 'error:6056', 'error:6057', 'error:InvalidAccountData', 'error:BorshIoError'})
        self.assertGreater(sum(a.startswith('ok,') for a in answers), 20)


if __name__ == '__main__':
    unittest.main()
