"""Captured-program checks for the QuoteControl mint registry.

Every case runs one of Pump `initialize_quote_control`,
`add_quote_control_mint`, `remove_quote_control_mint`,
`set_quote_control_mint_reserves`, `set_quote_control_admin` or
`set_quote_control_reserves_admin` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, against a synthetic Global
and QuoteControl account. The same inputs go to
`programs/pump/recovered/quote_control_host.rs`. The error, the signed
lamport deltas, the resulting account (size, lamports, every data byte) and
the emitted event must agree. This shows matching behaviour on these inputs
only; it is not a byte-identity claim.
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/quote_control_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
FOREIGN = Pubkey.from_bytes(bytes([9]) * 32)
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}
OPS = {'init': 'initialize_quote_control', 'add': 'add_quote_control_mint', 'remove': 'remove_quote_control_mint',
       'reserves': 'set_quote_control_mint_reserves', 'admin': 'set_quote_control_admin',
       'reserves_admin': 'set_quote_control_reserves_admin'}
IX = {op: next(i for i in IDL['instructions'] if i['name'] == name) for op, name in OPS.items()}

PAYER = Keypair.from_seed(bytes([231]) * 32)
GLOBAL_AUTHORITY, ADMIN, RESERVES_ADMIN, OUTSIDER = 10, 11, 12, 13
SIGNERS = {i: Keypair.from_seed(bytes([i + 222]) * 32) for i in (10, 11, 12, 13)}
NATIVE = Pubkey.from_string('So11111111111111111111111111111111111111112')
KEYS = {0: SYSTEM, 1: NATIVE, **{i: Pubkey.from_bytes(bytes([60 + i]) * 32) for i in range(2, 10)},
        **{i: kp.pubkey() for i, kp in SIGNERS.items()}}
GLOBAL = Pubkey.find_program_address([b'global'], PUMP)[0]
QUOTE_CONTROL = Pubkey.find_program_address([b'quote-control'], PUMP)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
NOW = 1_700_000_000
HEADER = 108
rent = lambda n: (128 + n) * 6_960


def case(op, a=2, b=0, **changes):
    item = dict(op=op, a=a, b=b, signed=True, signer=ADMIN, signer_lamports=10**10, holder='control',
                admin=ADMIN, reserves_admin=RESERVES_ADMIN, mints=((2, 100), (3, 200)), len=None, lamports=None,
                fill=0xEE)
    item.update(changes)
    if item['len'] is None:
        item['len'] = HEADER + 40 * len(item['mints'])
    if item['lamports'] is None:
        item['lamports'] = 0 if item['holder'] == 'missing' else rent(item['len'])
    return item


def serialize(admin, reserves_admin, mints):
    return (ACCOUNT_DISC['QuoteControl'] + bytes(KEYS[admin]) + bytes(KEYS[reserves_admin]) + bytes(32)
            + len(mints).to_bytes(4, 'little') + b''.join(bytes(KEYS[m]) + struct.pack('<Q', r) for m, r in mints))


def control_bytes(item):
    body = serialize(item['admin'], item['reserves_admin'], item['mints'])
    data = (body + bytes([item['fill']]) * item['len'])[:item['len']]
    if item['holder'] == 'disc':
        data = ACCOUNT_DISC['Global'] + data[8:]
    if item['holder'] == 'short':
        data = data[:100]
    return data


def host_line(item):
    mints = '+'.join(f'{m}:{r}' for m, r in item['mints']) or '-'
    return ','.join(map(str, (item['op'], item['a'], item['b'], int(item['signed']), item['signer'],
                              item['signer_lamports'], GLOBAL_AUTHORITY, item['holder'], item['admin'],
                              item['reserves_admin'], item['len'], item['lamports'], mints)))


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.set_clock(Clock(100, NOW, 0, 0, NOW))
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    signer = SIGNERS[item['signer']]
    if item['signer_lamports']:
        vm.set_account(signer.pubkey(), Account(item['signer_lamports'], b'', SYSTEM))
    global_data = bytearray(1088)
    global_data[:8] = ACCOUNT_DISC['Global']
    global_data[8] = 1
    global_data[9:41] = bytes(KEYS[GLOBAL_AUTHORITY])
    vm.set_account(GLOBAL, Account(10**9, bytes(global_data), PUMP))
    holder = item['holder']
    if holder == 'system':
        vm.set_account(QUOTE_CONTROL, Account(item['lamports'], b'', SYSTEM))
    elif holder != 'missing':
        vm.set_account(QUOTE_CONTROL, Account(item['lamports'], control_bytes(item),
                                              FOREIGN if holder == 'owner' else PUMP))
    names = {'authority': signer.pubkey(), 'user': signer.pubkey(), 'global': GLOBAL, 'quote_control': QUOTE_CONTROL,
             'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    ix = IX[item['op']]
    metas = [AccountMeta(names[a['name']], a.get('signer', False) and item['signed'], a.get('writable', False))
             for a in ix['accounts']]
    args = {'init': b'', 'add': bytes(KEYS[item['a']]) + struct.pack('<Q', item['b']),
            'remove': bytes(KEYS[item['a']]), 'reserves': bytes(KEYS[item['a']]) + struct.pack('<Q', item['b']),
            'admin': bytes(KEYS[item['a']]), 'reserves_admin': bytes(KEYS[item['a']])}[item['op']]
    signers = [PAYER] + ([signer] if item['signed'] else [])
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(ix['discriminator']) + args, metas)],
                                           PAYER.pubkey(), signers, vm.latest_blockhash())
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    watched = (signer.pubkey(), QUOTE_CONTROL)
    before = [lamports(k) for k in watched]
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    after = vm.get_account(QUOTE_CONTROL)
    return {'error': None, 'delta': [lamports(k) - b for k, b in zip(watched, before)],
            'account': (after.lamports, str(after.owner), bytes(after.data)),
            'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]}


def parse_mints(text):
    return [] if text == '-' else [tuple(map(int, pair.split(':'))) for pair in text.split('+')]


def fixed_cases():
    cases = []
    add = lambda op, *args, **k: cases.append(case(op, *args, **k))
    # initialize: anyone; 2,108 bytes; both admins left as the zero key.
    for signer in (OUTSIDER, GLOBAL_AUTHORITY):
        add('init', signer=signer, holder='missing')
    for lamports in (1, 10**6, rent(2108) - 1, rent(2108), 10**10):
        add('init', signer=OUTSIDER, holder='system', lamports=lamports)
    add('init', signer=OUTSIDER, holder='missing', signer_lamports=rent(2108))
    add('init', signer=OUTSIDER, holder='missing', signer_lamports=rent(2108) - 1)
    add('init', signer=OUTSIDER, holder='system', lamports=1000, signer_lamports=rent(2108) - 1000)
    add('init', signer=OUTSIDER, holder='system', lamports=1000, signer_lamports=rent(2108) - 1001)
    for holder in ('control', 'owner', 'disc'):
        add('init', signer=OUTSIDER, holder=holder)
        add('init', signer=OUTSIDER, holder=holder, signer_lamports=1000)
        add('init', signer=OUTSIDER, holder=holder, lamports=rent(2108), signer_lamports=1000)
    add('init', signer=OUTSIDER, holder='missing', signed=False)
    # add: admin or global authority; grows to the exact serialized size, the
    # signer paying only the shortfall to rent.
    for signer in (ADMIN, GLOBAL_AUTHORITY, RESERVES_ADMIN, OUTSIDER):
        add('add', 4, 300, signer=signer)
    add('add', 4, 300, signer=OUTSIDER, admin=OUTSIDER)
    add('add', 4, 300, signer=RESERVES_ADMIN, admin=RESERVES_ADMIN, reserves_admin=RESERVES_ADMIN)
    for reserves in (0, 1, 2**64 - 1):
        add('add', 5, reserves)
    add('add', 4, 7, mints=())
    for mint in (0, 1):
        add('add', mint, 7)
        add('add', mint, 7, mints=((mint, 1),))
        add('add', mint, 7, signer=OUTSIDER)
    for mint in (2, 3):
        add('add', mint, 7)
    add('add', 2, 7, signer=OUTSIDER)
    for lamports in (1, rent(188) - 1, rent(188), rent(228) - 1, rent(228), rent(228) + 1, 10**9):
        add('add', 4, 9, lamports=lamports)
    for length in (188, 228, 300, 2108):
        add('add', 4, 9, len=length, lamports=rent(min(length, 228)) - 1)
        add('add', 4, 9, len=length)
    add('add', 4, 9, mints=tuple((m, m) for m in range(2, 10) if m != 4) * 7, len=2108, lamports=rent(2108))
    # No cap at 50: a 51st entry grows the account past the initial 2,108 bytes.
    add('add', 4, 9, mints=tuple((m, m) for m in range(2, 10) if m != 4) * 7 + ((1, 1),), len=2108,
        lamports=rent(2108))
    add('add', 4, 9, signer_lamports=278_400)
    add('add', 4, 9, signer_lamports=278_399)
    add('add', 4, 9, signer_lamports=278_399, lamports=rent(228) + 1)
    add('add', 4, 9, lamports=rent(188), signer_lamports=278_400)
    # remove: the first match is taken out in order; the size never shrinks.
    for signer in (ADMIN, GLOBAL_AUTHORITY, RESERVES_ADMIN, OUTSIDER):
        add('remove', 2, signer=signer)
    for mint in (2, 3, 4, 0, 1):
        add('remove', mint, mints=((2, 1), (3, 2), (4, 3)))
    add('remove', 1, mints=((1, 5), (2, 1)))
    add('remove', 0, mints=((0, 5),))
    add('remove', 2, mints=((2, 1), (3, 2), (2, 3)))
    add('remove', 2, mints=((2, 1),), lamports=1)
    add('remove', 2, mints=(), len=300)
    add('remove', 5, signer=OUTSIDER)
    # set reserves: admin, reserves admin or global authority; first match only.
    for signer in (ADMIN, GLOBAL_AUTHORITY, RESERVES_ADMIN, OUTSIDER):
        add('reserves', 3, 77, signer=signer)
    for value in (0, 200, 2**64 - 1):
        add('reserves', 3, value)
    add('reserves', 5, 1)
    add('reserves', 5, 1, signer=OUTSIDER)
    add('reserves', 1, 9, mints=((1, 5),))
    add('reserves', 0, 9, mints=((0, 5),))
    add('reserves', 0, 9)
    add('reserves', 2, 9, mints=((2, 1), (3, 2), (2, 3)))
    # admin rotation: only the global authority; reserves admin: admin or global authority.
    for signer in (ADMIN, GLOBAL_AUTHORITY, RESERVES_ADMIN, OUTSIDER):
        add('admin', OUTSIDER, signer=signer)
        add('reserves_admin', OUTSIDER, signer=signer)
    for new in (0, ADMIN, RESERVES_ADMIN):
        add('admin', new, signer=GLOBAL_AUTHORITY)
        add('reserves_admin', new, signer=ADMIN)
    add('admin', OUTSIDER, signer=GLOBAL_AUTHORITY, admin=0, reserves_admin=0, mints=(), len=2108)
    # Account checks.
    for op in ('add', 'remove', 'reserves', 'admin', 'reserves_admin'):
        for holder in ('missing', 'system', 'owner', 'disc', 'short'):
            add(op, 3, 9, holder=holder, signer=GLOBAL_AUTHORITY)
        add(op, 3, 9, signed=False, signer=GLOBAL_AUTHORITY)
        add(op, 3, 9, signed=False, holder='missing')
        add(op, 3, 9, holder='missing', signer=OUTSIDER)
    return cases


def random_cases(count=120, seed=1891):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        op = rng.choice(('add',) * 3 + ('remove',) * 2 + ('reserves',) * 2 + ('admin', 'reserves_admin', 'init'))
        mints = tuple((rng.choice((0, 1) + tuple(range(2, 10)) * 3), rng.choice((0, 1, rng.randrange(2**64))))
                      for _ in range(rng.randrange(0, 6)))
        length = HEADER + 40 * len(mints) + rng.choice((0, 0, 0, rng.randrange(0, 200)))
        holder = rng.choice(('control',) * 10 + ('missing', 'system', 'owner', 'disc', 'short'))
        if op == 'init':
            holder = rng.choice(('missing', 'system', 'control'))
        lamports = 0 if holder == 'missing' else rng.choice((rent(length), 10**9, rng.randrange(1, rent(length))))
        a = rng.choice(tuple(range(0, 10)) + (ADMIN, OUTSIDER)) if op in ('admin', 'reserves_admin') else \
            rng.choice((0, 1) + tuple(range(2, 10)) * 2)
        cases.append(case(op, a, rng.choice((0, 1, rng.randrange(2**64))), mints=mints, len=length,
                          lamports=lamports, holder=holder, signed=rng.random() > 0.08,
                          signer=rng.choice((ADMIN, ADMIN, GLOBAL_AUTHORITY, RESERVES_ADMIN, OUTSIDER)),
                          admin=rng.choice((ADMIN, ADMIN, 0, OUTSIDER)), reserves_admin=rng.choice((RESERVES_ADMIN, 0)),
                          signer_lamports=rng.choice((10**10, 10**10, rng.randrange(1, 4 * 10**5))),
                          fill=rng.randrange(256)))
    return cases


class QuoteControlCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'quote-control-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        answers = subprocess.run([str(self.host)], input=text, capture_output=True, text=True,
                                 check=True).stdout.splitlines()
        self.assertEqual(len(answers), len(cases))
        return answers

    def assert_matches(self, item, answer, captured):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        fields = answer.split(',')
        paid, length, lamports, admin, reserves_admin, old = map(int, fields[1:7])
        mints = parse_mints(fields[7])
        # Signed lamport deltas: the signer pays exactly what the account gains.
        self.assertEqual(captured['delta'], [-paid, paid])
        body = serialize(admin, reserves_admin, mints)
        if item['op'] == 'init':
            data = (body + bytes(length))[:length]
        else:
            previous = control_bytes(item)
            data = (body + previous[len(body):] + bytes(length))[:length]
        self.assertEqual(captured['account'], (lamports, str(PUMP), data))
        authority = bytes(SIGNERS[item['signer']].pubkey())
        head = bytes(QUOTE_CONTROL) + authority
        tail = struct.pack('<q', NOW)
        mint = bytes(KEYS[item['a']])
        op = item['op']
        if op == 'init':
            expected = []
        elif op == 'add':
            expected = [EVENT_DISC['AddQuoteControlMintEvent'] + head + mint + struct.pack('<Q', old) + tail]
        elif op == 'remove':
            expected = [EVENT_DISC['RemoveQuoteControlMintEvent'] + head + mint + tail]
        elif op == 'reserves':
            expected = [EVENT_DISC['SetQuoteControlMintReservesEvent'] + head + mint
                        + struct.pack('<QQ', old, item['b']) + tail]
        elif op == 'admin':
            expected = [EVENT_DISC['SetQuoteControlAdminEvent'] + head + bytes(KEYS[old]) + bytes(KEYS[admin]) + tail]
        else:
            expected = [EVENT_DISC['SetQuoteControlReservesAdminEvent'] + head + bytes(KEYS[old])
                        + bytes(KEYS[reserves_admin]) + tail]
        self.assertEqual(captured['events'], expected)

    def run_cases(self, cases):
        for item, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: passing captured runs must fail once the payment
        # is reversed, a reserve value changes, or the list order changes.
        samples = (case('add', 4, 9, lamports=1), case('remove', 2, mints=((2, 1), (3, 2), (4, 3))),
                   case('reserves', 3, 77), case('init', signer=OUTSIDER, holder='missing'))
        for item, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            fields = answer.split(',')
            tampered = []
            if int(fields[1]):
                tampered.append(dict(captured, delta=[-d for d in captured['delta']]))
            if fields[7] != '-':
                mints = parse_mints(fields[7])
                bumped = '+'.join(f'{m}:{r + 1}' for m, r in mints)
                swapped = '+'.join(f'{m}:{r}' for m, r in reversed(mints))
                for text in {bumped, swapped} - {fields[7]}:
                    with self.subTest(case=host_line(item), mints=text):
                        with self.assertRaises(AssertionError):
                            self.assert_matches(item, ','.join(fields[:7] + [text]), captured)
            else:
                for i in (3, 4):
                    text = ','.join(fields[:i] + [str(int(fields[i]) + 1)] + fields[i + 1:])
                    with self.assertRaises(AssertionError):
                        self.assert_matches(item, text, captured)
            for flipped in tampered:
                with self.assertRaises(AssertionError):
                    self.assert_matches(item, answer, flipped)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers} - {'ok'}, {
            'error:0', 'error:1', 'error:3002', 'error:3003', 'error:3007', 'error:3010', 'error:3012', 'error:6000',
            'error:6067', 'error:6068', 'error:6069'})
        self.assertTrue(any(a.startswith('ok,') and a.split(',')[1] != '0' for a in answers))


if __name__ == '__main__':
    unittest.main()
