"""Captured-program checks for PumpSwap `update_admin`.

Each case builds a synthetic `GlobalConfig` (899-, 932- or 941-byte layout, or
something broken) and the five accounts (`admin`, `global_config`, `new_admin`,
`event_authority`, `program`), runs the instruction on
`evidence/original/pump_amm/deployed.so` in LiteSVM, and feeds the same bytes to
`programs/pump-amm/recovered/update_admin_host.rs`. The instruction takes no
Borsh arguments; the new admin is the third account's address. Owners, the
signer and writable flags and the event-authority / program addresses are
worked out here from the metas actually passed. The error (custom code, and for
3005 the account named in the Anchor log), the committed config bytes, the
`UpdateAdminEvent` in the log and the same bytes in the `emit_cpi!` self-call
must agree. Config metadata stays unchanged, and failed transactions roll back
its bytes. This is matching behaviour on these inputs only, not a byte-identity
claim.
"""
from pathlib import Path
import base64
import hashlib
from functools import cache
import random
import re
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
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/update_admin_host.rs'

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.default()
CONFIG_DISC = hashlib.sha256(b'account:GlobalConfig').digest()[:8]
EVENT_DISC = hashlib.sha256(b'event:UpdateAdminEvent').digest()[:8]
IX = hashlib.sha256(b'global:update_admin').digest()[:8]
# Anchor's EVENT_IX_TAG, the u64 0x1d9acb512ea545e4 in little-endian order.
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
GLOBAL_CONFIG = Pubkey.find_program_address([b'global_config'], AMM)[0]
PAYER = Keypair.from_seed(bytes([241]) * 32)
ADMIN = Keypair.from_seed(bytes([242]) * 32)
OTHER = Keypair.from_seed(bytes([243]) * 32)
NEW = Keypair.from_seed(bytes([244]) * 32)
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
NOW = 1_700_000_123
LENGTHS = (907, 940, 949)
MAYHEM, CASHBACK, BOOST_ON, CFC = 417, 642, 939, 940
ADMIN_AT = 8
NEAR = Pubkey.from_bytes(bytes(ADMIN.pubkey())[:-1] + bytes([bytes(ADMIN.pubkey())[-1] ^ 0xff]))
KEYS = (NEW.pubkey(), ADMIN.pubkey(), SYSTEM, STRAY, AMM, PUMP, GLOBAL_CONFIG, PAYER.pubkey(),
        OTHER.pubkey(), NEAR)


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
        end = min(at + len(value), len(data))
        if at < end:
            data[at:end] = value[:end - at]
    return bytes(data[:n])


def setup(c):
    config_key = c.get('config_key', GLOBAL_CONFIG)
    signer = c.get('signer', ADMIN)
    new_admin = c.get('new_admin', NEW.pubkey())
    metas = [AccountMeta(signer.pubkey(), not c.get('unsigned'), c.get('admin_writable', False)),
             AccountMeta(config_key, False, not c.get('readonly')),
             AccountMeta(new_admin, c.get('new_signer', False), c.get('new_writable', False)),
             AccountMeta(c.get('event_key', EVENT_AUTHORITY), False, c.get('event_writable', False)),
             AccountMeta(c.get('program_key', AMM), False, c.get('program_writable', False))]
    count = c.get('count', len(metas))
    if count > len(metas):
        extra = c.get('extra', PAYER.pubkey())
        metas.extend(AccountMeta(extra, False, False) for _ in range(count - len(metas)))
    metas = metas[:count]
    data = c['data'] if 'data' in c else IX + bytes.fromhex(c.get('trailing', ''))
    accounts = {config_key: Account(10**9, config_bytes(c), c.get('owner', AMM))}
    signers = []
    if metas and metas[0].is_signer:
        signers.append(signer)
    if any(m.is_signer and m.pubkey == NEW.pubkey() for m in metas) and all(s.pubkey() != NEW.pubkey() for s in signers):
        signers.append(NEW)
    return config_key, accounts, metas, data, signers


def host_line(c):
    config_key, accounts, metas, data, _ = setup(c)
    config = accounts[config_key]
    flags = [
        len(metas) > 0 and metas[0].is_signer,
        config.owner == AMM,
        len(metas) > 1 and metas[1].is_writable,
        len(metas) > 3 and metas[3].pubkey == EVENT_AUTHORITY,
        len(metas) > 4 and metas[4].pubkey == AMM,
    ]
    signer = metas[0].pubkey if metas else ADMIN.pubkey()
    new_admin = metas[2].pubkey if len(metas) > 2 else SYSTEM
    return ','.join([str(len(metas)), ''.join('1' if flag else '0' for flag in flags), data.hex(),
                     bytes(config.data).hex(), bytes(signer).hex(), bytes(new_admin).hex(),
                     str(c.get('now', NOW))])


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
    clock = vm.get_clock()
    vm.set_clock(Clock(clock.slot, clock.epoch_start_timestamp, clock.epoch, clock.leader_schedule_epoch,
                       c.get('now', NOW)))
    vm.airdrop(PAYER.pubkey(), 10**10)
    for key, account in accounts.items():
        vm.set_account(key, account)
    if c.get('program_key') == STRAY and STRAY != config_key:
        vm.set_account(STRAY, Account(10**9, b'', SYSTEM))
    before = {k: vm.get_account(k) for k in accounts}
    tx = Transaction.new_signed_with_payer([Instruction(AMM, data, metas)], PAYER.pubkey(), [PAYER] + signers,
                                           vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = [base64.b64decode(line[len('Program data: '):]) for line in meta.logs() if line.startswith('Program data: ')]
    logs = '\n'.join(meta.logs())
    after = {k: vm.get_account(k) for k in accounts}
    unchanged = all(
        (after[k].lamports, after[k].owner, after[k].executable, after[k].rent_epoch)
        == (before[k].lamports, before[k].owner, before[k].executable, before[k].rent_epoch)
        and (not failed or bytes(after[k].data) == bytes(before[k].data))
        and len(after[k].data) == len(before[k].data)
        for k in accounts)
    cpi = [bytes(ix.instruction().data) for group in meta.inner_instructions() for ix in group]
    out = {'events': events, 'cpi': cpi, 'unchanged': unchanged, 'logs': logs}
    if failed:
        text = str(result.err())
        custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
        out['error'] = int(custom.group(1)) if custom else re.search(r'Fieldless\((\w+)\)', text).group(1)
        return out
    out.update(error=None, config=bytes(after[config_key].data))
    return out


def fixed_cases():
    k = lambda **kw: dict(kw)
    cases = []
    # Any address can become the admin, including the current one, the zero key
    # and the config account itself. Trailing bytes are not the new admin.
    for key in KEYS:
        cases += [k(new_admin=key), k(new_admin=key, trailing='ffeeddcc')]
    cases += [k(trailing=bytes(STRAY).hex()), k(trailing='ab' * 64), k(trailing='00' * 32),
              k(count=6), k(count=7), k(count=8, extra=STRAY), k(config_key=STRAY),
              k(config_key=STRAY, new_admin=STRAY), k(config_key=STRAY, new_admin=SYSTEM),
              k(admin_writable=True), k(new_writable=True), k(new_signer=True),
              k(event_writable=True), k(program_writable=True),
              k(new_writable=True, new_signer=True, admin_writable=True)]
    # Layouts the program can write back, including bytes past the struct.
    cases += [k(length=949), k(length=950), k(length=960, new_admin=SYSTEM),
              k(length=1024, new_admin=NEAR), k(length=1024, patches=[(949, b'\xab' * 75)])]
    for mayhem, cashback, boost, cfc in ((0, 0, 0, 0), (1, 1, 1, 1), (1, 0, 1, 0), (0, 1, 0, 1)):
        cases.append(k(mayhem=mayhem, cashback=cashback, boost=boost, cfc=cfc, new_admin=SYSTEM))
    # The clock is copied into the event as a signed little-endian i64.
    for now in (0, -1, -5, 1, 2**31 - 1, -(2**31), 2**62, NOW):
        cases.append(k(now=now, new_admin=PUMP))
    # A non-bool byte next to the admin key is left alone.
    cases += [k(patches=[(56, b'\xff')]), k(patches=[(40, b'\x11' * 8)])]
    # Dispatch fails before accounts. The discriminator is 8 bytes; the rest is ignored.
    short = [b'', IX[:1], IX[:7], bytes(8), IX[:-1] + bytes([IX[-1] ^ 1]), b'\xff' * 8, IX[:4]]
    cases += [k(data=d) for d in short]
    cases += [k(data=b'', count=0), k(data=b'', unsigned=True), k(data=bytes(8), owner=SYSTEM),
              k(data=IX[:7], readonly=True), k(data=IX[:3], signer=OTHER), k(data=b'\x00' * 9)]
    # Account load order. 3005 names the first meta that is missing.
    cases += [k(count=n) for n in range(6)]
    cases += [k(count=0, unsigned=True), k(count=0, length=10), k(count=1, unsigned=True),
              k(count=1, patches=[(MAYHEM, b'\x02')]), k(count=1, owner=SYSTEM),
              k(count=2, readonly=True), k(count=2, signer=OTHER), k(count=2, patches=[(MAYHEM, b'\x02')]),
              k(count=2, length=100), k(count=2, patches=[(0, b'\x00')]), k(count=2, owner=SYSTEM),
              k(count=3, readonly=True), k(count=3, signer=OTHER), k(count=3, patches=[(CASHBACK, b'\x02')]),
              k(count=3, event_key=STRAY), k(count=4, readonly=True), k(count=4, signer=OTHER),
              k(count=4, event_key=STRAY), k(count=4, patches=[(MAYHEM, b'\x02')]),
              k(count=4, owner=SYSTEM), k(count=4, length=100)]
    # Owners, signers, mut, has_one, seeds. Later failures do not hide earlier ones.
    cases += [k(owner=o) for o in (SYSTEM, PUMP)]
    cases += [k(unsigned=True), k(readonly=True), k(signer=OTHER), k(admin=OTHER.pubkey()),
              k(admin=SYSTEM), k(admin=STRAY), k(patches=[(8, b'\x00' * 32)])]
    cases += [k(event_key=key) for key in (STRAY, AMM, GLOBAL_CONFIG, PUMP, SYSTEM)]
    cases += [k(program_key=key) for key in (STRAY, PUMP, EVENT_AUTHORITY, SYSTEM, GLOBAL_CONFIG)]
    cases += [k(unsigned=True, owner=SYSTEM), k(unsigned=True, readonly=True), k(unsigned=True, signer=OTHER),
              k(owner=SYSTEM, readonly=True), k(owner=SYSTEM, signer=OTHER), k(owner=PUMP, patches=[(MAYHEM, b'\x02')]),
              k(readonly=True, signer=OTHER), k(readonly=True, event_key=STRAY), k(readonly=True, length=907),
              k(signer=OTHER, event_key=STRAY), k(signer=OTHER, program_key=STRAY),
              k(event_key=STRAY, program_key=STRAY), k(event_key=STRAY, length=940),
              k(program_key=STRAY, length=907), k(program_key=STRAY, length=949),
              k(program_key=STRAY, new_admin=STRAY), k(program_key=PUMP, length=948),
              k(readonly=True, program_key=STRAY), k(count=3, owner=SYSTEM)]
    # Config read. Under 907 bytes, or a wrong discriminator, is InvalidAccountData.
    # A bool above 1 is a load error only in a field the layout has.
    for n in (0, 7, 8, 100, 417, 906, 939, 948, 949, 950, 1024):
        cases.append(k(length=n))
    cases += [k(length=n, new_admin=SYSTEM) for n in (906, 907, 939, 940, 948, 949)]
    cases += [k(patches=[(0, b'\x00')]), k(patches=[(7, b'\x00')]), k(length=7, owner=SYSTEM),
              k(length=906, patches=[(MAYHEM, b'\x02')]), k(length=906, patches=[(0, b'\x00')]),
              k(patches=[(0, b'\x00'), (MAYHEM, b'\x02')])]
    for at, versions in ((MAYHEM, LENGTHS), (CASHBACK, LENGTHS), (BOOST_ON, (940, 949)), (CFC, (949,))):
        for n in versions:
            cases += [k(length=n, patches=[(at, bytes([v]))]) for v in (2, 255)]
    # A byte the layout does not treat as a bool is not a load error.
    cases += [k(length=939, patches=[(BOOST_ON, b'\x02')]), k(length=948, patches=[(CFC, b'\x07')]),
              k(length=948, patches=[(CFC, b'\x02')], signer=OTHER),
              k(length=940, patches=[(BOOST_ON, b'\x02')], readonly=True)]
    cases += [k(patches=[(MAYHEM, b'\x02')], unsigned=True), k(patches=[(MAYHEM, b'\x02')], owner=SYSTEM),
              k(patches=[(CASHBACK, b'\x02')], readonly=True), k(patches=[(CASHBACK, b'\x02')], signer=OTHER),
              k(patches=[(CFC, b'\x02')], event_key=STRAY), k(patches=[(BOOST_ON, b'\x02')], program_key=STRAY),
              k(patches=[(MAYHEM, b'\xff')], length=907), k(count=2, length=940, patches=[(BOOST_ON, b'\x02')])]
    return cases


def random_cases():
    rng = random.Random(20261030)
    cases = []
    for _ in range(200):
        c = {'mayhem': rng.randint(0, 1), 'cashback': rng.randint(0, 1), 'boost': rng.randint(0, 1),
             'cfc': rng.randint(0, 1), 'new_admin': rng.choice(KEYS)}
        roll = rng.random()
        if roll < 0.12:
            c['data'] = rng.choice([b'', IX[:7], bytes(8), IX[:-1] + bytes([IX[-1] ^ 1]), b'\xff' * 4, IX[:2]])
        elif roll < 0.22:
            c['trailing'] = rng.randbytes(rng.randint(1, 24)).hex()
        if rng.random() < 0.28:
            c['length'] = rng.choice([0, 8, 100, 906, 907, 920, 939, 940, 948, 949, 950, 960, 1024])
        if rng.random() < 0.08:
            c['patches'] = [(rng.choice([MAYHEM, CASHBACK, BOOST_ON, CFC]), bytes([rng.choice([2, 255])]))]
        if rng.random() < 0.04:
            c['patches'] = [(0, bytes([rng.randrange(256)]))]
        for flag, prob in (('unsigned', 0.05), ('readonly', 0.05), ('new_signer', 0.03),
                           ('new_writable', 0.03), ('admin_writable', 0.02),
                           ('event_writable', 0.02), ('program_writable', 0.02)):
            if rng.random() < prob:
                c[flag] = True
        if c.get('new_signer'):
            c['new_admin'] = NEW.pubkey()
        if rng.random() < 0.05:
            c['signer'] = OTHER
        if rng.random() < 0.04:
            c['admin'] = rng.choice([OTHER.pubkey(), SYSTEM, STRAY])
        if rng.random() < 0.05:
            c['owner'] = rng.choice([SYSTEM, PUMP])
        if rng.random() < 0.05:
            c['config_key'] = STRAY
        if rng.random() < 0.05 and c.get('config_key') != STRAY:
            c['program_key'] = rng.choice([STRAY, PUMP, SYSTEM, EVENT_AUTHORITY])
        if rng.random() < 0.05:
            c['event_key'] = rng.choice([STRAY, AMM, PUMP, SYSTEM])
        if rng.random() < 0.05:
            c['count'] = rng.randint(0, 7)
        if rng.random() < 0.04:
            c['now'] = rng.choice([0, -1, 42, 2**31 - 1, -(2**31)])
        cases.append(c)
    return cases


class PumpAmmUpdateAdminCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured_image()
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'update-admin-host'
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
            rest = answer[6:]
            if rest.startswith('3005,'):
                code, site = rest.split(',')
                self.assertEqual(captured['error'], int(code))
                self.assertIn(f'caused by account: {site}', captured['logs'])
            else:
                self.assertEqual(captured['error'], int(rest) if rest.isdigit() else rest)
            self.assertEqual(captured['events'], [])
            self.assertEqual(captured['cpi'], [])
            return
        if answer.startswith('event-then:'):
            name, event = answer[11:].split(',')
            self.assertEqual(captured['error'], name)
            self.assertEqual(captured['events'], [bytes.fromhex(event)])
            expected_cpi = [] if name == 'MissingAccount' else [EVENT_CPI_TAG + bytes.fromhex(event)]
            self.assertEqual(captured['cpi'], expected_cpi)
            self.assertEqual(bytes.fromhex(event)[:8], EVENT_DISC)
            self.assertEqual(len(event) // 2, 80)
            return
        self.assertTrue(answer.startswith('ok,'), 'unknown model outcome')
        _, config, event = answer.split(',')
        self.assertIsNone(captured['error'])
        self.assertEqual(captured['config'], bytes.fromhex(config))
        self.assertEqual(captured['events'], [bytes.fromhex(event)])
        self.assertEqual(captured['cpi'], [EVENT_CPI_TAG + bytes.fromhex(event)])
        raw = bytes.fromhex(event)
        self.assertEqual(raw[:8], EVENT_DISC)
        self.assertEqual(len(raw), 80)
        self.assertEqual(captured['config'][ADMIN_AT:ADMIN_AT + 32], raw[48:80])

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
        case = {'new_admin': SYSTEM}
        expected = run_captured(case)
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'replacement.so'
            wrong.write_bytes(b'wrong ELF')
            with patch(__name__ + '.AMM_ELF', wrong):
                self.assertEqual(run_captured(case), expected)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_extra_account_case_really_supplies_more_metas(self):
        case = {'count': 6, 'new_admin': SYSTEM, 'trailing': bytes(STRAY).hex()}
        _, _, metas, data, _ = setup(case)
        self.assertEqual(len(metas), 6)
        self.assertEqual(metas[2].pubkey, SYSTEM)
        self.assertTrue(data.endswith(bytes(STRAY)))
        answer = self.host_answers([case])[0]
        self.assert_matches(answer, run_captured(case))
        event = bytes.fromhex(answer.split(',')[2])
        self.assertEqual(event[48:80], bytes(SYSTEM))
        self.assertNotEqual(event[48:80], bytes(STRAY))

    def test_checker_rejects_tampered_outcomes(self):
        samples = ({'new_admin': SYSTEM}, {'new_admin': ADMIN.pubkey()}, {'data': b''}, {'count': 0},
                   {'count': 2}, {'count': 4, 'event_key': STRAY}, {'unsigned': True}, {'owner': SYSTEM},
                   {'readonly': True}, {'signer': OTHER}, {'event_key': STRAY}, {'program_key': STRAY},
                   {'length': 907}, {'length': 100}, {'patches': [(MAYHEM, b'\x02')]})
        flip = lambda h, i: h[:2 * i] + format(int(h[2 * i:2 * i + 2], 16) ^ 1, '02x') + h[2 * i + 2:]
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured)
            with self.assertRaises(AssertionError):
                self.assert_matches(answer, dict(captured, unchanged=False))
            if answer.startswith('ok,'):
                _, config, event = answer.split(',')
                tampered = ['ok,' + flip(config, ADMIN_AT) + ',' + event, 'ok,' + flip(config, 40) + ',' + event,
                            'ok,' + config + ',' + flip(event, 8), 'ok,' + config + ',' + flip(event, 16),
                            'ok,' + config + ',' + flip(event, 48), 'error:6005', 'ok,' + config + ',']
            elif answer.startswith('event-then:'):
                name, event = answer[11:].split(',')
                tampered = ['event-then:' + name + ',' + flip(event, 16), 'error:' + name,
                            'event-then:' + ('BorshIoError' if name == 'MissingAccount' else 'MissingAccount') + ',' + event,
                            'event-then:' + name + ',' + flip(event, 48)]
            elif answer.startswith('error:3005,'):
                site = answer.split(',')[1]
                other = next(name for name in ('admin', 'global_config', 'new_admin', 'event_authority', 'program')
                             if name != site)
                tampered = ['error:3005,' + other, 'error:3010', 'error:2000', 'error:101']
            else:
                tampered = [text for text in ('error:101', 'error:2000', 'error:2006', 'error:3005,admin',
                                              'error:3007', 'error:3010', 'error:6005', 'error:BorshIoError',
                                              'error:InvalidAccountData') if text != answer]
            for text in tampered:
                with self.subTest(case=repr(c), tampered=text[:60]), self.assertRaises(AssertionError):
                    self.assert_matches(text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        cases = fixed_cases()
        answers = self.host_answers(cases)
        self.assertEqual({a for a in answers if a.startswith('error:')}, {
            'error:101', 'error:2000', 'error:2006', 'error:3005,admin', 'error:3005,global_config',
            'error:3005,new_admin', 'error:3005,event_authority', 'error:3005,program', 'error:3007',
            'error:3010', 'error:6005', 'error:InvalidAccountData', 'error:BorshIoError'})
        self.assertEqual({a.split(',')[0] for a in answers if a.startswith('event-then:')},
                         {'event-then:MissingAccount', 'event-then:BorshIoError'})
        self.assertGreater(sum(a.startswith('ok,') for a in answers), 20)


if __name__ == '__main__':
    unittest.main()
