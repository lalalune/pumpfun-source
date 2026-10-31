"""Captured-program checks for PumpSwap `update_fee_config`.

Each case builds a synthetic `GlobalConfig` (899-, 932- or 941-byte layout, or
something broken) and the five Borsh arguments (lp bps, protocol bps, eight
protocol-fee recipients, creator bps, fee authority), runs the instruction on
`evidence/original/pump_amm/deployed.so` in LiteSVM, and feeds the same bytes to
`programs/pump-amm/recovered/update_fee_config_host.rs`. Owners, the signer and
writable flags and the event-authority / program addresses are worked out here
from the metas actually passed. The error (custom code, and for 6000 the fee
field named in the Anchor log), the committed config bytes, the
`UpdateFeeConfigEvent` in the log and the same bytes in the `emit_cpi!`
self-call must agree. Config metadata stays unchanged, and failed transactions
roll back its bytes. This is matching behaviour on these inputs only, not a
byte-identity claim.
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
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/update_fee_config_host.rs'

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.default()
CONFIG_DISC = hashlib.sha256(b'account:GlobalConfig').digest()[:8]
EVENT_DISC = hashlib.sha256(b'event:UpdateFeeConfigEvent').digest()[:8]
IX = hashlib.sha256(b'global:update_fee_config').digest()[:8]
# Anchor's EVENT_IX_TAG, the u64 0x1d9acb512ea545e4 in little-endian order.
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
GLOBAL_CONFIG = Pubkey.find_program_address([b'global_config'], AMM)[0]
PAYER = Keypair.from_seed(bytes([251]) * 32)
ADMIN = Keypair.from_seed(bytes([252]) * 32)
OTHER = Keypair.from_seed(bytes([253]) * 32)
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
AUTHORITY = Pubkey.from_bytes(bytes([0x63]) * 32)
NOW = 1_700_000_123
LENGTHS = (907, 940, 949)
MAYHEM, CASHBACK, BOOST_ON, CFC = 417, 642, 939, 940
LP, PROTOCOL, RECIPIENTS, CREATOR, FEE_AUTHORITY = 40, 48, 57, 313, 321
# The three 6000 sites, as logged by the captured program.
FEE_SITE = {
    'lp': 'programs/pump-amm/src/state/global_config.rs:220',
    'protocol': 'programs/pump-amm/src/state/global_config.rs:230',
    'creator': 'programs/pump-amm/src/state/global_config.rs:243',
}
SORTED = [Pubkey.from_bytes(bytes([i + 1]) * 32) for i in range(8)]
PREFIXED = []
for _i in range(8):
    raw = bytearray(b'\x11' * 32)
    raw[31] = _i + 1
    PREFIXED.append(Pubkey.from_bytes(bytes(raw)))


def with_at(keys, index, key):
    out = list(keys)
    out[index] = key
    return out


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
    recipients = c.get('recipients', SORTED)
    authority = c.get('authority', AUTHORITY)
    return (struct.pack('<QQ', c.get('lp', 20), c.get('proto', 5))
            + b''.join(bytes(key) for key in recipients)
            + struct.pack('<Q', c.get('creator', 5)) + bytes(authority))


def setup(c):
    config_key = c.get('config_key', GLOBAL_CONFIG)
    signer = c.get('signer', ADMIN)
    metas = [AccountMeta(signer.pubkey(), not c.get('unsigned'), False),
             AccountMeta(config_key, False, not c.get('readonly'))]
    if not c.get('omit_event_metas'):
        metas += [AccountMeta(c.get('event_key', EVENT_AUTHORITY), False, False),
                  AccountMeta(c.get('program_key', AMM), False, False)]
    count = c.get('count', len(metas))
    if count > len(metas):
        metas.extend(AccountMeta(PAYER.pubkey(), False, False) for _ in range(count - len(metas)))
    metas = metas[:count]
    data = IX + args_bytes(c) + bytes.fromhex(c.get('trailing', ''))
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
    return ','.join([str(len(metas)), ''.join('1' if flag else '0' for flag in flags), data[8:].hex(),
                     bytes(config.data).hex(), bytes(signer).hex(), str(NOW)])


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
    # In-range fees, including the inclusive bound of 1000, and a zero authority.
    for lp, proto, creator in ((0, 0, 0), (1, 2, 3), (20, 5, 5), (1000, 0, 1000), (0, 1000, 1),
                               (1000, 1000, 1000), (999, 1000, 0)):
        cases += [k(lp=lp, proto=proto, creator=creator), k(lp=lp, proto=proto, creator=creator, authority=SYSTEM)]
    cases += [k(recipients=PREFIXED), k(recipients=PREFIXED, authority=ADMIN.pubkey()),
              k(recipients=PREFIXED, lp=1000, proto=1000, creator=1000),
              k(authority=GLOBAL_CONFIG), k(authority=STRAY), k(trailing='ffeeddcc'), k(count=5), k(count=6)]
    # Each fee field rejects 1001 and above. The field is named in the log.
    for name, big in (('lp', {'lp': 1001}), ('proto', {'proto': 1001}), ('creator', {'creator': 1001})):
        for value in (1001, 1002, 65_535, 2**32, 2**64 - 1):
            over = dict(big)
            over[name] = value
            cases.append(k(**over))
    # Check order: lp, protocol, recipients (zero then strictly ascending), creator.
    cases += [k(lp=1001, proto=1001), k(lp=1001, recipients=list(reversed(SORTED))),
              k(lp=1001, recipients=with_at(SORTED, 0, SYSTEM)), k(lp=1001, creator=1001),
              k(proto=1001, recipients=list(reversed(SORTED))), k(proto=1001, recipients=with_at(SORTED, 3, SYSTEM)),
              k(proto=1001, creator=1001), k(creator=1001, recipients=list(reversed(SORTED))),
              k(creator=1001, recipients=with_at(SORTED, 7, SYSTEM)), k(creator=1001),
              k(lp=1001, proto=1001, creator=1001, recipients=[SYSTEM] * 8)]
    # A leading zero still sorts; a trailing zero does not. Zero is reported first either way.
    cases += [k(recipients=with_at(SORTED, i, SYSTEM)) for i in (0, 3, 7)]
    cases += [k(recipients=[SYSTEM] + SORTED[1:]), k(recipients=SORTED[:7] + [SYSTEM]),
              k(recipients=[SYSTEM] * 8), k(recipients=[SYSTEM, SORTED[1], SORTED[1]] + SORTED[3:])]
    # Unsorted or duplicated non-zero keys, including order that lives past the first byte.
    swapped = list(PREFIXED)
    swapped[2], swapped[3] = swapped[3], swapped[2]
    cases += [k(recipients=list(reversed(SORTED))), k(recipients=list(reversed(PREFIXED))), k(recipients=swapped),
              k(recipients=with_at(SORTED, 0, SORTED[1])), k(recipients=with_at(SORTED, 4, SORTED[3])),
              k(recipients=with_at(SORTED, 7, SORTED[6])), k(recipients=[SORTED[0]] * 8),
              k(recipients=SORTED[:6] + [SORTED[5], SORTED[7]])]
    # Arguments are decoded first.
    cases += [k(args=''), k(args='00' * 311), k(args='ff' * 8), k(args='01'),
              k(args='', unsigned=True), k(args='', count=0), k(args='00' * 311, owner=SYSTEM),
              k(trailing='aa' * 16), k(args=args_bytes({}).hex() + 'ab')]
    # Layout versions: the program reads all three, but writes back the 941 layout.
    for n in LENGTHS:
        cases += [k(length=n), k(length=n, lp=10, proto=20, creator=30), k(length=n + 1), k(length=n - 1),
                  k(length=n, signer=OTHER), k(length=n, readonly=True), k(length=n, lp=1001),
                  k(length=n, recipients=list(reversed(SORTED))), k(length=n, recipients=with_at(SORTED, 0, SYSTEM))]
    cases += [k(length=n) for n in (0, 7, 8, 100, 906, 939, 948, 950, 1024)]
    cases += [k(length=1024, patches=[(949, b'\xab' * 75)]), k(length=950, lp=0, proto=0, creator=0)]
    cases += [k(patches=[(0, b'\0')]), k(patches=[(7, b'\0')]), k(length=7, owner=SYSTEM)]
    # Bools are checked on load, only in the fields the version has.
    for at, versions in ((MAYHEM, LENGTHS), (CASHBACK, LENGTHS), (BOOST_ON, (940, 949)), (CFC, (949,))):
        for n in versions:
            cases += [k(length=n, patches=[(at, bytes([v]))]) for v in (2, 255)]
    cases += [k(length=939, patches=[(BOOST_ON, b'\x02')]), k(length=948, patches=[(CFC, b'\x07')]),
              k(length=948, patches=[(CFC, b'\x02')], lp=1001)]
    # A bad bool fails on load, after the signer and the owner, before later constraints.
    cases += [k(patches=[(MAYHEM, b'\x02')], unsigned=True), k(patches=[(MAYHEM, b'\x02')], owner=SYSTEM),
              k(patches=[(CASHBACK, b'\x02')], readonly=True), k(patches=[(CASHBACK, b'\x02')], signer=OTHER),
              k(patches=[(CFC, b'\x02')], lp=1001), k(count=3, patches=[(MAYHEM, b'\x02')]),
              k(length=940, patches=[(BOOST_ON, b'\x02')], readonly=True)]
    # Owners, keys, signers and check order.
    cases += [k(owner=o) for o in (SYSTEM, PUMP)]
    cases += [k(config_key=STRAY), k(config_key=STRAY, lp=7, proto=8, creator=9), k(unsigned=True),
              k(readonly=True), k(signer=OTHER), k(admin=OTHER), k(admin=SYSTEM)]
    cases += [k(count=n) for n in range(6)]
    cases += [k(event_key=STRAY), k(event_key=AMM), k(event_key=GLOBAL_CONFIG), k(program_key=STRAY),
              k(program_key=EVENT_AUTHORITY), k(program_key=SYSTEM), k(program_key=STRAY, lp=1001),
              k(program_key=STRAY, length=907), k(program_key=STRAY, recipients=list(reversed(SORTED))),
              k(event_key=STRAY, lp=1001), k(event_key=STRAY, readonly=True), k(event_key=STRAY, signer=OTHER),
              k(event_key=STRAY, length=907), k(count=3, signer=OTHER), k(count=3, readonly=True),
              k(count=3, length=100), k(count=2, owner=SYSTEM), k(count=2, length=100), k(count=1, unsigned=True),
              k(count=0, lp=1001)]
    cases += [k(unsigned=True, owner=SYSTEM), k(owner=SYSTEM, readonly=True), k(readonly=True, signer=OTHER),
              k(readonly=True, length=100), k(readonly=True, lp=1001), k(signer=OTHER, lp=1001),
              k(signer=OTHER, recipients=list(reversed(SORTED))), k(readonly=True, recipients=[SYSTEM] * 8),
              k(signer=OTHER, length=907), k(length=907, lp=1001), k(length=906, lp=1001),
              k(length=940, program_key=STRAY), k(length=948, creator=1001)]
    # Existing fee fields are overwritten; the surrounding pattern is kept.
    cases += [k(lp=lp, proto=proto, creator=creator,
                patches=[(LP, struct.pack('<Q', 7)), (PROTOCOL, struct.pack('<Q', 8)),
                         (CREATOR, struct.pack('<Q', 9)), (RECIPIENTS, b'\x5a' * 256),
                         (FEE_AUTHORITY, b'\x3c' * 32)])
              for lp, proto, creator in ((0, 0, 0), (1000, 1000, 1000), (20, 5, 5))]
    return cases


def random_cases():
    rng = random.Random(20261030)
    cases = []
    for _ in range(200):
        c = {'mayhem': rng.randint(0, 1), 'cashback': rng.randint(0, 1), 'boost': rng.randint(0, 1),
             'cfc': rng.randint(0, 1)}
        roll = rng.random()
        if roll < 0.55:
            c['lp'] = rng.choice([0, 1, 20, 999, 1000, rng.randint(0, 1000)])
            c['proto'] = rng.choice([0, 5, 1000, rng.randint(0, 1000)])
            c['creator'] = rng.choice([0, 5, 1000, rng.randint(0, 1000)])
        elif roll < 0.8:
            field = rng.choice(['lp', 'proto', 'creator'])
            c[field] = rng.choice([1001, 1002, rng.randint(1001, 2**64 - 1)])
        else:
            c['args'] = rng.choice(['', '00' * 311, 'ff' * 7, args_bytes({}).hex()[:20]])
        roll = rng.random()
        if roll < 0.45:
            c['recipients'] = list(SORTED) if rng.random() < 0.5 else list(PREFIXED)
        elif roll < 0.7:
            keys = list(SORTED)
            keys[rng.randrange(8)] = rng.choice([SYSTEM, keys[rng.randrange(8)], STRAY])
            if rng.random() < 0.5:
                rng.shuffle(keys)
            c['recipients'] = keys
        elif roll < 0.85:
            c['recipients'] = list(reversed(SORTED))
        if rng.random() < 0.2:
            c['authority'] = rng.choice([SYSTEM, ADMIN.pubkey(), STRAY, AUTHORITY])
        if rng.random() < 0.25:
            c['length'] = rng.choice([906, 907, 920, 939, 940, 948, 949, 950, 960])
        if rng.random() < 0.08:
            c['patches'] = [(rng.choice([MAYHEM, CASHBACK, BOOST_ON, CFC]), bytes([rng.choice([2, 255])]))]
        for flag, prob in (('unsigned', 0.05), ('readonly', 0.05)):
            if rng.random() < prob:
                c[flag] = True
        if rng.random() < 0.05:
            c['signer'] = OTHER
        if rng.random() < 0.05:
            c['owner'] = rng.choice([SYSTEM, PUMP])
        if rng.random() < 0.06:
            c[rng.choice(['config_key', 'event_key', 'program_key'])] = STRAY
        if rng.random() < 0.04:
            c['count'] = rng.randint(0, 5)
        cases.append(c)
    return cases


class PumpAmmUpdateFeeConfigCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured_image()
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'update-fee-config-host'
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
            if rest[:4] == '6000':
                code, field = rest.split(',')
                self.assertEqual(captured['error'], int(code))
                self.assertIn(FEE_SITE[field], captured['logs'])
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
            self.assertTrue(event.startswith(EVENT_DISC.hex()))
            return
        self.assertTrue(answer.startswith('ok,'), 'unknown model outcome')
        _, config, event = answer.split(',')
        self.assertIsNone(captured['error'])
        self.assertEqual(captured['config'], bytes.fromhex(config))
        self.assertEqual(captured['events'], [bytes.fromhex(event)])
        self.assertEqual(captured['cpi'], [EVENT_CPI_TAG + bytes.fromhex(event)])
        self.assertTrue(bytes.fromhex(event).startswith(EVENT_DISC))

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
        case = {'lp': 20, 'proto': 5, 'creator': 5}
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
        case = {'count': 6, 'lp': 4, 'proto': 5, 'creator': 6}
        self.assertEqual(len(setup(case)[2]), 6)
        self.assert_matches(self.host_answers([case])[0], run_captured(case))

    def test_checker_rejects_tampered_outcomes(self):
        samples = ({'lp': 20, 'proto': 5, 'creator': 5}, {'lp': 1001}, {'proto': 1001}, {'creator': 1001},
                   {'recipients': list(reversed(SORTED))}, {'recipients': with_at(SORTED, 0, SYSTEM)},
                   {'program_key': STRAY}, {'length': 940}, {'length': 100}, {'args': ''})
        flip = lambda h, i: h[:2 * i] + format(int(h[2 * i:2 * i + 2], 16) ^ 1, '02x') + h[2 * i + 2:]
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured)
            with self.assertRaises(AssertionError):
                self.assert_matches(answer, dict(captured, unchanged=False))
            if answer.startswith('ok,'):
                _, config, event = answer.split(',')
                tampered = ['ok,' + flip(config, at) + ',' + event for at in (LP, PROTOCOL, RECIPIENTS, CREATOR, FEE_AUTHORITY, 948)]
                tampered += ['ok,' + config + ',' + flip(event, 8), 'ok,' + config + ',' + flip(event, 40),
                             'error:6000,lp', 'ok,' + config + ',']
            elif answer.startswith('event-then:'):
                name, event = answer[11:].split(',')
                tampered = ['event-then:' + name + ',' + flip(event, 16), 'error:' + name,
                            'event-then:' + ('BorshIoError' if name == 'MissingAccount' else 'MissingAccount') + ',' + event]
            elif answer.startswith('error:6000,'):
                field = answer.split(',')[1]
                other = next(name for name in FEE_SITE if name != field)
                tampered = ['error:6000,' + other, 'error:6011', 'error:6012']
            else:
                tampered = [text for text in ('error:6005', 'error:6011', 'error:6012', 'error:BorshIoError',
                                              'error:102') if text != answer]
            for text in tampered:
                with self.subTest(case=repr(c), tampered=text[:60]), self.assertRaises(AssertionError):
                    self.assert_matches(text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        cases = fixed_cases()
        answers = self.host_answers(cases)
        self.assertEqual({a for a in answers if a.startswith('error:')}, {
            'error:102', 'error:2000', 'error:2006', 'error:3005', 'error:3007', 'error:3010',
            'error:6000,lp', 'error:6000,protocol', 'error:6000,creator', 'error:6005', 'error:6011',
            'error:6012', 'error:InvalidAccountData', 'error:BorshIoError'})
        self.assertEqual({a.split(',')[0] for a in answers if a.startswith('event-then:')},
                         {'event-then:MissingAccount', 'event-then:BorshIoError'})
        self.assertGreater(sum(a.startswith('ok,') for a in answers), 20)


if __name__ == '__main__':
    unittest.main()
