"""Captured-program checks for UserVolumeAccumulator init/close and extend_account.

Every case runs Pump `init_user_volume_accumulator`,
`close_user_volume_accumulator`, or `extend_account` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, against synthetic accounts.
The same inputs go to `programs/pump/recovered/account_lifecycle_host.rs`.
The error, the signed lamport movements, the resulting account (size, owner,
lamports, data), and the emitted event must agree. This shows matching
behaviour on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
import re
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/account_lifecycle_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
FOREIGN = Pubkey.from_bytes(bytes([9]) * 32)
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}
IX = {i['name']: i for i in IDL['instructions']}
KIND_DISC = {'bc': ACCOUNT_DISC['BondingCurve'], 'uva': ACCOUNT_DISC['UserVolumeAccumulator'],
             'gva': ACCOUNT_DISC['GlobalVolumeAccumulator'], 'global': ACCOUNT_DISC['Global'],
             'fee_config': ACCOUNT_DISC['FeeConfig'], 'sharing': ACCOUNT_DISC['SharingConfig'],
             'quote_control': ACCOUNT_DISC['QuoteControl'], 'junk': bytes(range(1, 9))}

PAYER = Keypair.from_seed(bytes([211]) * 32)
USER = Keypair.from_seed(bytes([212]) * 32)
TARGET = Pubkey.from_bytes(bytes([77]) * 32)
UVA = Pubkey.find_program_address([b'user_volume_accumulator', bytes(USER.pubkey())], PUMP)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
NOW = 1_700_000_000
FEE = 5_000
UVA_RENT = (128 + 137) * 6_960


def uva_body(item):
    """A UVA image: discriminator (or another), stored user, then the fields."""
    data = bytearray(max(item['len'], 0))
    head = ACCOUNT_DISC['UserVolumeAccumulator'] if item['disc_ok'] else ACCOUNT_DISC['BondingCurve']
    body = head + bytes(item['stored_user']) + struct.pack('<?QQQq?QQQQ', *item['fields'])
    data[:] = (body + bytes(len(data)))[:len(data)]
    return bytes(data)


def case(op, **changes):
    item = dict(op=op, holder='pump', len=137, disc_ok=True, lamports=UVA_RENT, payer=10**12, user=10**9,
                signed=True, stored_user=USER.pubkey(), fields=(1, 5, 6, 7, 8, 1, 9, 10, 11, 12),
                owner='pump', kind='bc', fill=0)
    item.update(changes)
    return item


def holder_spec(item):
    return f"pump:{item['len']}:{int(item['disc_ok'])}" if item['holder'] == 'pump' else item['holder']


def host_line(item):
    signers = 2 if item['op'] != 'init' and item['signed'] else 1
    if item['op'] == 'init':
        return f"init,{holder_spec(item)},{item['lamports']},{item['payer'] - FEE}"
    if item['op'] == 'close':
        return f"close,{holder_spec(item)},{item['lamports']},{int(item['signed'])}"
    known = item['kind'] if item['kind'] in ('bc', 'uva', 'gva', 'global') else 'other'
    assert signers
    return (f"extend,{int(item['signed'])},{int(item['owner'] == 'pump')},{known},{item['len']},"
            f"{item['lamports']},{item['user']}")


def subject(item):
    return TARGET if item['op'] == 'extend' else UVA


def subject_account(item):
    if item['op'] == 'extend':
        if item['owner'] == 'missing':
            return None
        data = (KIND_DISC[item['kind']] + bytes([item['fill']]) * item['len'])[:item['len']]
        owner = {'pump': PUMP, 'system': SYSTEM, 'other': FOREIGN}[item['owner']]
        return Account(item['lamports'], data, owner)
    holder = item['holder']
    if holder == 'missing':
        return None
    if holder == 'system':
        return Account(item['lamports'], b'', SYSTEM)
    if holder == 'system_data':
        return Account(item['lamports'], bytes(137), SYSTEM)
    if holder == 'other':
        return Account(item['lamports'], b'', FOREIGN)
    return Account(item['lamports'], uva_body(item), PUMP)


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.set_clock(Clock(100, NOW, 0, 0, NOW))
    vm.set_account(PAYER.pubkey(), Account(item['payer'], b'', SYSTEM))
    if item['user']:
        vm.set_account(USER.pubkey(), Account(item['user'], b'', SYSTEM))
    account = subject_account(item)
    if account is not None:
        vm.set_account(subject(item), account)
    names = {'payer': PAYER.pubkey(), 'user': USER.pubkey(), 'user_volume_accumulator': UVA, 'account': TARGET,
             'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    ix = IX[item['op'] + ('_user_volume_accumulator' if item['op'] != 'extend' else '_account')]
    metas = [AccountMeta(names[a['name']], a.get('signer', False) and item['signed'], a.get('writable', False))
             for a in ix['accounts']]
    signers = [PAYER] + ([USER] if any(m.is_signer and m.pubkey == USER.pubkey() for m in metas) else [])
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(ix['discriminator']), metas)], PAYER.pubkey(),
                                           signers, vm.latest_blockhash())
    watched = (PAYER.pubkey(), USER.pubkey(), subject(item))
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [lamports(key) for key in watched]
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    after = vm.get_account(subject(item))
    return {'error': None, 'fee': FEE * len(signers),
            'delta': dict(zip(('payer', 'user', 'subject'), (lamports(k) - b for k, b in zip(watched, before)))),
            'account': None if after is None or after.lamports == 0 else
            (after.lamports, str(after.owner), bytes(after.data)),
            'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]}


def fixed_cases():
    cases = []
    add = lambda op, **k: cases.append(case(op, **k))
    # init: create from nothing or a pre-funded system account (shortfall only).
    for lamports in (0, 1, 890_880, UVA_RENT - 1, UVA_RENT, 10**9):
        add('init', holder='system' if lamports else 'missing', lamports=lamports)
    add('init', holder='missing', lamports=0, payer=UVA_RENT + FEE)
    add('init', holder='missing', lamports=0, payer=UVA_RENT + FEE - 1)
    add('init', holder='system', lamports=1, payer=UVA_RENT + FEE - 2)
    # init on an existing accumulator: only `user` is rewritten.
    add('init')
    add('init', stored_user=TARGET, lamports=10**9)
    add('init', fields=(0,) * 10)
    for length in (0, 7, 8, 105, 106, 136, 138, 200):
        add('init', len=length)
    # An existing accumulator must already be rent-exempt.
    for lamports in (1, UVA_RENT - 1):
        add('init', lamports=lamports)
    add('init', disc_ok=False)
    add('init', holder='system_data', lamports=10**9)
    add('init', holder='other', lamports=10**9)
    # close: every lamport to the user, whatever is still owed.
    for lamports in (1, UVA_RENT, UVA_RENT + 77, 10**12):
        add('close', lamports=lamports)
    add('close', fields=(0,) * 10)
    add('close', fields=(1, 2**64 - 1, 2**64 - 1, 2**64 - 1, -1, 1, 2**64 - 1, 0, 2**64 - 1, 0))
    add('close', stored_user=TARGET)
    add('close', len=200)
    for length in (0, 7, 8, 105, 106, 136):
        add('close', len=length)
    add('close', disc_ok=False)
    add('close', holder='missing', lamports=0)
    add('close', holder='system', lamports=10**9)
    add('close', holder='other', lamports=10**9)
    add('close', signed=False)
    add('close', signed=False, holder='missing', lamports=0)
    # extend: the size difference at 6,960 per byte, whatever the balance.
    for kind, target in (('bc', 166), ('uva', 137), ('gva', 600), ('global', 1088)):
        for length in (8, 81, target - 1, target, target + 1):
            add('extend', kind=kind, len=length, lamports=10**9, fill=0xAB)
        add('extend', kind=kind, len=target - 16, lamports=(128 + target - 16) * 6_960)
    add('extend', kind='bc', len=81, lamports=1)
    add('extend', kind='bc', len=158, lamports=1)
    add('extend', kind='bc', len=166, lamports=1)  # already full size: no-op, even underfunded
    add('extend', kind='bc', len=81, lamports=1_454_640)
    add('extend', kind='bc', len=81, lamports=1_454_639)
    add('extend', kind='bc', len=81, lamports=10**9, user=591_600)
    add('extend', kind='bc', len=81, lamports=10**9, user=591_599)
    add('extend', kind='bc', len=81, lamports=10**9, user=0)
    for kind in ('fee_config', 'sharing', 'quote_control', 'junk'):
        add('extend', kind=kind, len=40, lamports=10**9)
    for length in (0, 7):
        add('extend', kind='bc', len=length, lamports=10**9)
    for owner in ('system', 'other', 'missing'):
        add('extend', kind='bc', len=81, lamports=10**9, owner=owner)
    add('extend', kind='bc', len=81, lamports=10**9, signed=False)
    add('extend', kind='junk', len=3, lamports=10**9, signed=False, owner='system')
    add('extend', kind='junk', len=3, lamports=10**9, owner='system')
    add('extend', kind='bc', len=0, lamports=0, owner='missing')
    return cases


def random_cases(count=90, seed=1891):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        op = rng.choice(('init', 'close', 'extend'))
        if op == 'extend':
            kind = rng.choice(('bc', 'uva', 'gva', 'global', 'junk'))
            length = rng.choice((rng.randrange(0, 1200), rng.randrange(8, 200)))
            cases.append(case('extend', kind=kind, len=length, fill=rng.randrange(256),
                              lamports=rng.choice((10**9, (128 + length) * 6_960, rng.randrange(1, 10**7))),
                              user=rng.choice((10**10, 0, rng.randrange(0, 2 * 10**6))),
                              owner=rng.choice(('pump',) * 6 + ('system', 'other')), signed=rng.random() > 0.1))
            # Avoid leaving the user between 0 and the zero-byte minimum: that
            # is a runtime rule on the user account the model does not cover.
            item = cases[-1]
            if 0 < item['user'] < 10**10:
                item['user'] = rng.choice((0, 10**10))
        else:
            holder = rng.choice(('pump',) * 6 + ('missing', 'system', 'other'))
            fields = (rng.randrange(2), rng.randrange(2**64), rng.randrange(2**64), rng.randrange(2**64),
                      rng.randrange(-2**63, 2**63), rng.randrange(2), rng.randrange(2**64), rng.randrange(2**64),
                      rng.randrange(2**64), rng.randrange(2**64))
            lamports = 0 if holder == 'missing' else rng.choice((1, UVA_RENT, rng.randrange(1, 10**10)))
            cases.append(case(op, holder=holder, lamports=lamports, fields=fields,
                              len=rng.choice((137,) * 5 + (rng.randrange(0, 300),)), disc_ok=rng.random() > 0.15,
                              stored_user=rng.choice((USER.pubkey(), TARGET)), signed=rng.random() > 0.1,
                              payer=rng.choice((10**12, UVA_RENT + FEE, rng.randrange(FEE, 3 * 10**6)))))
    return cases


class AccountLifecycleCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'account-lifecycle-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        return subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()

    def check(self, item, answer):
        self.assert_matches(item, answer, run_captured(item))

    def assert_matches(self, item, answer, captured):
        if answer == 'rent':
            self.assertIn('InsufficientFundsForRent', str(captured['error']))
            return
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        values = list(map(int, answer.split(',')[1:]))
        fee, delta = captured['fee'], captured['delta']
        before = subject_account(item)
        if item['op'] == 'init':
            paid, created = values
            self.assertEqual(delta, {'payer': -(paid + fee), 'user': 0, 'subject': paid})
            old = bytes(137) if created else before.data
            data = ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(USER.pubkey()) + old[40:]
            start = 0 if before is None else before.lamports
            self.assertEqual(captured['account'], (start + paid, str(PUMP), data))
            expected = [EVENT_DISC['InitUserVolumeAccumulatorEvent'] + bytes(PAYER.pubkey())
                        + bytes(USER.pubkey()) + struct.pack('<q', NOW)]
        elif item['op'] == 'close':
            (refund,) = values
            self.assertEqual(delta, {'payer': -fee, 'user': refund, 'subject': -refund})
            self.assertIsNone(captured['account'])
            unclaimed, claimed, volume, last = struct.unpack_from('<QQQq', before.data, 41)
            expected = [EVENT_DISC['CloseUserVolumeAccumulatorEvent'] + bytes(USER.pubkey())
                        + struct.pack('<qQQQq', NOW, unclaimed, claimed, volume, last)]
        else:
            new_len, paid = values
            self.assertEqual(delta, {'payer': -fee, 'user': -paid, 'subject': paid})
            self.assertEqual(captured['account'], (before.lamports + paid, str(PUMP),
                                                   before.data + bytes(new_len - len(before.data))))
            expected = [EVENT_DISC['ExtendAccountEvent'] + bytes(TARGET) + bytes(USER.pubkey())
                        + struct.pack('<QQq', item['len'], new_len, NOW)] if paid else []
        self.assertEqual(captured['events'], expected)

    def run_cases(self, cases):
        for item, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=host_line(item), host=answer):
                self.check(item, answer)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_reversed_lamport_movements(self):
        # Negative control: passing captured runs must fail once a lamport
        # movement is reversed (credit <-> debit of the same size).
        for item, keys in ((case('init', holder='missing', lamports=0), ('payer', 'subject')),
                           (case('close'), ('user', 'subject')),
                           (case('extend', kind='bc', len=81, lamports=10**9), ('user', 'subject'))):
            answer = self.host_answers([item])[0]
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            for key in keys:
                with self.subTest(op=item['op'], reversed=key):
                    self.assertNotEqual(captured['delta'][key], 0)
                    flipped = dict(captured, delta=dict(captured['delta'], **{key: -captured['delta'][key]}))
                    with self.assertRaises(AssertionError):
                        self.assert_matches(item, answer, flipped)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers} - {'ok'}, {
            'rent', 'error:0', 'error:1', 'error:2004', 'error:2005', 'error:2019', 'error:3001', 'error:3002', 'error:3003',
            'error:3007', 'error:3010', 'error:3012', 'error:6010',
        })
        self.assertTrue(any(a.startswith('ok') and a.endswith(',0') for a in answers if a.count(',') == 2))


if __name__ == '__main__':
    unittest.main()
