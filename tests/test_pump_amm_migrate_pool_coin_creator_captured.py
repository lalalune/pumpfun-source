"""Captured-program checks for PumpSwap `migrate_pool_coin_creator`.

Each case builds a synthetic pool, Pump Fees `SharingConfig` and instruction,
runs it on `evidence/original/pump_amm/deployed.so` in LiteSVM, and feeds the
same bytes to `programs/pump-amm/recovered/migrate_pool_coin_creator_host.rs`.
The host gets the raw pool and sharing-config bytes; owners and PDA matches are
worked out here from the accounts actually loaded. The error (custom code or
runtime error), the committed pool bytes, the `MigratePoolCoinCreatorEvent` in
the log and the same bytes in the `emit_cpi!` self-call must agree, and nothing
else may move. This is matching behaviour on these inputs only, not a
byte-identity claim. `scripts/pump_amm_creator_reassignment_differential.py`
compares candidate builds with the captured program; this test pins the
captured outcomes to a model instead and does not read `research/`.
"""
from pathlib import Path
import base64
import hashlib
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
AMM_ELF = ROOT / 'evidence/original/pump_amm/deployed.so'
AMM_SHA256 = '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7'
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/migrate_pool_coin_creator_host.rs'

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.default()
DISCRIMINATOR = bytes([208, 8, 159, 4, 74, 175, 16, 58])
POOL_DISC = hashlib.sha256(b'account:Pool').digest()[:8]
SHARING_DISC = hashlib.sha256(b'account:SharingConfig').digest()[:8]
EVENT_DISC = hashlib.sha256(b'event:MigratePoolCoinCreatorEvent').digest()[:8]
# Anchor's EVENT_IX_TAG, the u64 0x1d9acb512ea545e4 in little-endian order.
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
PAYER = Keypair.from_seed(bytes([231]) * 32)
ADMIN = Keypair.from_seed(bytes([232]) * 32).pubkey()
OTHER = Keypair.from_seed(bytes([233]) * 32).pubkey()
BASE_MINT = Keypair.from_seed(bytes([234]) * 32).pubkey()
QUOTE_MINT = Pubkey.from_string('So11111111111111111111111111111111111111112')
POOL_CREATOR = Pubkey.find_program_address([b'pool-authority', bytes(BASE_MINT)], PUMP)[0]
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
STRAY_SHARING = Pubkey.from_bytes(bytes([78]) * 32)
NOW = 1_761_800_000
ACCOUNTS = ('pool', 'sharing_config', 'event_authority', 'program')


def pool_address(data):
    """`["pool", index, creator, base_mint, quote_mint]` read from the pool's own bytes."""
    data = bytes(data).ljust(107, b'\0')
    return Pubkey.find_program_address([b'pool', data[9:11], data[11:43], data[43:75], data[75:107]], AMM)[0]


def pool_bytes(c):
    data = bytearray(300)
    data[:8] = POOL_DISC
    data[8] = 254
    data[9:11] = struct.pack('<H', c.get('index', 0))
    data[11:43] = bytes(POOL_CREATOR)
    data[43:75] = bytes(BASE_MINT)
    data[75:107] = bytes(QUOTE_MINT)
    for i, at in enumerate((107, 139, 171)):
        data[at:at + 32] = bytes([40 + i]) * 32
    data[203:211] = struct.pack('<Q', 4_000_000)
    data[211:243] = bytes(c.get('coin_creator', ADMIN))
    data[245:261] = (12_345).to_bytes(16, 'little', signed=True)
    data[261:269] = struct.pack('<Q', 30)
    data[269] = 1
    data[271:279] = struct.pack('<Q', 55)
    for at, value in c.get('pool_patches', ()):
        data[at:at + len(value)] = value
    if 'pool_length' in c:
        data = data[:c['pool_length']]
    return bytes(data)


def sharing_bytes(c, bump):
    holders = c.get('holders', [(ADMIN, 10_000)])
    data = bytearray(SHARING_DISC + bytes([bump, c.get('version', 2), c.get('status', 1)]) + bytes(c.get('sharing_mint', BASE_MINT))
                     + bytes(c.get('sharing_admin', ADMIN)) + bytes([c.get('revoked', 0)]) + struct.pack('<I', len(holders))
                     + b''.join(bytes(k) + struct.pack('<H', w) for k, w in holders))
    data = data.ljust(c.get('sharing_pad', len(data)), b'\0')
    for at, value in c.get('sharing_patches', ()):
        data[at:at + len(value)] = value
    if 'sharing_length' in c:
        data = data[:c['sharing_length']]
    return bytes(data)


def setup(c):
    pool = pool_bytes(c)
    pool_key = c.get('pool_key', pool_address(pool_bytes({k: v for k, v in c.items() if k != 'pool_length'})))
    sharing_seed_mint = bytes(pool).ljust(75, b'\0')[43:75]
    sharing_pda, bump = Pubkey.find_program_address([b'sharing-config', sharing_seed_mint], FEES)
    sharing_key = c.get('sharing_key', sharing_pda)
    keys = {'pool': pool_key, 'sharing_config': sharing_key, 'event_authority': c.get('event_key', EVENT_AUTHORITY),
            'program': c.get('program_key', AMM)}
    accounts = {pool_key: Account(10**9, pool, c.get('pool_owner', AMM)),
                sharing_key: Account(10**9, sharing_bytes(c, bump), c.get('sharing_owner', FEES))}
    metas = [AccountMeta(keys[n], False, n == 'pool' and not c.get('readonly')) for n in ACCOUNTS]
    count = c.get('count', 4)
    if count > len(metas):
        metas.extend(AccountMeta(PAYER.pubkey(), False, False) for _ in range(count - len(metas)))
    metas = metas[:count]
    data = (DISCRIMINATOR + bytes.fromhex(c.get('trailing', '')))[:c.get('payload', 8 + len(c.get('trailing', '')) // 2)]
    return pool_key, sharing_key, accounts, metas, data


def host_line(c):
    pool_key, sharing_key, accounts, metas, data = setup(c)
    pool = accounts[pool_key]
    sharing = accounts[sharing_key]
    by_name = dict(zip(ACCOUNTS, metas))
    pool_data = bytes(pool.data)
    seed_mint = pool_data.ljust(75, b'\0')[43:75]
    flags = [
        pool.owner == AMM,
        by_name.get('pool') is not None and by_name['pool'].is_writable,
        pool_data.ljust(75, b'\0')[11:43] == bytes(Pubkey.find_program_address([b'pool-authority', seed_mint], PUMP)[0]),
        pool_key == pool_address(pool_data),
        sharing.owner == FEES,
        sharing_key == Pubkey.find_program_address([b'sharing-config', seed_mint], FEES)[0],
        'event_authority' in by_name and by_name['event_authority'].pubkey == EVENT_AUTHORITY,
        'program' in by_name and by_name['program'].pubkey == AMM,
    ]
    return ','.join([str(len(data)), str(len(metas)), ''.join('1' if f else '0' for f in flags), pool_data.hex(),
                     bytes(sharing.data).hex(), bytes(pool_key).hex(), bytes(sharing_key).hex(), str(NOW)])


def run_captured(c):
    pool_key, sharing_key, accounts, metas, data = setup(c)
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(AMM, AMM_ELF)
    clock = vm.get_clock()
    vm.set_clock(Clock(clock.slot, clock.epoch_start_timestamp, clock.epoch, clock.leader_schedule_epoch, NOW))
    vm.airdrop(PAYER.pubkey(), 10**10)
    for key, account in accounts.items():
        vm.set_account(key, account)
    if c.get('program_key') == STRAY:
        vm.set_account(STRAY, Account(10**9, b'', SYSTEM))
    watched = list(accounts) + [PAYER.pubkey()]
    before = {k: vm.get_account(k) for k in watched}
    tx = Transaction.new_signed_with_payer([Instruction(AMM, data, metas)], PAYER.pubkey(), [PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = [base64.b64decode(l[len('Program data: '):]) for l in meta.logs() if l.startswith('Program data: ')]
    after = {k: vm.get_account(k) for k in watched}
    unchanged = all(
        (after[k].lamports, after[k].owner, after[k].executable, after[k].rent_epoch)
        == (before[k].lamports, before[k].owner, before[k].executable, before[k].rent_epoch)
        and (not failed and k == pool_key or bytes(after[k].data) == bytes(before[k].data))
        for k in watched if k != PAYER.pubkey())
    if failed:
        text = str(result.err())
        custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
        error = int(custom.group(1)) if custom else re.search(r'Fieldless\((\w+)\)', text).group(1)
        return {'error': error, 'events': events, 'unchanged': unchanged}
    cpi = [bytes(ix.instruction().data) for group in meta.inner_instructions() for ix in group]
    return {'error': None, 'events': events, 'cpi': cpi, 'pool': bytes(after[pool_key].data),
            'unchanged': unchanged}


def fixed_cases():
    cases = [{}, {'trailing': 'ffeeddccbbaa'}, {'count': 5}]
    cases += [{'payload': n} for n in range(8)]
    cases += [{'count': n} for n in range(4)]
    # Who the sharing config's admin and the pool's coin creator are; equal is all that counts.
    for creator, admin in [(ADMIN, OTHER), (OTHER, ADMIN), (SYSTEM, SYSTEM), (SYSTEM, ADMIN), (OTHER, OTHER),
                           (STRAY, STRAY), (ADMIN, SYSTEM)]:
        cases.append({'coin_creator': creator, 'sharing_admin': admin})
    cases += [{'sharing_mint': m} for m in (SYSTEM, OTHER, QUOTE_MINT)]
    cases += [{'version': n} for n in (0, 1, 3, 255)]
    cases += [{'status': n} for n in (0, 2, 255)] + [{'revoked': n} for n in (1, 2, 255)]
    cases += [{'holders': []}, {'holders': [(OTHER, 1), (ADMIN, 9_999)]}, {'holders': [(SYSTEM, 65_535)] * 10},
              {'sharing_patches': [(76, b'\xff\xff\xff\xff')]}, {'sharing_patches': [(76, b'\x02\0\0\0')]},
              {'sharing_patches': [(8, b'\0')]}, {'sharing_patches': [(0, b'\0')]}, {'sharing_pad': 1024}]
    cases += [{'sharing_length': n} for n in (0, 1, 7, 8, 10, 11, 42, 43, 75, 76, 79, 80, 113)]
    cases += [{'holders': [], 'sharing_length': n} for n in (79, 80)]
    # Pool layout: what is read, what is zero-filled, what is written back.
    cases += [{'pool_length': n} for n in (0, 7, 8, 100, 210, 211, 212, 242, 243, 244, 269, 270, 271, 279, 286, 287, 288)]
    cases += [{'pool_length': 211, 'sharing_admin': SYSTEM}, {'pool_length': 230, 'sharing_admin': SYSTEM},
              {'pool_length': 250, 'sharing_mint': OTHER}, {'pool_length': 270, 'pool_patches': [(270, b'\x01')]}]
    cases += [{'pool_patches': [(at, bytes([v]))]} for at in (243, 244, 269, 270) for v in (0, 1, 2, 255)]
    cases += [{'pool_patches': [(279, struct.pack('<Q', v))]} for v in (1, 2**64 - 1)]
    cases += [{'pool_patches': [(at, b'\xff' * 8)]} for at in (203, 245, 261, 271)]
    cases += [{'pool_patches': [(8, b'\0')]}, {'pool_patches': [(0, b'\0')]}, {'index': 1}, {'index': 65_535}]
    cases += [{'pool_patches': [(at, bytes(32))]} for at in (11, 43, 75, 107, 139, 171)]
    # Owners and addresses.
    for owner in (SYSTEM, FEES, PUMP):
        cases += [{'pool_owner': owner}]
    for owner in (SYSTEM, AMM, PUMP):
        cases += [{'sharing_owner': owner}]
    cases += [{'readonly': True}, {'pool_key': STRAY}, {'sharing_key': STRAY_SHARING}, {'event_key': STRAY},
              {'event_key': AMM}, {'program_key': STRAY}]
    # The pool must be one a Pump curve migrated into: creator is Pump's pool authority of the base mint.
    nc = (11, bytes(OTHER))
    cases += [{'pool_patches': [nc]}, {'pool_patches': [nc], 'readonly': True}, {'pool_patches': [nc], 'pool_key': STRAY},
              {'pool_patches': [nc], 'sharing_key': STRAY_SHARING}, {'pool_patches': [nc], 'sharing_mint': OTHER},
              {'pool_patches': [nc], 'sharing_admin': OTHER}, {'pool_patches': [nc], 'event_key': STRAY},
              {'pool_patches': [nc, (270, b'\x01')]}, {'pool_patches': [nc], 'sharing_owner': SYSTEM},
              {'pool_patches': [(11, bytes(Pubkey.find_program_address([b'pool-authority', bytes(OTHER)], PUMP)[0]))]},
              {'pool_patches': [(43, bytes(OTHER))], 'sharing_mint': OTHER},
              {'pool_patches': [(11, bytes(Pubkey.find_program_address([b'pool-authority', bytes(OTHER)], PUMP)[0])),
                                (43, bytes(OTHER))], 'sharing_mint': OTHER}]
    # A meta that is missing fails when its account is loaded.
    cases += [{'count': 1, 'pool_owner': SYSTEM}, {'count': 1, 'pool_length': 100}, {'count': 2, 'sharing_owner': SYSTEM},
              {'count': 3, 'status': 2}, {'count': 3, 'readonly': True}, {'count': 3, 'sharing_admin': OTHER},
              {'count': 0, 'payload': 3}]
    # A pool field cut short reads as zero, so the old creator can be the zero key.
    cases += [{'pool_length': n, 'sharing_admin': SYSTEM} for n in (212, 230, 242)]
    cases += [{'pool_length': n, 'sharing_admin': SYSTEM, 'pool_patches': [(270, b'\x02')]} for n in (230, 271)]
    cases += [{'pool_length': 285, 'pool_patches': [(279, b'\xff' * 8)]}, {'count': 1}, {'count': 1, 'sharing_owner': SYSTEM}, {'count': 2}]
    # Every byte of the unswept-fee counter counts, and bytes past the pool are left alone.
    cases += [{'pool_patches': [(286, b'\x01')]}, {'pool_patches': [(287, b'\xab' * 13)]}]
    # Handler order: mint, creator, event authority, holder reward, unswept fees.
    holder, unswept = (270, b'\x01'), (279, b'\x01')
    cases += [{'sharing_mint': OTHER, 'sharing_admin': OTHER}, {'sharing_mint': OTHER, 'pool_patches': [holder]},
              {'sharing_admin': OTHER, 'pool_patches': [holder]}, {'sharing_admin': OTHER, 'pool_patches': [unswept]},
              {'pool_patches': [holder, unswept]}, {'sharing_mint': OTHER, 'pool_patches': [unswept]}]
    # Loading before constraints, constraints before the handler.
    cases += [{'pool_owner': SYSTEM, 'pool_patches': [(0, b'\0')]}, {'pool_patches': [(0, b'\0')], 'sharing_owner': SYSTEM},
              {'pool_patches': [(243, b'\x02')], 'sharing_owner': SYSTEM}, {'pool_patches': [(243, b'\x02')], 'readonly': True},
              {'sharing_owner': SYSTEM, 'pool_key': STRAY}, {'status': 2, 'pool_key': STRAY},
              {'readonly': True, 'pool_key': STRAY}, {'readonly': True, 'sharing_key': STRAY_SHARING},
              {'readonly': True, 'event_key': STRAY}, {'pool_key': STRAY, 'sharing_mint': OTHER},
              {'sharing_key': STRAY_SHARING, 'sharing_admin': OTHER}, {'event_key': STRAY, 'pool_patches': [holder]},
              {'program_key': STRAY, 'pool_length': 250}, {'program_key': STRAY, 'sharing_admin': OTHER},
              {'pool_length': 250, 'pool_patches': [unswept]}, {'payload': 3, 'count': 2}, {'count': 2, 'pool_owner': SYSTEM}]
    return cases


def random_cases():
    rng = random.Random(20261030)
    keys = [ADMIN, OTHER, SYSTEM, STRAY]
    cases = []
    for _ in range(150):
        c = {'coin_creator': rng.choice(keys), 'sharing_admin': rng.choice(keys)}
        if rng.random() < 0.2:
            c['sharing_mint'] = rng.choice([BASE_MINT, OTHER])
        patches = [(at, bytes([rng.choice([0, 0, 1, 2])])) for at in (243, 244, 269, 270) if rng.random() < 0.3]
        if rng.random() < 0.3:
            patches.append((279, struct.pack('<Q', rng.choice([0, 1, rng.randint(0, 2**64 - 1)]))))
        if patches:
            c['pool_patches'] = patches
        if rng.random() < 0.2:
            c['pool_length'] = rng.choice([rng.randint(200, 300), 287, 300])
        if rng.random() < 0.15:
            c['status'] = rng.choice([0, 1, 2])
        if rng.random() < 0.15:
            c['revoked'] = rng.choice([0, 1, 2])
        if rng.random() < 0.2:
            c['holders'] = [(rng.choice(keys), rng.randint(0, 65_535)) for _ in range(rng.randint(0, 4))]
        if rng.random() < 0.1:
            c['sharing_length'] = rng.randint(0, 120)
        if rng.random() < 0.08:
            c['readonly'] = True
        if rng.random() < 0.08:
            name = rng.choice(['pool_key', 'sharing_key', 'event_key', 'program_key'])
            c[name] = STRAY_SHARING if name == 'sharing_key' else STRAY
        if rng.random() < 0.05:
            c[rng.choice(['pool_owner', 'sharing_owner'])] = rng.choice([SYSTEM, PUMP])
        cases.append(c)
    return cases


class PumpAmmMigratePoolCoinCreatorCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if hashlib.sha256(AMM_ELF.read_bytes()).hexdigest() != AMM_SHA256:
            raise ValueError('captured AMM hash mismatch')
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'migrate-pool-coin-creator-host'
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
            return
        if answer.startswith('event-then:'):
            name, event = answer[11:].split(',')
            self.assertEqual(captured['error'], name)
            self.assertEqual(captured['events'], [bytes.fromhex(event)])
            return
        _, pool, event = answer.split(',')
        self.assertIsNone(captured['error'])
        self.assertEqual(captured['pool'], bytes.fromhex(pool))
        self.assertTrue(captured['unchanged'])
        self.assertEqual(captured['events'], [bytes.fromhex(event)])
        self.assertEqual(captured['cpi'], [EVENT_CPI_TAG + bytes.fromhex(event)])

    def run_cases(self, cases):
        for c, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=repr(c), host=answer[:80]):
                self.assert_matches(answer, run_captured(c))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_extra_account_case_really_supplies_a_fifth_meta(self):
        case = {'count': 5}
        self.assertEqual(len(setup(case)[3]), 5)
        self.assert_matches(self.host_answers([case])[0], run_captured(case))

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: each passing captured run must fail once the error,
        # a pool byte or an event byte moves.
        samples = ({}, {'sharing_admin': OTHER}, {'pool_length': 250}, {'program_key': STRAY}, {'pool_length': 100},
                   {'pool_patches': [(243, b'\x02')]})
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured)
            with self.assertRaises(AssertionError):
                self.assert_matches(answer, dict(captured, unchanged=False))
            if answer.startswith('ok,'):
                _, pool, event = answer.split(',')
                flip = lambda h, i: h[:2 * i] + format(int(h[2 * i:2 * i + 2], 16) ^ 1, '02x') + h[2 * i + 2:]
                tampered = ['ok,' + flip(pool, 211) + ',' + event, 'ok,' + flip(pool, 290) + ',' + event,
                            'ok,' + pool + ',' + flip(event, 8), 'ok,' + pool + ',' + flip(event, 175), 'error:6046']
            elif answer.startswith('event-then:'):
                name, event = answer[11:].split(',')
                tampered = ['event-then:' + name + ',' + event[:-2] + '00', 'error:' + name,
                            'event-then:' + ('BorshIoError' if name == 'MissingAccount' else 'MissingAccount') + ',' + event]
            else:
                tampered = ['error:6081', 'error:BorshIoError' if answer != 'error:BorshIoError' else 'error:3003']
            for text in tampered:
                with self.subTest(case=repr(c), tampered=text[:60]):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a for a in answers if a.startswith('error:')}, {
            'error:101', 'error:2000', 'error:2006', 'error:6028', 'error:3001', 'error:3002', 'error:3003', 'error:3005',
            'error:3007', 'error:6045', 'error:6046', 'error:6074', 'error:6081', 'error:InvalidAccountData',
            'error:BorshIoError'})
        self.assertEqual({a.split(',')[0] for a in answers if a.startswith('event-then:')},
                         {'event-then:MissingAccount', 'event-then:BorshIoError'})
        self.assertGreater(sum(a.startswith('ok,') for a in answers), 20)


if __name__ == '__main__':
    unittest.main()
