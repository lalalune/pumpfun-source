"""Captured-program checks for bonding-curve creator assignment.

Every case runs Pump `set_creator`, `set_metaplex_creator`, or
`migrate_bonding_curve_creator` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, against synthetic Global,
Metaplex metadata, bonding-curve and pump_fees SharingConfig accounts. The
same inputs go to `programs/pump/recovered/creator_assignment_host.rs`. The
error, the resulting curve bytes, the signed lamport deltas (only the
transaction fee moves) and the emitted event must agree. This shows matching
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/creator_assignment_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
METAPLEX = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}
IX = {'set': 'set_creator', 'metaplex': 'set_metaplex_creator', 'migrate': 'migrate_bonding_curve_creator'}
IX = {op: next(i for i in IDL['instructions'] if i['name'] == name) for op, name in IX.items()}

PAYER = Keypair.from_seed(bytes([221]) * 32)
AUTHORITY = Keypair.from_seed(bytes([222]) * 32)
INTRUDER = Keypair.from_seed(bytes([223]) * 32)
MINT = Pubkey.from_bytes(bytes([31]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([32]) * 32)
ELSEWHERE = Pubkey.from_bytes(bytes([55]) * 32)
GLOBAL = Pubkey.find_program_address([b'global'], PUMP)[0]
CURVE = Pubkey.find_program_address([b'bonding-curve', bytes(MINT)], PUMP)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
METADATA = Pubkey.find_program_address([b'metadata', bytes(METAPLEX), bytes(MINT)], METAPLEX)[0]
SHARING = Pubkey.find_program_address([b'sharing-config', bytes(MINT)], FEES)[0]
SHARING_ID = 9
KEYS = {0: SYSTEM, 1: Pubkey.from_bytes(bytes([41]) * 32), 2: Pubkey.from_bytes(bytes([42]) * 32),
        3: Pubkey.from_bytes(bytes([43]) * 32), SHARING_ID: SHARING}
NOW = 1_700_000_000
FEE = 5_000


def case(op, **changes):
    item = dict(op=op, signed=True, authority_ok=True, metadata='ok', metadata_address_ok=True, creators=(1,),
                verified=True, curve_len=166, curve_address_ok=True, curve_creator=0, argument=2, sharing='ok',
                sharing_address_ok=True, sharing_mint_ok=True, sharing_admin=2, status=1, revoked=False,
                holders=((1, 10_000),), complete=False, tail=0x5A,
                holder_reward=False, creator_fee=0)
    item.update(changes)
    return item


def host_line(item):
    creators = item['creators']
    text = 'none' if creators is None else ('empty' if not creators else '+'.join(map(str, creators)))
    flags = lambda *names: [str(int(item[n])) for n in names]
    return ','.join([item['op'], *flags('signed', 'authority_ok'), item['metadata'], *flags('metadata_address_ok'),
                     text, str(item['curve_len']), *flags('curve_address_ok'), str(item['curve_creator']),
                     *flags('holder_reward'), str(item['creator_fee']), str(item['argument']), item['sharing'], *flags('sharing_address_ok', 'sharing_mint_ok'),
                     str(item['sharing_admin']), str(SHARING_ID)])


def text(value):
    raw = value.encode()
    return len(raw).to_bytes(4, 'little') + raw


def metadata_bytes(item):
    creators = item['creators']
    data = bytes([4]) + bytes(AUTHORITY.pubkey()) + bytes(MINT) + text('Synthetic') + text('SYN') + text('') + bytes(2)
    if creators is None:
        data += b'\0'
    else:
        data += b'\1' + len(creators).to_bytes(4, 'little') + b''.join(
            bytes(KEYS[k]) + bytes([int(item['verified']), 100 // len(creators)]) for k in creators)
    data += bytes([0, 1]) + bytes(16)
    if item['metadata'] == 'disc':
        data = bytes([0]) + data[1:]
    if item['metadata'] == 'data':
        data = data[:50]
    return data


def curve_bytes(item):
    data = bytearray([item['tail']]) * 166
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, 10**15, 3 * 10**10, 8 * 10**14, 0, 10**15)
    data[48] = int(item['complete'])
    data[49:81] = bytes(KEYS[item['curve_creator']])
    for flag in (81, 82, 123):  # the other bool fields must stay 0 or 1
        data[flag] = item['tail'] & 1
    data[124] = int(item['holder_reward'])
    struct.pack_into('<Q', data, 125, item['creator_fee'])
    return bytes(data[:item['curve_len']]) + bytes(max(0, item['curve_len'] - 166))


def sharing_bytes(item):
    disc = ACCOUNT_DISC['Global'] if item['sharing'] == 'disc' else ACCOUNT_DISC['SharingConfig']
    status = 2 if item['sharing'] == 'data' else item['status']
    data = disc + bytes([255, 1, status]) + bytes(MINT if item['sharing_mint_ok'] else OTHER_MINT)
    data += bytes(KEYS[item['sharing_admin']]) + bytes([int(item['revoked'])])
    data += len(item['holders']).to_bytes(4, 'little') + b''.join(
        bytes(KEYS[k]) + struct.pack('<H', bps) for k, bps in item['holders'])
    return data


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.set_clock(Clock(100, NOW, 0, 0, NOW))
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    global_data = bytearray(1088)
    global_data[:8] = ACCOUNT_DISC['Global']
    global_data[8] = 1
    global_data[386:418] = bytes(AUTHORITY.pubkey())
    global_data[418:450] = bytes(INTRUDER.pubkey())  # admin_set_creator_authority is not accepted
    vm.set_account(GLOBAL, Account(10**9, bytes(global_data), PUMP))
    mint = bytearray(82)
    mint[44], mint[45] = 6, 1
    vm.set_account(MINT, Account(10**9, bytes(mint), TOKEN))
    curve_key = CURVE if item['curve_address_ok'] else ELSEWHERE
    metadata_key = METADATA if item['metadata_address_ok'] else Pubkey.from_bytes(bytes([56]) * 32)
    sharing_key = SHARING if item['sharing_address_ok'] else Pubkey.from_bytes(bytes([57]) * 32)
    vm.set_account(curve_key, Account(2 * 10**9, curve_bytes(item), PUMP))
    if item['metadata'] != 'missing':
        owner = SYSTEM if item['metadata'] == 'owner' else METAPLEX
        vm.set_account(metadata_key, Account(10**9, metadata_bytes(item), owner))
    if item['sharing'] != 'missing':
        owner = PUMP if item['sharing'] == 'owner' else FEES
        vm.set_account(sharing_key, Account(10**9, sharing_bytes(item), owner))
    signer = AUTHORITY if item['authority_ok'] else INTRUDER
    names = {'set_creator_authority': signer.pubkey(), 'global': GLOBAL, 'mint': MINT, 'metadata': metadata_key,
             'bonding_curve': curve_key, 'sharing_config': sharing_key, 'event_authority': EVENT_AUTHORITY,
             'program': PUMP}
    ix = IX[item['op']]
    metas = [AccountMeta(names[a['name']], a.get('signer', False) and item['signed'], a.get('writable', False))
             for a in ix['accounts']]
    data = bytes(ix['discriminator']) + (bytes(KEYS[item['argument']]) if item['op'] == 'set' else b'')
    signers = [PAYER] + ([signer] if any(m.is_signer and m.pubkey == signer.pubkey() for m in metas) else [])
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], PAYER.pubkey(), signers,
                                           vm.latest_blockhash())
    watched = [PAYER.pubkey(), GLOBAL, MINT, metadata_key, curve_key, sharing_key]
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [lamports(key) for key in watched]
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        message = str(result.err())
        code = re.search(r'Custom\((\d+)\)', message)
        logs = ' '.join(result.meta().logs())
        if code:
            return {'error': int(code.group(1))}
        if 'panicked' in logs:
            return {'error': 'panic'}
        if 'failed to write whole buffer' in logs:
            return {'error': 'borsh_write'}
        if 'BorshIoError' in message:
            return {'error': 'borsh_read'}
        if 'InvalidAccountData' in message:
            return {'error': 'invalid_data'}
        return {'error': message}
    return {'error': None, 'fee': FEE * len(signers),
            'delta': [lamports(k) - b for k, b in zip(watched, before)],
            'curve': bytes(vm.get_account(curve_key).data),
            'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]}


def fixed_cases():
    cases = []
    # Migration cases start from a curve whose creator is the sharing admin.
    add = lambda op, **k: cases.append(case(op, **({'curve_creator': 2} if op == 'migrate' else {}) | k))
    # set_creator: an unset creator is filled; Metaplex creators beat the argument.
    for creators in ((1,), (3,), (2, 1), (3, 1, 2), (0,), None):
        add('set', creators=creators)
    add('set', creators=(1,), verified=False)
    for argument in (0, 1, 3):
        add('set', creators=None, argument=argument)
    add('set', creators=None, complete=True)
    add('set', complete=True)
    # An already-set creator is never overwritten, even by the authority.
    for creator in (1, 2, 3):
        add('set', curve_creator=creator)
        add('set', curve_creator=creator, creators=None, argument=1)
    add('set', curve_creator=1, creators=())
    add('set', creators=())
    add('set', creators=(), curve_len=150)
    # Account checks and their order.
    add('set', signed=False)
    add('set', signed=False, metadata='missing')
    add('set', authority_ok=False)
    add('set', authority_ok=False, metadata='missing')
    add('set', authority_ok=False, curve_len=40)
    add('set', authority_ok=False, curve_len=150)
    add('set', authority_ok=False, metadata_address_ok=False)
    for state in ('missing', 'owner', 'disc', 'data'):
        add('set', metadata=state)
    add('set', metadata='missing', curve_len=40)
    add('set', metadata_address_ok=False)
    add('set', curve_address_ok=False)
    add('set', metadata_address_ok=False, curve_len=40)
    for length in (0, 8, 48, 49, 80, 81, 150, 165, 167, 200):
        add('set', curve_len=length)
        add('set', curve_len=length, curve_creator=1)
    # set_metaplex_creator: anyone may copy the first Metaplex creator into an unset curve.
    for creators in ((1,), (3,), (2, 1), (3, 1, 2), (0,)):
        add('metaplex', creators=creators)
    add('metaplex', creators=(1,), verified=False)
    add('metaplex', creators=None)
    add('metaplex', creators=None, curve_len=150)
    add('metaplex', creators=())
    add('metaplex', creators=(), curve_creator=2)
    add('metaplex', complete=True)
    for creator in (1, 2, 3):
        add('metaplex', curve_creator=creator)
    for state in ('missing', 'owner', 'disc', 'data'):
        add('metaplex', metadata=state)
    add('metaplex', metadata_address_ok=False)
    add('metaplex', curve_address_ok=False)
    add('metaplex', metadata='missing', curve_len=40)
    add('metaplex', metadata_address_ok=False, curve_len=40)
    for length in (8, 48, 49, 81, 165, 200):
        add('metaplex', curve_len=length)
        add('metaplex', curve_len=length, curve_creator=3)
    # migrate_bonding_curve_creator: the admin's curve moves to the sharing config.
    for creator in (0, 1, 2, 3):
        add('migrate', curve_creator=creator, sharing_admin=creator)
    add('migrate', curve_creator=SHARING_ID, sharing_admin=SHARING_ID)
    for status in (0, 1):
        add('migrate', status=status)
    add('migrate', revoked=True)
    add('migrate', holders=())
    add('migrate', holders=((1, 5_000), (3, 5_000)))
    add('migrate', complete=True)
    add('migrate', curve_creator=1, sharing_admin=2)
    add('migrate', curve_creator=0, sharing_admin=2)
    add('migrate', curve_creator=SHARING_ID, sharing_admin=2)
    add('migrate', curve_creator=1, holders=((1, 10_000),))
    add('migrate', sharing_mint_ok=False)
    add('migrate', sharing_mint_ok=False, curve_creator=1)
    for state in ('missing', 'owner', 'disc', 'data'):
        add('migrate', sharing=state)
        add('migrate', sharing=state, curve_len=40)
    add('migrate', curve_address_ok=False)
    add('migrate', sharing_address_ok=False)
    add('migrate', curve_address_ok=False, sharing='missing')
    add('migrate', sharing_address_ok=False, sharing_mint_ok=False)
    add('migrate', curve_address_ok=False, sharing_mint_ok=False)
    for length in (8, 48, 49, 150, 165, 200):
        add('migrate', curve_len=length)
    add('migrate', curve_len=150, curve_creator=1)
    # Holder-reward coins and unswept creator fees block the migration.
    add('migrate', curve_creator=2, holder_reward=True)
    for fee in (1, 2**64 - 1):
        add('migrate', curve_creator=2, creator_fee=fee)
        add('migrate', curve_creator=2, creator_fee=fee, holder_reward=True)
    add('migrate', curve_creator=1, holder_reward=True)
    add('migrate', curve_creator=1, creator_fee=5)
    add('migrate', curve_creator=2, creator_fee=5, sharing_mint_ok=False)
    add('migrate', curve_creator=0, sharing_admin=0, holder_reward=True)
    add('migrate', curve_creator=2, creator_fee=1, complete=True)
    for length in (49, 80, 81):
        add('migrate', curve_len=length)
        add('migrate', curve_len=length, curve_creator=0, sharing_admin=0)
    for length in (124, 125, 140, 141, 150):
        add('migrate', curve_creator=2, holder_reward=True, curve_len=length)
        add('migrate', curve_creator=2, creator_fee=1, curve_len=length)
    # The setters do not consult either field.
    for op in ('set', 'metaplex'):
        add(op, holder_reward=True)
        add(op, creator_fee=7)
    add('set', holder_reward=True, creators=None)
    return cases


def random_cases(count=120, seed=1891):
    rng = random.Random(seed)
    cases = []
    pick = lambda *options: rng.choice(options)
    for _ in range(count):
        size = rng.randrange(5)
        creators = None if size == 4 else tuple(rng.choice((0, 1, 2, 3)) for _ in range(size))
        cases.append(case(
            pick('set', 'metaplex', 'migrate'), signed=rng.random() > 0.1, authority_ok=rng.random() > 0.15,
            metadata=pick(*('ok',) * 8, 'missing', 'owner', 'disc', 'data'), metadata_address_ok=rng.random() > 0.1,
            creators=creators, verified=rng.random() > 0.5,
            curve_len=pick(*(166,) * 6, 200, rng.randrange(0, 260)), curve_address_ok=rng.random() > 0.1,
            curve_creator=pick(0, 0, 0, 1, 2, 3, SHARING_ID), argument=pick(0, 1, 2, 3),
            sharing=pick(*('ok',) * 8, 'missing', 'owner', 'disc', 'data'), sharing_address_ok=rng.random() > 0.1,
            sharing_mint_ok=rng.random() > 0.1, sharing_admin=pick(0, 1, 2, 3, SHARING_ID, None, None),
            status=pick(0, 1), revoked=rng.random() > 0.7, complete=rng.random() > 0.8, tail=rng.randrange(256),
            holder_reward=rng.random() > 0.8, creator_fee=pick(0, 0, 0, 1, rng.randrange(2**64))))
    for item in cases:
        if item['sharing_admin'] is None:  # half the time, the curve creator is the admin
            item['sharing_admin'] = item['curve_creator']
    return cases


class CreatorAssignmentCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'creator-assignment-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        lines = ''.join(host_line(item) + '\n' for item in cases)
        return subprocess.run([str(self.host)], input=lines, capture_output=True, text=True,
                              check=True).stdout.splitlines()

    def assert_matches(self, item, answer, captured):
        if not answer.startswith('ok,'):
            expected = int(answer[6:]) if answer.startswith('error:') else answer
            self.assertEqual(captured['error'], expected)
            return
        self.assertIsNone(captured['error'])
        _, creator, event = answer.split(',')
        creator = KEYS[int(creator)]
        # Signed lamport deltas: only the payer's transaction fee moves.
        self.assertEqual(captured['delta'], [-captured['fee'], 0, 0, 0, 0, 0])
        before = curve_bytes(item)
        self.assertEqual(captured['curve'], before[:49] + bytes(creator) + before[81:])
        head = struct.pack('<q', NOW) + bytes(MINT) + bytes(CURVE)
        expected = {
            'none': [],
            'set': [EVENT_DISC['SetCreatorEvent'] + head + bytes(creator)],
            'metaplex': [EVENT_DISC['SetMetaplexCreatorEvent'] + head + bytes(METADATA) + bytes(creator)],
        }.get(event)
        if event.startswith('migrate:'):
            old = KEYS[int(event[8:])]
            expected = [EVENT_DISC['MigrateBondingCurveCreatorEvent'] + head + bytes(SHARING) + bytes(old)
                        + bytes(creator)]
        self.assertEqual(captured['events'], expected)

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: passing captured runs must fail once the creator,
        # the event, or the fee delta is altered.
        samples = (case('set'), case('set', creators=None), case('metaplex'), case('migrate', curve_creator=2))
        for item, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            _, creator, event = answer.split(',')
            wrong_creator = ','.join(['ok', '3' if creator != '3' else '1', event])
            wrong_event = ','.join(['ok', creator, 'none'])
            for tampered in (wrong_creator, wrong_event):
                with self.subTest(case=host_line(item), tampered=tampered):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(item, tampered, captured)
            reversed_fee = dict(captured, delta=[captured['fee']] + captured['delta'][1:])
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, reversed_fee)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers} - {'ok'}, {
            'error:2006', 'error:3002', 'error:3003', 'error:3007', 'error:3010', 'error:3012', 'error:6000',
            'error:6004', 'error:6053', 'error:6083', 'error:6095', 'invalid_data', 'borsh_read', 'borsh_write', 'panic'})
        self.assertEqual({a.split(',')[2].split(':')[0] for a in answers if a.startswith('ok')},
                         {'none', 'set', 'metaplex', 'migrate'})


if __name__ == '__main__':
    unittest.main()
