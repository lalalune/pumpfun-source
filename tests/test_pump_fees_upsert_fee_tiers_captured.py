"""Captured-program checks for Pump Fees `upsert_fee_tiers`.

Each case builds a synthetic `FeeConfig` (legacy 2512-byte layout, stable
4073..4096, full 4097+, or something broken), a `Vec<FeeTier>` plus `u8`
offset, and the five fixed metas (`fee_config`, `admin`, `config_program_id`,
`event_authority`, `program`). It runs the instruction on
`evidence/original/pump_fees/deployed.so` in LiteSVM and feeds the same bytes
to `programs/pump-fees/recovered/upsert_fee_tiers_host.rs`. Owners, the signer
and writable flags, and the PDA matches are worked out here from the metas
actually passed. The error, the committed config bytes, the logged
`UpsertFeeTiersEvent` and the same bytes in the `emit_cpi!` self-call must
agree. Failed transactions roll the config back. This is matching behaviour
on these inputs, not a byte-identity claim.
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
FEES_ELF = ROOT / 'evidence/original/pump_fees/deployed.so'
FEES_SHA256 = '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e'
HOST_SOURCE = ROOT / 'programs/pump-fees/recovered/upsert_fee_tiers_host.rs'
MODEL_SOURCE = ROOT / 'programs/pump-fees/recovered/upsert_fee_tiers.rs'

PROGRAM = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.default()
CONFIG, BUMP = Pubkey.find_program_address([b'fee_config', bytes(PUMP)], PROGRAM)
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
CONFIG_DISC = hashlib.sha256(b'account:FeeConfig').digest()[:8]
IX = hashlib.sha256(b'global:upsert_fee_tiers').digest()[:8]
EVENT_DISC = hashlib.sha256(b'event:UpsertFeeTiersEvent').digest()[:8]
# Anchor's EVENT_IX_TAG, the u64 0x1d9acb512ea545e4 in little-endian order.
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
PAYER = Keypair.from_seed(bytes([215]) * 32)
ADMIN = Keypair.from_seed(bytes([213]) * 32)
OTHER = Keypair.from_seed(bytes([214]) * 32)
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
NOW = 1_700_000_000
VALID = (1, 2, 3)


def fees(parts):
    return struct.pack('<QQQ', *parts)


def tier_list(items):
    body = b''.join(int(cap).to_bytes(16, 'little') + fees(parts) for cap, parts in items)
    return struct.pack('<I', len(items)) + body


def config_bytes(c):
    """A config whose tail is 0xAB, so a wiped tail or a stale tier shows."""
    normal = c.get('normal', [(0, VALID), (100, (4, 5, 6))])
    stable = c.get('stable', [(10, (7, 8, 9))])
    body = bytearray(CONFIG_DISC)
    body.append(c.get('bump', BUMP))
    body += bytes(c.get('admin_key', ADMIN.pubkey()))
    body += fees(c.get('flat', (11, 22, 33)))
    body += tier_list(normal)
    body += tier_list(stable)
    body += fees(c.get('exotic', (44, 55, 66)))
    length = c.get('length', 4097)
    if len(body) >= length:
        data = bytearray(body[:length])
    else:
        data = bytearray(body)
        data.extend(bytes([0xAB]) * (length - len(body)))
    if 'disc' in c:
        data[:8] = c['disc']
    for at, value in c.get('patches', ()):
        data[at:at + len(value)] = value
    return bytes(data)


def args_bytes(c):
    if 'args' in c:
        return bytes.fromhex(c['args'])
    incoming = c.get('incoming', [(0, VALID), (200, (4, 5, 6))])
    return tier_list(incoming) + bytes([c.get('offset', 0)]) + bytes.fromhex(c.get('trailing', ''))


def fee_seeds_ok(data, key, config_program):
    if len(data) < 9:
        return False
    pda, bump = Pubkey.find_program_address([b'fee_config', bytes(config_program)], PROGRAM)
    return key == pda and data[8] == bump


def setup(c):
    key = c.get('key', CONFIG)
    signer = c.get('signer', ADMIN)
    data = config_bytes(c)
    metas = [
        AccountMeta(key, False, not c.get('readonly')),
        AccountMeta(signer.pubkey(), not c.get('unsigned'), c.get('admin_writable', False)),
        AccountMeta(c.get('config_program', PUMP), False, False),
        AccountMeta(c.get('event_key', EVENT), False, c.get('event_writable', False)),
        AccountMeta(c.get('program_key', PROGRAM), False, False),
    ]
    metas = metas[:c.get('count', len(metas))]
    metas += [AccountMeta(extra, False, False) for extra in c.get('extra', ())]
    ix_data = IX + args_bytes(c)
    accounts = {key: Account(c.get('lamports', 10**9), data, c.get('owner', PROGRAM))}
    signers = [PAYER]
    if any(meta.is_signer and meta.pubkey == signer.pubkey() for meta in metas):
        signers.append(signer)
    return key, accounts, metas, ix_data, signers


def host_line(c):
    key, accounts, metas, ix_data, _ = setup(c)
    raw = bytes(accounts[key].data)
    config_program = metas[2].pubkey if len(metas) > 2 else PUMP
    flags = [
        len(metas) > 1 and metas[1].is_signer,
        accounts[key].owner == PROGRAM,
        len(metas) > 0 and metas[0].is_writable,
        len(metas) > 2 and fee_seeds_ok(raw, key, config_program),
        len(metas) > 3 and metas[3].pubkey == EVENT,
        len(metas) > 4 and metas[4].pubkey == PROGRAM,
    ]
    admin = metas[1].pubkey if len(metas) > 1 else ADMIN.pubkey()
    return ','.join([
        str(len(metas)),
        ''.join('1' if flag else '0' for flag in flags),
        ix_data[8:].hex(),
        raw.hex(),
        bytes(admin).hex(),
        bytes(key).hex(),
        str(c.get('timestamp', NOW)),
    ])


def read_captured_image(path):
    image = path.read_bytes()
    if hashlib.sha256(image).hexdigest() != FEES_SHA256:
        raise ValueError('captured pump_fees hash mismatch')
    return image


@cache
def captured_image():
    return read_captured_image(FEES_ELF)


def run_captured(c):
    key, accounts, metas, ix_data, signers = setup(c)
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program(PROGRAM, captured_image())
    vm.set_clock(Clock(0, 0, 0, 0, c.get('timestamp', NOW)))
    vm.airdrop(PAYER.pubkey(), 10**12)
    for signer in (ADMIN, OTHER):
        vm.airdrop(signer.pubkey(), 10**12)
    for account_key, account in accounts.items():
        vm.set_account(account_key, account)
    before = {k: vm.get_account(k) for k in accounts}
    tx = Transaction.new_signed_with_payer(
        [Instruction(PROGRAM, ix_data, metas)], PAYER.pubkey(), signers, vm.latest_blockhash())
    # An unsigned transaction yields no results and `not all([])` is false, so
    # this check passed for a fixture the VM had no signature to accept.
    if not (tx.signatures and all(tx.verify_with_results())):
        raise ValueError('fixture transaction signature verification failed')
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = [base64.b64decode(line[len('Program data: '):])
              for line in meta.logs() if line.startswith('Program data: ')]
    after = {k: vm.get_account(k) for k in accounts}
    unchanged = all(
        (after[k].lamports, after[k].owner, after[k].executable, after[k].rent_epoch)
        == (before[k].lamports, before[k].owner, before[k].executable, before[k].rent_epoch)
        and len(after[k].data) == len(before[k].data)
        and (not failed or bytes(after[k].data) == bytes(before[k].data))
        for k in accounts)
    out = {'events': events, 'unchanged': unchanged}
    if failed:
        text = str(result.err())
        custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
        out['error'] = int(custom.group(1)) if custom else re.search(r'Fieldless\((\w+)\)', text).group(1)
        out['cpi'] = [bytes(ix.instruction().data) for group in meta.inner_instructions() for ix in group]
        return out
    out.update(error=None, config=bytes(after[key].data),
               cpi=[bytes(ix.instruction().data) for group in meta.inner_instructions() for ix in group])
    return out


def case(**kwargs):
    return dict(kwargs)


def fixed_cases():
    cases = []
    # Splices that commit, across the three layouts, with the tail left in place.
    for length in (2512, 4072, 4073, 4096, 4097, 5000):
        cases.append(case(length=length))
        cases.append(case(length=length, incoming=[(300, VALID)], offset=2))
        cases.append(case(length=length, incoming=[(50, (9, 9, 9))], offset=1))
        cases.append(case(length=length, flat=(2**64 - 1, 0, 0), exotic=(9, 8, 7),
                           stable=[(4, (10001, 0, 0)), (3, (1, 1, 1))]))
    # The 50-tier cap is inclusive, and a full account can hold 50 + 50.
    fifty = [(i, VALID) for i in range(50)]
    cases += [
        case(length=8192, normal=[(0, VALID)], stable=[], incoming=fifty, offset=0),
        case(length=2512, normal=[(0, VALID)], stable=[], incoming=fifty, offset=0),
        case(length=8192, normal=[(i, VALID) for i in range(49)], stable=[], incoming=[(1000, VALID)], offset=49),
        case(length=4097, normal=[(0, VALID)], stable=[(10_000 + i, VALID) for i in range(50)], incoming=fifty, offset=0),
        case(length=4073, normal=[(0, VALID)], stable=[(10_000 + i, VALID) for i in range(50)],
             incoming=[(i, VALID) for i in range(49)], offset=0),
        case(normal=[], stable=[(5, VALID)], incoming=[(2**128 - 1, VALID)], offset=0),
        case(incoming=[(0, (4000, 3000, 3000))], offset=0),
        case(incoming=[(0, (10_000, 0, 0))], offset=0),
        case(incoming=[(99, VALID)], offset=0),
        case(timestamp=0),
        case(timestamp=-5),
        case(trailing='ffee'),
        case(extra=(STRAY,)),
        case(admin_writable=True, event_writable=True),
        case(lamports=1),
        # Overwriting a bad kept tier removes it; the result is what is checked.
        case(normal=[(0, (2**64 - 1, 1, 0)), (10, VALID)], stable=[],
             incoming=[(0, VALID), (10, VALID)], offset=0, length=4097),
    ]
    # Argument decoding wins over every account failure.
    cases += [
        case(args=''),
        case(args='00'),
        case(args='01000000' + '00' * 39),
        case(args='ffffffff'),
        case(args='', count=0),
        case(args='', owner=SYSTEM),
        case(args='', unsigned=True),
        case(args='', bump=BUMP ^ 1),
        case(args='', disc=b'\x00' * 8),
    ]
    # Account load order: owner, layout, signer, then the remaining metas.
    cases += [case(count=n) for n in range(5)]
    cases += [
        case(owner=SYSTEM),
        case(owner=SYSTEM, unsigned=True),
        case(owner=SYSTEM, readonly=True),
        case(owner=SYSTEM, disc=b'\x00' * 8),
        case(owner=SYSTEM, length=2511),
        case(owner=PUMP),
        case(disc=b'\x00' + CONFIG_DISC[1:]),
        case(length=0),
        case(length=7),
        case(length=8),
        case(length=2511),
        case(length=2511, unsigned=True),
        case(disc=b'\x00' * 8, patches=[(65, b'\xff\xff\xff\xff')]),
        case(patches=[(65, b'\xff\xff\xff\xff')]),
        case(patches=[(65, (62).to_bytes(4, 'little'))], length=2512, normal=[(0, VALID)], stable=[]),
        case(patches=[(65, (61).to_bytes(4, 'little'))], length=2512, normal=[(0, VALID)], stable=[],
             incoming=[(0, VALID)], offset=0),
        case(unsigned=True),
        case(unsigned=True, readonly=True),
        case(unsigned=True, bump=BUMP ^ 1),
        case(count=3, unsigned=True),
        case(count=3, bump=BUMP ^ 1),
        case(count=2, owner=SYSTEM),
        case(count=1, disc=b'\x00' * 8),
    ]
    # Constraints: seeds, then mut, then has_one, then the event-authority seeds.
    cases += [
        case(bump=BUMP ^ 1),
        case(key=STRAY),
        case(config_program=STRAY),
        case(bump=BUMP ^ 1, event_key=STRAY),
        case(bump=BUMP ^ 1, signer=OTHER),
        case(readonly=True),
        case(readonly=True, bump=BUMP ^ 1),
        case(readonly=True, event_key=STRAY),
        case(readonly=True, signer=OTHER),
        case(signer=OTHER),
        case(admin_key=OTHER.pubkey()),
        case(admin_key=SYSTEM),
        case(event_key=STRAY),
        case(event_key=STRAY, signer=OTHER),
        case(event_key=PROGRAM),
    ]
    # Handler order, then the event / CPI / write-back split.
    overflow = (2**64 - 1, 1, 0)
    cases += [
        case(incoming=[], offset=0),
        case(incoming=[], offset=255),
        case(incoming=[(1, VALID)], offset=3),
        case(incoming=[(i, VALID) for i in range(51)], offset=3),
        case(incoming=[(i, (10001, 0, 0)) for i in range(51)], offset=0, length=8192),
        case(length=8192, normal=[(i, VALID) for i in range(50)], stable=[], incoming=[(1000, VALID)], offset=50),
        case(length=8192, normal=[(i, VALID) for i in range(60)], stable=[], incoming=[(0, VALID)], offset=0),
        case(incoming=[(0, (10001, 0, 0))], offset=0),
        case(incoming=[(0, (4000, 3000, 3001))], offset=0),
        case(incoming=[(0, (2**64 - 1, 0, 0))], offset=0),
        case(incoming=[(5, (10001, 0, 0)), (1, VALID)], offset=0),
        case(incoming=[(5, VALID), (1, (10001, 0, 0))], offset=0),
        case(incoming=[(0, overflow)], offset=0),
        case(incoming=[(0, (1, 2**64 - 1, 0))], offset=0),
        case(incoming=[(0, (0, 1, 2**64 - 1))], offset=0),
        case(incoming=[(0, overflow), (1, (10001, 0, 0))], offset=0),
        case(incoming=[(0, (10001, 0, 0)), (1, overflow)], offset=0),
        case(normal=[(0, (10001, 0, 0)), (100, VALID)], stable=[], incoming=[(200, VALID)], offset=1),
        case(normal=[(0, overflow), (100, VALID)], stable=[], incoming=[(200, VALID)], offset=1),
        case(incoming=[(100, VALID), (100, (4, 5, 6))], offset=0),
        case(incoming=[(100, VALID)], offset=0),
        case(incoming=[(20, VALID)], offset=0),
        case(incoming=[(5, VALID), (4, VALID)], offset=0),
        case(normal=[(5, VALID)], stable=[], incoming=[(0, VALID)], offset=1, length=4097),
        case(program_key=STRAY),
        case(program_key=SYSTEM),
        case(program_key=STRAY, incoming=[(0, (10001, 0, 0))], offset=0),
        case(length=4096, normal=[(0, VALID)], stable=[(10_000 + i, VALID) for i in range(50)],
             incoming=fifty, offset=0),
        case(length=4073, normal=[(0, VALID)], stable=[(10_000 + i, VALID) for i in range(50)],
             incoming=fifty, offset=0),
        case(length=4096, normal=[(0, VALID)], stable=[(10_000 + i, VALID) for i in range(50)],
             incoming=fifty, offset=0, program_key=STRAY),
    ]
    return cases


def random_cases():
    rng = random.Random(20261030)
    lengths = [2511, 2512, 3000, 4072, 4073, 4096, 4097, 4200, 8192]
    cases = []
    for _ in range(200):
        c = {'timestamp': rng.choice([0, -1, NOW, 2**31 - 1])}
        old_n = rng.randrange(0, 12)
        new_n = rng.randrange(0, 12)
        if rng.random() < 0.08:
            old_n = rng.choice([49, 50, 60])
        if rng.random() < 0.08:
            new_n = rng.choice([0, 49, 50, 51])
        def fee_parts():
            roll = rng.random()
            if roll < 0.7:
                return tuple(rng.randrange(0, 4000) for _ in range(3))
            if roll < 0.85:
                return (10_000, 0, 0) if rng.random() < 0.5 else (10001, 0, 0)
            return rng.choice([(2**64 - 1, 0, 0), (2**64 - 1, 1, 0), (0, 1, 2**64 - 1)])
        c['normal'] = [(i * 10, fee_parts()) for i in range(old_n)]
        c['stable'] = [(rng.randrange(0, 1000), fee_parts()) for _ in range(rng.randrange(0, 4))]
        c['incoming'] = [(rng.randrange(0, 500), fee_parts()) for _ in range(new_n)]
        c['offset'] = rng.randrange(0, old_n + 3)
        c['length'] = rng.choice(lengths)
        c['flat'] = fee_parts()
        c['exotic'] = fee_parts()
        if rng.random() < 0.05:
            c['unsigned'] = True
        if rng.random() < 0.05:
            c['readonly'] = True
        if rng.random() < 0.04:
            c['owner'] = rng.choice([SYSTEM, PUMP])
        if rng.random() < 0.04:
            c['bump'] = BUMP ^ 1
        if rng.random() < 0.04:
            c[rng.choice(['key', 'event_key', 'program_key', 'config_program'])] = STRAY
        if rng.random() < 0.04:
            c['signer'] = OTHER
        if rng.random() < 0.03:
            c['count'] = rng.randrange(0, 5)
        if rng.random() < 0.03:
            c['args'] = rng.choice(['', '00', '01000000', 'ffffffff00'])
        if rng.random() < 0.04:
            c['patches'] = [(65, rng.choice([62, 2**32 - 1]).to_bytes(4, 'little'))]
        cases.append(c)
    return cases


class PumpFeesUpsertFeeTiersCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured_image()
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'upsert-fee-tiers-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases, host=None):
        text = ''.join(host_line(c) + '\n' for c in cases)
        answers = subprocess.run([str(host or self.host)], input=text, capture_output=True, text=True,
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
            name, event_hex = answer[len('event-then:'):].split(',', 1)
            event = bytes.fromhex(event_hex)
            self.assertEqual(captured['error'], name)
            self.assertEqual(captured['events'], [event])
            expected_cpi = [] if name == 'MissingAccount' else [EVENT_CPI_TAG + event]
            self.assertEqual(captured['cpi'], expected_cpi)
            return
        self.assertIsNone(captured['error'])
        self.assertTrue(answer.startswith('ok,'), 'unknown model outcome')
        _, config_hex, event_hex = answer.split(',', 2)
        event = bytes.fromhex(event_hex)
        self.assertEqual(captured['config'], bytes.fromhex(config_hex))
        self.assertEqual(captured['events'], [event])
        self.assertEqual(event[:8], EVENT_DISC)
        self.assertEqual(captured['cpi'], [EVENT_CPI_TAG + event])

    def run_cases(self, cases):
        for c, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=repr(c)[:240], host=answer[:80]):
                self.assert_matches(answer, run_captured(c))

    def test_rejects_wrong_image_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'wrong.so'
            wrong.write_bytes(b'not the captured fees program')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                read_captured_image(wrong)

    def test_admitted_image_is_used_after_source_path_moves(self):
        sample = case()
        expected = run_captured(sample)
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'replacement.so'
            wrong.write_bytes(b'wrong ELF')
            with patch(__name__ + '.FEES_ELF', wrong):
                self.assertEqual(run_captured(sample), expected)

    def test_fixed_cases_match_captured_program(self):
        cases = fixed_cases()
        self.assertEqual(len(cases), 122)
        self.run_cases(cases)

    def test_seeded_random_cases_match_captured_program(self):
        cases = random_cases()
        self.assertEqual(len(cases), 200)
        self.run_cases(cases)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({answer.split(',')[0] for answer in answers}, {
            'error:102', 'error:2000', 'error:2006', 'error:3005', 'error:3007', 'error:3010',
            'error:6001', 'error:6002', 'error:6003', 'error:6004', 'error:6005', 'error:6006',
            'error:InvalidAccountData', 'error:BorshIoError', 'error:ProgramFailedToComplete',
            'event-then:MissingAccount', 'event-then:BorshIoError', 'ok'})
        self.assertGreater(sum(answer.startswith('ok,') for answer in answers), 20)

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: each captured run must fail once the error, a config
        # byte, or an event byte moves.
        samples = (
            case(),
            case(length=2512, flat=(7, 8, 9)),
            case(incoming=[], offset=0),
            case(incoming=[(0, (2**64 - 1, 1, 0))], offset=0),
            case(program_key=STRAY),
            case(length=4096, normal=[(0, VALID)], stable=[(10_000 + i, VALID) for i in range(50)],
                 incoming=[(i, VALID) for i in range(50)], offset=0),
            case(readonly=True),
        )
        flip = lambda blob, at: blob[:at] + bytes([blob[at] ^ 1]) + blob[at + 1:]
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured)
            with self.assertRaises(AssertionError):
                self.assert_matches(answer, dict(captured, unchanged=False))
            if answer.startswith('ok,'):
                _, config_hex, event_hex = answer.split(',', 2)
                config = bytes.fromhex(config_hex)
                event = bytes.fromhex(event_hex)
                tampered = [
                    'ok,' + flip(config, 8).hex() + ',' + event_hex,
                    'ok,' + flip(config, len(config) - 1).hex() + ',' + event_hex,
                    'ok,' + config_hex + ',' + flip(event, 0).hex(),
                    'ok,' + config_hex + ',' + flip(event, len(event) - 1).hex(),
                    'error:6005',
                    'event-then:BorshIoError,' + event_hex,
                ]
            elif answer.startswith('event-then:'):
                name, event_hex = answer[len('event-then:'):].split(',', 1)
                other = 'BorshIoError' if name == 'MissingAccount' else 'MissingAccount'
                tampered = [
                    f'event-then:{other},{event_hex}',
                    'event-then:' + name + ',' + flip(bytes.fromhex(event_hex), 8).hex(),
                    'error:' + name,
                    'ok,' + config_bytes(c).hex() + ',' + event_hex,
                ]
            else:
                tampered = [text for text in (
                    'error:6005', 'error:BorshIoError', 'error:ProgramFailedToComplete',
                    'ok,' + config_bytes(c).hex() + ',' + (EVENT_DISC + bytes(16)).hex(),
                ) if text != answer]
            for text in tampered:
                with self.subTest(case=repr(c)[:120], tampered=text[:48]):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(text, captured)

    def test_model_mutants_diverge_from_captured_program(self):
        # Each mutant compiles and disagrees with the captured program on a case
        # the real model matches. The replacement is a single check.
        mutants = (
            ('const MAX_FEE_TIERS: usize = 50;', 'const MAX_FEE_TIERS: usize = 49;',
             case(length=8192, normal=[(0, VALID)], stable=[], incoming=[(i, VALID) for i in range(50)], offset=0)),
            ('if pair[0].market_cap >= pair[1].market_cap {', 'if pair[0].market_cap > pair[1].market_cap {',
             case(incoming=[(100, VALID), (100, (4, 5, 6))], offset=0)),
            ('const MAX_FEE_BPS: u64 = 10_000;', 'const MAX_FEE_BPS: u64 = 9_999;',
             case(incoming=[(0, (10_000, 0, 0))], offset=0)),
            ('lp.checked_add(protocol).and_then(|sum| sum.checked_add(creator))',
             'lp.wrapping_add(protocol).wrapping_add(creator).checked_add(0)',
             case(incoming=[(0, (2**64 - 1, 1, 0))], offset=0)),
        )
        source = MODEL_SOURCE.read_text()
        for old, new, sample in mutants:
            self.assertEqual(source.count(old), 1, old)
            mutated = source.replace(old, new, 1)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                (path / 'upsert_fee_tiers.rs').write_text(mutated)
                host_src = HOST_SOURCE.read_text()
                (path / 'upsert_fee_tiers_host.rs').write_text(host_src)
                binary = path / 'mutant'
                subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings',
                                str(path / 'upsert_fee_tiers_host.rs'), '-o', str(binary)], check=True)
                real, mutant = self.host_answers([sample])[0], self.host_answers([sample], binary)[0]
            captured = run_captured(sample)
            self.assert_matches(real, captured)
            self.assertNotEqual(mutant, real)
            with self.assertRaises(AssertionError):
                self.assert_matches(mutant, captured)


if __name__ == '__main__':
    unittest.main()
