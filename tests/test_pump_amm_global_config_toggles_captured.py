"""Captured-program checks for the PumpSwap `GlobalConfig` admin toggles.

Covers `disable`, `toggle_mayhem_mode`, `toggle_cashback_enabled` and
`toggle_boost`. Each case builds a synthetic `GlobalConfig` (899-, 932- or
941-byte layout, or something broken) and an instruction, runs it on
`evidence/original/pump_amm/deployed.so` in LiteSVM, and feeds the same bytes to
`programs/pump-amm/recovered/global_config_toggles_host.rs`. Owners, the signer
and writable flags and the event-authority / program addresses are worked out
here from the metas actually passed. The error (custom code or runtime error),
the committed config bytes, the `DisableEvent` in the log and the same bytes in
the `emit_cpi!` self-call must agree. Config metadata stays unchanged, and
failed transactions roll back its bytes. This is
matching behaviour on these inputs only, not a byte-identity claim.
"""
from pathlib import Path
import base64
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
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
AMM_ELF = ROOT / 'evidence/original/pump_amm/deployed.so'
AMM_SHA256 = '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7'
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/global_config_toggles_host.rs'

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.default()
CONFIG_DISC = hashlib.sha256(b'account:GlobalConfig').digest()[:8]
DISABLE_EVENT_DISC = hashlib.sha256(b'event:DisableEvent').digest()[:8]
IX = {name: hashlib.sha256(b'global:' + ix.encode()).digest()[:8] for name, ix in
      (('disable', 'disable'), ('mayhem', 'toggle_mayhem_mode'), ('cashback', 'toggle_cashback_enabled'),
       ('boost', 'toggle_boost'))}
ARGS = {'disable': 5, 'mayhem': 1, 'cashback': 1, 'boost': 1}
# Anchor's EVENT_IX_TAG, the u64 0x1d9acb512ea545e4 in little-endian order.
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
GLOBAL_CONFIG = Pubkey.find_program_address([b'global_config'], AMM)[0]
PAYER = Keypair.from_seed(bytes([241]) * 32)
ADMIN = Keypair.from_seed(bytes([242]) * 32)
OTHER = Keypair.from_seed(bytes([243]) * 32)
BOOST_AUTHORITY = Keypair.from_seed(bytes([244]) * 32).pubkey()
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
NOW = 1_761_810_000
LENGTHS = {'v899': 907, 'v932': 940, 'v941': 949}
MAYHEM, CASHBACK, FLAGS, BOOST_AUTH, BOOST_ON, CFC = 417, 642, 56, 907, 939, 940


def config_bytes(c):
    """A config with every non-bool byte set to a pattern, so a stray write shows."""
    n = c.get('length', 949)
    data = bytearray((i * 37 + 11) % 256 for i in range(max(n, 949)))
    data[:8] = CONFIG_DISC
    data[8:40] = bytes(c.get('admin', ADMIN.pubkey()))
    data[FLAGS] = c.get('flags', 0)
    data[MAYHEM] = c.get('mayhem', 0)
    data[CASHBACK] = c.get('cashback', 0)
    data[BOOST_AUTH:BOOST_AUTH + 32] = bytes(c.get('boost_authority', BOOST_AUTHORITY))
    data[BOOST_ON] = c.get('boost', 0)
    data[CFC] = c.get('cfc', 1)
    for at, value in c.get('patches', ()):
        data[at:at + len(value)] = value
    return bytes(data[:n])


def setup(c):
    kind = c['kind']
    config_key = c.get('config_key', GLOBAL_CONFIG)
    signer = c.get('signer', ADMIN)
    metas = [AccountMeta(signer.pubkey(), not c.get('unsigned'), False),
             AccountMeta(config_key, False, not c.get('readonly'))]
    if kind != 'boost' or c.get('event_metas'):
        metas += [AccountMeta(c.get('event_key', EVENT_AUTHORITY), False, False),
                  AccountMeta(c.get('program_key', AMM), False, False)]
    count = c.get('count', len(metas))
    if count > len(metas):
        metas.extend(AccountMeta(PAYER.pubkey(), False, False) for _ in range(count - len(metas)))
    metas = metas[:count]
    args = bytes.fromhex(c['args']) if 'args' in c else bytes([c.get('value', 1)]) * ARGS[kind]
    data = IX[kind] + args + bytes.fromhex(c.get('trailing', ''))
    accounts = {config_key: Account(10**9, config_bytes(c), c.get('owner', AMM))}
    signers = [signer] if metas and metas[0].is_signer else []
    return config_key, accounts, metas, data, signers


def host_line(c):
    config_key, accounts, metas, data, _ = setup(c)
    config = accounts[config_key]
    flags = [
        len(metas) > 0 and metas[0].is_signer,
        config.owner == AMM,
        len(metas) > 1 and metas[1].is_writable,
        len(metas) > 2 and metas[2].pubkey == EVENT_AUTHORITY,
        len(metas) > 3 and metas[3].pubkey == AMM,
    ]
    signer = metas[0].pubkey if metas else ADMIN.pubkey()
    return ','.join([c['kind'], str(len(metas)), ''.join('1' if f else '0' for f in flags), data[8:].hex(),
                     bytes(config.data).hex(), bytes(signer).hex(), str(NOW)])


def read_captured_image(path):
    image = path.read_bytes()
    if hashlib.sha256(image).hexdigest() != AMM_SHA256:
        raise ValueError('captured AMM hash mismatch')
    return image


@cache
def captured_image():
    """The immutable admitted image used for every case in this process."""
    return read_captured_image(AMM_ELF)


def run_captured(c):
    config_key, accounts, metas, data, signers = setup(c)
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program(AMM, captured_image())
    clock = vm.get_clock()
    vm.set_clock(Clock(clock.slot, clock.epoch_start_timestamp, clock.epoch, clock.leader_schedule_epoch, NOW))
    vm.airdrop(PAYER.pubkey(), 10**10)
    for key, account in accounts.items():
        vm.set_account(key, account)
    if c.get('program_key') == STRAY:
        vm.set_account(STRAY, Account(10**9, b'', SYSTEM))
    before = {k: vm.get_account(k) for k in accounts}
    tx = Transaction.new_signed_with_payer([Instruction(AMM, data, metas)], PAYER.pubkey(), [PAYER] + signers,
                                           vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = [base64.b64decode(l[len('Program data: '):]) for l in meta.logs() if l.startswith('Program data: ')]
    after = {k: vm.get_account(k) for k in accounts}
    unchanged = all(
        (after[k].lamports, after[k].owner, after[k].executable, after[k].rent_epoch)
        == (before[k].lamports, before[k].owner, before[k].executable, before[k].rent_epoch)
        and (not failed or bytes(after[k].data) == bytes(before[k].data))
        and len(after[k].data) == len(before[k].data)
        for k in accounts)
    cpi = [bytes(ix.instruction().data) for group in meta.inner_instructions() for ix in group]
    if failed:
        text = str(result.err())
        custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
        error = int(custom.group(1)) if custom else re.search(r'Fieldless\((\w+)\)', text).group(1)
        return {'error': error, 'events': events, 'cpi': cpi, 'unchanged': unchanged}
    return {'error': None, 'events': events, 'cpi': cpi, 'config': bytes(after[config_key].data),
            'unchanged': unchanged}


def fixed_cases():
    cases = []
    for kind in ('disable', 'mayhem', 'cashback', 'boost'):
        k = lambda **kw: dict(kind=kind, **kw)
        cases += [k(), k(value=0), k(trailing='ffeeddccbbaa'), k(count=5), k(count=6)]
        # Arguments are decoded first; a bool above 1 or a short payload is 102.
        cases += [k(args=''), k(args='02' * ARGS[kind]), k(args='ff' * ARGS[kind]), k(args='01' * (ARGS[kind] - 1)),
                  k(args='02', unsigned=True), k(args='', count=0), k(args='02', owner=SYSTEM)]
        # Layout versions: the program reads all three, but writes back the 941 layout.
        for name, n in LENGTHS.items():
            cases += [k(length=n), k(length=n, value=0), k(length=n + 1), k(length=n - 1)]
            cases += [k(length=n, signer=OTHER), k(length=n, readonly=True), k(length=n, boost_authority=SYSTEM)]
        cases += [k(length=n) for n in (0, 7, 8, 100, 906, 948, 950, 1024)]
        cases += [k(length=1024, patches=[(949, b'\xab' * 75)])]
        cases += [k(patches=[(0, b'\0')]), k(patches=[(7, b'\0')]), k(length=7, owner=SYSTEM),
                  k(owner=SYSTEM, patches=[(0, b'\0')])]
        # Bools are checked on load, only in the fields the version has.
        for at, versions in ((MAYHEM, (907, 940, 949)), (CASHBACK, (907, 940, 949)), (BOOST_ON, (940, 949)),
                             (CFC, (949,))):
            for n in versions:
                cases += [k(length=n, patches=[(at, bytes([v]))]) for v in (2, 255)]
        cases += [k(length=939, patches=[(BOOST_ON, b'\x02')]), k(length=948, patches=[(CFC, b'\x07')])]
        # Owners, keys, signers.
        cases += [k(owner=o) for o in (SYSTEM, PUMP)]
        cases += [k(config_key=STRAY), k(unsigned=True), k(readonly=True), k(signer=OTHER), k(admin=OTHER),
                  k(admin=SYSTEM), k(event_key=STRAY), k(event_key=AMM), k(program_key=STRAY),
                  k(program_key=EVENT_AUTHORITY), k(event_metas=True, event_key=STRAY)]
        cases += [k(count=n) for n in range(4)]
        cases += [k(count=1, unsigned=True), k(count=2, owner=SYSTEM), k(count=2, readonly=True),
                  k(count=3, signer=OTHER), k(count=2, length=100), k(count=3, patches=[(MAYHEM, b'\x02')])]
        # Check order across loading, constraints and the handler.
        cases += [k(unsigned=True, owner=SYSTEM), k(owner=SYSTEM, readonly=True), k(readonly=True, signer=OTHER),
                  k(readonly=True, length=100), k(readonly=True, patches=[(CASHBACK, b'\x02')]),
                  k(signer=OTHER, event_key=STRAY), k(readonly=True, event_key=STRAY),
                  k(event_key=STRAY, value=0), k(event_key=STRAY, boost_authority=SYSTEM),
                  k(signer=OTHER, length=907), k(signer=OTHER, boost_authority=SYSTEM),
                  k(event_key=STRAY, length=907), k(program_key=STRAY, length=907), k(program_key=STRAY, value=0),
                  k(readonly=True, length=907, value=0)]
        # Current states.
        for m in (0, 1):
            for cb in (0, 1):
                for b in (0, 1):
                    for value in (0, 1):
                        cases.append(k(mayhem=m, cashback=cb, boost=b, value=value))
        cases += [k(flags=f, args=a) for f in (0, 0x1f, 0x20, 0x40, 0x80, 0xff, 0xaa)
                  for a in ('0000000000', '0101010101', '0100010001', '0001000100')
                  if kind == 'disable']
        cases += [k(flags=0xff, value=1), k(flags=0xe0, value=0)]
    return cases


def random_cases():
    rng = random.Random(20261030)
    cases = []
    for _ in range(200):
        kind = rng.choice(['disable', 'mayhem', 'cashback', 'boost'])
        c = {'kind': kind, 'mayhem': rng.randint(0, 1), 'cashback': rng.randint(0, 1), 'boost': rng.randint(0, 1),
             'flags': rng.randint(0, 255)}
        c['args'] = ''.join(rng.choice(['00', '01', '01', '00', '02']) for _ in range(ARGS[kind]))
        if rng.random() < 0.3:
            c['length'] = rng.choice([906, 907, 920, 939, 940, 945, 948, 949, 949, 960])
        if rng.random() < 0.15:
            c['boost_authority'] = SYSTEM
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
            c[rng.choice(['event_key', 'program_key', 'config_key'])] = STRAY
        if rng.random() < 0.05:
            c['count'] = rng.randint(0, 5)
        cases.append(c)
    return cases


class PumpAmmGlobalConfigTogglesCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured_image()
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'global-config-toggles-host'
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
        if answer.startswith('error:'):
            code = answer[6:]
            self.assertEqual(captured['error'], int(code) if code.isdigit() else code)
            self.assertEqual(captured['events'], [])
            self.assertEqual(captured['cpi'], [])
            return
        if answer.startswith('event-then:'):
            name, event = answer[11:].split(',')
            self.assertEqual(captured['error'], name)
            self.assertEqual(captured['events'], [bytes.fromhex(event)])
            expected_cpi = [] if name == 'MissingAccount' else [EVENT_CPI_TAG + bytes.fromhex(event)]
            self.assertEqual(captured['cpi'], expected_cpi)
            return
        self.assertTrue(answer.startswith('ok,'), 'unknown model outcome')
        _, config, event = answer.split(',')
        self.assertIsNone(captured['error'])
        self.assertEqual(captured['config'], bytes.fromhex(config))
        expected = [bytes.fromhex(event)] if event else []
        self.assertEqual(captured['events'], expected)
        self.assertEqual(captured['cpi'], [EVENT_CPI_TAG + e for e in expected])

    def run_cases(self, cases):
        for c, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=repr(c), host=answer[:80]):
                self.assert_matches(answer, run_captured(c))

    def test_admitted_image_survives_path_replacement_and_rejects_wrong_bytes(self):
        case = {'kind': 'boost'}
        expected = run_captured(case)
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'wrong.so'
            wrong.write_bytes(b'not the captured AMM')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                read_captured_image(wrong)
            # Execution is bound to the admitted bytes even after this name moves.
            with patch(__name__ + '.AMM_ELF', wrong):
                self.assertEqual(run_captured(case), expected)

    def test_failed_self_cpi_observations_are_checked(self):
        cases = [{'kind': 'disable', 'program_key': STRAY},
                 {'kind': 'disable', 'length': 940}, {'kind': 'mayhem', 'length': 100}]
        for case, answer in zip(cases, self.host_answers(cases)):
            captured = run_captured(case)
            self.assert_matches(answer, captured)
            for altered in [[], [b'altered CPI data'], captured['cpi'] + [b'extra CPI']]:
                if altered == captured['cpi']:
                    continue
                with self.subTest(case=case, cpi=altered), self.assertRaises(AssertionError):
                    self.assert_matches(answer, dict(captured, cpi=altered))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_extra_account_case_really_supplies_more_metas(self):
        for kind in ('disable', 'boost'):
            case = {'kind': kind, 'count': 6}
            self.assertEqual(len(setup(case)[2]), 6)
            self.assert_matches(self.host_answers([case])[0], run_captured(case))

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: each captured run must fail once the error, a
        # config byte or an event byte moves.
        samples = ({'kind': 'disable'}, {'kind': 'mayhem'}, {'kind': 'boost'}, {'kind': 'cashback', 'value': 0},
                   {'kind': 'disable', 'program_key': STRAY}, {'kind': 'disable', 'length': 940},
                   {'kind': 'mayhem', 'length': 100})
        flip = lambda h, i: h[:2 * i] + format(int(h[2 * i:2 * i + 2], 16) ^ 1, '02x') + h[2 * i + 2:]
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured)
            with self.assertRaises(AssertionError):
                self.assert_matches(answer, dict(captured, unchanged=False))
            if answer.startswith('ok,'):
                _, config, event = answer.split(',')
                tampered = ['ok,' + flip(config, at) + ',' + event for at in (FLAGS, MAYHEM, CASHBACK, BOOST_ON, 948)]
                tampered += ['error:6005', 'ok,' + config + ',' + (flip(event, 8) if event else '00')]
                if event:
                    tampered += ['ok,' + config + ',' + flip(event, 52), 'ok,' + config + ',']
            elif answer.startswith('event-then:'):
                name, event = answer[11:].split(',')
                tampered = ['event-then:' + name + ',' + flip(event, 52), 'error:' + name,
                            'event-then:' + ('BorshIoError' if name == 'MissingAccount' else 'MissingAccount') + ',' + event]
            else:
                tampered = ['error:6043', 'error:BorshIoError']
            for text in tampered:
                with self.subTest(case=repr(c), tampered=text[:60]):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        cases = fixed_cases()
        answers = self.host_answers(cases)
        self.assertEqual({a for a in answers if a.startswith('error:')}, {
            'error:102', 'error:2000', 'error:2006', 'error:3005', 'error:3007', 'error:3010', 'error:6005',
            'error:6043', 'error:6051', 'error:InvalidAccountData', 'error:BorshIoError'})
        self.assertEqual({a.split(',')[0] for a in answers if a.startswith('event-then:')},
                         {'event-then:MissingAccount', 'event-then:BorshIoError'})
        for kind in ARGS:
            self.assertGreater(sum(a.startswith('ok,') for c, a in zip(cases, answers) if c['kind'] == kind), 10)


if __name__ == '__main__':
    unittest.main()
