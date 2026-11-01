"""Captured-program checks for PumpSwap `set_coin_creator`.

Each case builds a synthetic pool, Metaplex metadata account, Pump bonding
curve and instruction, runs it on `evidence/original/pump_amm/deployed.so` in
LiteSVM, and feeds the same bytes to
`programs/pump-amm/recovered/set_coin_creator_host.rs`. The host gets the raw
account bytes; owners and PDA matches are worked out here from the accounts
actually loaded. The host also receives a target-calibrated metadata heap
budget for this fixture's account layout. That budget is a context assumption,
not an account-count-only law or proof for arbitrary transactions. The error (custom code or runtime error), the committed pool
bytes, the logged event and the same bytes in the `emit_cpi!` self-call must
agree, and nothing else may move. This is matching behaviour on these inputs only, not a
byte-identity claim. `scripts/pump_amm_creator_reassignment_differential.py`
compares candidate builds with the captured program; this test pins the
captured outcomes to a model instead and does not read `research/`.
"""
from pathlib import Path
from unittest import mock
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
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/set_coin_creator_host.rs'

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.default()
DISCRIMINATOR = bytes([210, 149, 128, 45, 188, 58, 78, 175])
METAPLEX = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
POOL_DISC = hashlib.sha256(b'account:Pool').digest()[:8]
CURVE_DISC = hashlib.sha256(b'account:BondingCurve').digest()[:8]
METAPLEX_EVENT_DISC = hashlib.sha256(b'event:SetMetaplexCoinCreatorEvent').digest()[:8]
CURVE_EVENT_DISC = hashlib.sha256(b'event:SetBondingCurveCoinCreatorEvent').digest()[:8]
# Anchor's EVENT_IX_TAG, the u64 0x1d9acb512ea545e4 in little-endian order.
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
PAYER = Keypair.from_seed(bytes([231]) * 32)
FIRST = Keypair.from_seed(bytes([232]) * 32).pubkey()
OTHER = Keypair.from_seed(bytes([233]) * 32).pubkey()
BASE_MINT = Keypair.from_seed(bytes([234]) * 32).pubkey()
CURVE_CREATOR = Keypair.from_seed(bytes([235]) * 32).pubkey()
QUOTE_MINT = Pubkey.from_string('So11111111111111111111111111111111111111112')
POOL_CREATOR = Pubkey.find_program_address([b'pool-authority', bytes(BASE_MINT)], PUMP)[0]
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
STRAY_METADATA = Pubkey.from_bytes(bytes([78]) * 32)
STRAY_CURVE = Pubkey.from_bytes(bytes([79]) * 32)
NOW = 1_761_800_000
ACCOUNTS = ('pool', 'metadata', 'bonding_curve', 'event_authority', 'program')

# Calibrated once using declared-name allocation thresholds. Counts <=5 use
# prefixes of ACCOUNTS; higher counts append duplicate PAYER metas. Distinct
# additional account keys are a different context and require new calibration.
# Subsequent string and near-boundary controls validate the admitted budgets.
FIXTURE_METADATA_HEAP = {0: 0, 1: 0, 2: 31766, 3: 31646, 4: 31526, 5: 31406,
                         6: 31286, 7: 31238, 8: 31190, 9: 31142, 10: 31094,
                         11: 31046, 12: 30998}


def metadata_address(mint):
    return Pubkey.find_program_address([b'metadata', bytes(METAPLEX), mint], METAPLEX)[0]


def curve_address(mint):
    return Pubkey.find_program_address([b'bonding-curve', mint], PUMP)[0]


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
    data[211:243] = bytes(c.get('coin_creator', SYSTEM))
    data[245:261] = (12_345).to_bytes(16, 'little', signed=True)
    data[261:269] = struct.pack('<Q', 30)
    data[269] = 1
    data[271:279] = struct.pack('<Q', 55)
    data[279:287] = struct.pack('<Q', 7)
    for at, value in c.get('pool_patches', ()):
        data[at:at + len(value)] = value
    if 'pool_length' in c:
        data = data[:c['pool_length']]
    return bytes(data)


def borsh_string(s):
    return struct.pack('<I', len(s)) + s


def metadata_bytes(c):
    creators = c.get('creators', [(FIRST, 1, 100)])
    data = bytearray(bytes([c.get('key', 4)]) + bytes(OTHER) + bytes(c.get('metadata_mint', BASE_MINT))
                     + borsh_string(c.get('name', b'Coin')) + borsh_string(c.get('symbol', b'C'))
                     + borsh_string(c.get('uri', b'https://x'))
                     + struct.pack('<H', 0))
    if creators is None:
        data += b'\0'
    else:
        data += b'\1' + struct.pack('<I', len(creators)) + b''.join(bytes(k) + bytes([v, s]) for k, v, s in creators)
    data += c.get('metadata_tail', bytes([0, 1, 1, 254, 1, 2, 0, 0, 0, 0]))
    data = data.ljust(c.get('metadata_pad', 679), b'\0')
    for at, value in c.get('metadata_patches', ()):
        data[at:at + len(value)] = value
    if 'metadata_length' in c:
        data = data[:c['metadata_length']]
    return bytes(data)


def curve_bytes(c):
    data = bytearray(CURVE_DISC + struct.pack('<QQQQQ', 1, 2, 3, 4, 5) + bytes([c.get('complete', 1)])
                     + bytes(c.get('curve_creator', CURVE_CREATOR)) + bytes([0, 0]))
    data = data.ljust(c.get('curve_pad', 151), b'\0')
    for at, value in c.get('curve_patches', ()):
        data[at:at + len(value)] = value
    if 'curve_length' in c:
        data = data[:c['curve_length']]
    return bytes(data)


def setup(c):
    pool = pool_bytes(c)
    pool_key = c.get('pool_key', pool_address(pool_bytes({k: v for k, v in c.items() if k != 'pool_length'})))
    seed_mint = bytes(pool).ljust(75, b'\0')[43:75]
    metadata_key = c.get('metadata_key', metadata_address(seed_mint))
    curve_key = c.get('curve_key', curve_address(seed_mint))
    keys = {'pool': pool_key, 'metadata': metadata_key, 'bonding_curve': curve_key,
            'event_authority': c.get('event_key', EVENT_AUTHORITY), 'program': c.get('program_key', AMM)}
    accounts = {pool_key: Account(10**9, pool, c.get('pool_owner', AMM)),
                metadata_key: Account(10**9, metadata_bytes(c), c.get('metadata_owner', METAPLEX)),
                curve_key: Account(10**9, curve_bytes(c), c.get('curve_owner', PUMP))}
    metas = [AccountMeta(keys[n], False, n == 'pool' and not c.get('readonly')) for n in ACCOUNTS]
    count = c.get('count', 5)
    if count > len(metas):
        metas.extend(AccountMeta(PAYER.pubkey(), False, False) for _ in range(count - len(metas)))
    metas = metas[:count]
    data = (DISCRIMINATOR + bytes.fromhex(c.get('trailing', '')))[:c.get('payload', 8 + len(c.get('trailing', '')) // 2)]
    return keys, accounts, metas, data


def run_captured(c):
    keys, accounts, metas, data = setup(c)
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
    # An unsigned transaction yields no results and `not all([])` is false, so
    # this check passed for a fixture the VM had no signature to accept.
    if not (tx.signatures and all(tx.verify_with_results())):
        raise ValueError('fixture transaction signature verification failed')
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = [base64.b64decode(l[len('Program data: '):]) for l in meta.logs() if l.startswith('Program data: ')]
    after = {k: vm.get_account(k) for k in watched}
    pool_key = keys['pool']
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
    pool_key = keys['pool']
    return {'error': None, 'events': events, 'cpi': cpi, 'pool': bytes(after[pool_key].data),
            'unchanged': unchanged}


def host_line(c):
    keys, accounts, metas, data = setup(c)
    pool_data = bytes(accounts[keys['pool']].data)
    by_name = dict(zip(ACCOUNTS, metas))
    seed_mint = pool_data.ljust(75, b'\0')[43:75]
    flags = [
        accounts[keys['pool']].owner == AMM,
        'pool' in by_name and by_name['pool'].is_writable,
        pool_data.ljust(75, b'\0')[11:43] == bytes(Pubkey.find_program_address([b'pool-authority', seed_mint], PUMP)[0]),
        accounts[keys['metadata']].owner == METAPLEX,
        keys['metadata'] == metadata_address(seed_mint),
        accounts[keys['bonding_curve']].owner == PUMP,
        keys['bonding_curve'] == curve_address(seed_mint),
        'event_authority' in by_name and by_name['event_authority'].pubkey == EVENT_AUTHORITY,
        'program' in by_name and by_name['program'].pubkey == AMM,
    ]
    return ','.join([str(len(data)), str(len(metas)), ''.join('1' if f else '0' for f in flags), pool_data.hex(),
                     bytes(accounts[keys['metadata']].data).hex(), bytes(accounts[keys['bonding_curve']].data).hex(),
                     bytes(keys['pool']).hex(), bytes(keys['metadata']).hex(), bytes(keys['bonding_curve']).hex(),
                     str(NOW), str(FIXTURE_METADATA_HEAP[len(metas)])])


def name_length(n):
    """Overwrite the metadata name's declared length."""
    return {'metadata_patches': [(65, struct.pack('<I', n))]}


def fixed_cases():
    nc = (11, bytes(OTHER))
    other_authority = bytes(Pubkey.find_program_address([b'pool-authority', bytes(OTHER)], PUMP)[0])
    cases = [{}, {'trailing': 'ffeeddccbbaa'}, {'count': 6}, {'creators': None}]
    cases += [{'payload': n} for n in range(8)] + [{'count': n} for n in range(5)]
    # Lazy loading: a missing meta fails when its account is reached.
    cases += [{'count': 1, 'pool_owner': SYSTEM}, {'count': 1, 'metadata_owner': SYSTEM}, {'count': 2, 'key': 0},
              {'count': 2, 'curve_owner': SYSTEM}, {'count': 3, 'curve_patches': [(0, b'\0')]},
              {'count': 3, 'readonly': True}, {'count': 4, 'readonly': True}, {'count': 4, 'coin_creator': OTHER},
              {'count': 0, 'payload': 3}, {'count': 1, 'pool_patches': [nc]}]
    # Who becomes the coin creator.
    cases += [{'creators': [(OTHER, 0, 1), (FIRST, 1, 99), (SYSTEM, 0, 0)]}, {'creators': [(SYSTEM, 0, 100)]},
              {'creators': [(FIRST, 0, 0)]}, {'creators': [(FIRST, 1, 255)]}, {'creators': [(CURVE_CREATOR, 1, 100)]},
              {'creators': []}, {'creators': [(FIRST, 2, 100)]}, {'creators': [(FIRST, 255, 100)]},
              {'creators': [(OTHER, 1, 50)] * 17}, {'creators': None, 'curve_creator': SYSTEM},
              {'creators': None, 'curve_creator': OTHER}, {'creators': None, 'complete': 0},
              {'creators': [], 'coin_creator': OTHER}, {'creators': [], 'pool_patches': [nc]}]
    cases += [{'metadata_patches': [(94, struct.pack('<I', n))]} for n in (2, 17, 18, 1000, 2**32 - 1)]
    cases += [{'metadata_patches': [(93, bytes([v]))]} for v in (2, 255)]
    # Already set: nothing changes and nothing is logged, but the pool is still written back.
    cases += [{'coin_creator': k} for k in (OTHER, FIRST, CURVE_CREATOR, STRAY)]
    cases += [{'coin_creator': OTHER, 'program_key': STRAY}, {'coin_creator': OTHER, 'creators': None},
              {'coin_creator': OTHER, 'pool_length': 250}, {'coin_creator': OTHER, 'pool_length': 286},
              {'coin_creator': OTHER, 'pool_length': 287}, {'coin_creator': OTHER, 'metadata_patches': [(0, b'\0')]},
              {'coin_creator': OTHER, 'readonly': True}, {'coin_creator': OTHER, 'event_key': STRAY},
              {'pool_patches': [(242, b'\x01')]}, {'pool_patches': [(211, b'\x01')]}]
    # Metadata layout: key, strings, creators, then two bools and the edition nonce; the rest is lenient.
    cases += [{'key': k} for k in (0, 1, 3, 5, 6, 12, 255)]
    cases += [{'metadata_pad': 0, 'metadata_length': n} for n in (0, 1, 33, 65, 69, 93, 98, 131, 132, 133, 135, 136, 137, 142)]
    cases += [{'metadata_pad': 0, 'metadata_length': n, 'metadata_tail': bytes([0, 1, 0])} for n in (134, 135)]
    cases += [{'metadata_pad': 0, 'creators': None, 'metadata_tail': bytes([0, 1, 0]), 'metadata_length': n} for n in (95, 96, 97)]
    tail = [0, 1, 1, 254, 1, 2, 0, 0, 0, 0]
    for at, value in [(0, 2), (0, 1), (1, 2), (1, 0), (2, 2), (2, 255), (2, 0), (4, 2), (4, 255), (5, 9), (6, 2),
                      (7, 2), (8, 2), (9, 2), (6, 1), (8, 1)]:
        t = list(tail)
        t[at] = value
        cases += [{'metadata_tail': bytes(t)}, {'metadata_tail': bytes(t), 'metadata_pad': 0}]
    cases += [{'name': b''}, {'name': b'a' * 300}, {'symbol': b''}, {'uri': b''}, {'uri': 'é'.encode()},
              {'name': b'\xff\xfe'}, {'symbol': b'\xc3'}, {'uri': b'\xc3('}, {'name': b'\x00'}]
    cases += [name_length(n) for n in (5, 100, 4_000, 31_406, 31_407, 40_000, 2**32 - 1)]
    cases += [{'metadata_patches': [(73, struct.pack('<I', n))]} for n in (31_402, 31_403)]
    cases += [{'metadata_patches': [(78, struct.pack('<I', n))]} for n in (31_401, 31_402)]
    cases += [{'name': b'a' * 200, 'metadata_patches': [(73 + 196, struct.pack('<I', n))]} for n in (31_206, 31_207)]
    cases += [{'metadata_mint': OTHER}, {'metadata_patches': [(1, bytes(32))]}, {'metadata_patches': [(91, b'\xff\xff')]}]
    # Bonding curve layout.
    cases += [{'curve_pad': 0, 'curve_length': n} for n in (0, 7, 8, 48, 49, 81, 82, 83)]
    cases += [{'curve_pad': 0, 'curve_length': n, 'creators': None} for n in (82, 83)]
    cases += [{'curve_patches': [(at, bytes([v]))]} for at in (48, 81, 82) for v in (1, 2)]
    cases += [{'curve_patches': [(0, b'\0')]}, {'curve_patches': [(8, b'\xff' * 40)]}]
    # Pool layout.
    cases += [{'pool_length': n} for n in (0, 7, 8, 100, 210, 211, 212, 230, 242, 243, 244, 270, 279, 286, 287, 288)]
    cases += [{'pool_length': n, 'creators': None} for n in (211, 250)]
    cases += [{'pool_patches': [(at, bytes([v]))]} for at in (243, 244, 269, 270) for v in (0, 1, 2, 255)]
    cases += [{'pool_length': 243, 'pool_patches': [(243, b'\x02')]}, {'pool_length': 244, 'pool_patches': [(243, b'\x02')]}]
    cases += [{'pool_patches': [(8, b'\0')]}, {'pool_patches': [(0, b'\0')]}, {'index': 1}, {'index': 65_535},
              {'pool_patches': [(287, b'\xab' * 13)]}, {'pool_patches': [(279, b'\xff' * 8)]}]
    cases += [{'pool_patches': [(at, bytes(32))]} for at in (75, 107, 139, 171)]
    # Canonical pools only.
    cases += [{'pool_patches': [nc]}, {'pool_patches': [(11, bytes(32))]}, {'pool_patches': [(43, bytes(OTHER))]},
              {'pool_patches': [(11, other_authority)]}, {'pool_patches': [(11, other_authority), (43, bytes(OTHER))]},
              {'pool_patches': [(11, other_authority), (43, bytes(OTHER))], 'metadata_key': metadata_address(bytes(OTHER)),
               'curve_key': curve_address(bytes(OTHER))},
              {'pool_patches': [nc], 'coin_creator': OTHER}, {'pool_patches': [nc], 'creators': None}]
    # Owners and addresses.
    cases += [{'pool_owner': o} for o in (SYSTEM, FEES, PUMP)] + [{'metadata_owner': o} for o in (SYSTEM, AMM, PUMP)]
    cases += [{'curve_owner': o} for o in (SYSTEM, AMM, METAPLEX)]
    cases += [{'readonly': True}, {'pool_key': STRAY}, {'metadata_key': STRAY_METADATA}, {'curve_key': STRAY_CURVE},
              {'event_key': STRAY}, {'event_key': AMM}, {'program_key': STRAY}, {'program_key': STRAY, 'creators': None},
              {'program_key': STRAY, 'pool_length': 250}, {'pool_key': STRAY, 'creators': None}]
    # Loading before constraints, constraints before the handler.
    cases += [{'readonly': True, 'metadata_owner': SYSTEM}, {'readonly': True, 'key': 0}, {'readonly': True, 'curve_owner': SYSTEM},
              {'readonly': True, 'curve_patches': [(0, b'\0')]}, {'readonly': True, 'metadata_key': STRAY_METADATA},
              {'readonly': True, 'pool_patches': [nc]}, {'metadata_key': STRAY_METADATA, 'pool_patches': [nc]},
              {'curve_key': STRAY_CURVE, 'pool_patches': [nc]}, {'event_key': STRAY, 'pool_patches': [nc]},
              {'event_key': STRAY, 'creators': []}, {'event_key': STRAY, 'coin_creator': OTHER},
              {'pool_patches': [(0, b'\0')], 'metadata_owner': SYSTEM}, {'pool_patches': [(243, b'\x02')], 'metadata_owner': SYSTEM},
              {'key': 0, 'curve_owner': SYSTEM}, {'metadata_owner': SYSTEM, 'curve_owner': SYSTEM},
              {'pool_owner': SYSTEM, 'pool_patches': [(0, b'\0')]}, {'key': 0, 'curve_patches': [(0, b'\0')]},
              {'creators': [], 'program_key': STRAY}, {'creators': [], 'pool_length': 250}]
    return cases


def random_cases():
    rng = random.Random(20261030)
    keys = [FIRST, OTHER, SYSTEM, CURVE_CREATOR]
    cases = []
    for _ in range(150):
        c = {}
        roll = rng.random()
        if roll < 0.3:
            c['creators'] = None
        elif roll < 0.9:
            c['creators'] = [(rng.choice(keys), 2 if rng.random() < 0.03 else rng.choice([0, 1]), rng.randint(0, 255))
                             for _ in range(rng.choice([0, 1, 1, 2, 3, 17]))]
        if rng.random() < 0.3:
            c['coin_creator'] = rng.choice(keys)
        if rng.random() < 0.3:
            c['curve_creator'] = rng.choice(keys)
        if rng.random() < 0.25:
            t = [0, 1, 1, 254, 1, 2, 0, 0, 0, 0]
            t[rng.randrange(10)] = rng.choice([0, 1, 1, 2])
            c['metadata_tail'] = bytes(t)
        if rng.random() < 0.2:
            c['metadata_pad'] = rng.choice([0, 200, 679])
        if rng.random() < 0.1:
            c['metadata_length'] = rng.randint(120, 160)
            c.setdefault('metadata_pad', 0)
        if rng.random() < 0.15:
            c['name'] = rng.choice(['ok', 'é', 'Pump']).encode() * rng.randint(0, 20) + (b'\xc3' if rng.random() < 0.2 else b'')
        patches = [(at, bytes([rng.choice([0, 0, 1, 1, 1, 2])])) for at in (243, 244, 269, 270) if rng.random() < 0.15]
        if rng.random() < 0.1:
            patches.append((11, bytes(OTHER)))
        if patches:
            c['pool_patches'] = patches
        if rng.random() < 0.15:
            c['pool_length'] = rng.choice([rng.randint(200, 300), 287, 300])
        if rng.random() < 0.1:
            c['curve_patches'] = [(rng.choice([48, 81, 82]), bytes([rng.choice([1, 2])]))]
        if rng.random() < 0.06:
            c['curve_length'] = rng.randint(0, 90)
            c['curve_pad'] = 0
        if rng.random() < 0.06:
            c['readonly'] = True
        if rng.random() < 0.08:
            name = rng.choice(['metadata_key', 'curve_key', 'event_key', 'program_key', 'pool_key'])
            c[name] = {'metadata_key': STRAY_METADATA, 'curve_key': STRAY_CURVE}.get(name, STRAY)
        if rng.random() < 0.05:
            c[rng.choice(['pool_owner', 'metadata_owner', 'curve_owner'])] = rng.choice([SYSTEM, AMM, PUMP])
        if rng.random() < 0.05:
            c['count'] = rng.randint(0, 4)
        cases.append(c)
    return cases


class PumpAmmSetCoinCreatorCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if hashlib.sha256(AMM_ELF.read_bytes()).hexdigest() != AMM_SHA256:
            raise ValueError('captured AMM hash mismatch')
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'set-coin-creator-host'
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
        self.assertIsNone(captured['error'])
        self.assertTrue(captured['unchanged'])
        if answer.startswith('unchanged,'):
            self.assertEqual(captured['pool'], bytes.fromhex(answer[10:]))
            self.assertEqual(captured['events'], [])
            self.assertEqual(captured['cpi'], [])
            return
        _, pool, event = answer.split(',')
        self.assertEqual(captured['pool'], bytes.fromhex(pool))
        self.assertEqual(captured['events'], [bytes.fromhex(event)])
        self.assertEqual(captured['cpi'], [EVENT_CPI_TAG + bytes.fromhex(event)])

    def run_cases(self, cases):
        for c, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=repr(c)[:300], host=answer[:80]):
                self.assert_matches(answer, run_captured(c))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_extra_account_case_supplies_a_sixth_meta(self):
        case = {'count': 6}
        self.assertEqual(len(setup(case)[2]), 6)
        self.assert_matches(self.host_answers([case])[0], run_captured(case))

    def test_calibrated_heap_contexts_and_unseen_string_boundaries(self):
        cases = []
        for count in range(2, 13):
            budget = FIXTURE_METADATA_HEAP[count]
            for delta in (-2, 2):
                cases.append(dict(name_length(budget + delta), count=count))
        # These independent controls consume real name/symbol allocations and
        # then test URI lengths that were not used in the name calibration.
        for count in (6, 8, 12):
            remaining = FIXTURE_METADATA_HEAP[count] - 31 - 11
            for delta in (-2, 2):
                cases.append({'count': count, 'name': b'a' * 31, 'symbol': b'b' * 11,
                              'metadata_patches': [(115, struct.pack('<I', remaining + delta))]})
        self.run_cases(cases)

    def test_captured_image_identity_is_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            wrong = Path(temporary) / 'wrong.so'
            wrong.write_bytes(AMM_ELF.read_bytes() + b'wrong capture')
            with mock.patch.dict(globals(), AMM_ELF=wrong):
                with self.assertRaisesRegex(ValueError, 'captured AMM hash mismatch'):
                    type(self).setUpClass()

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: each captured run must fail once the error, a pool
        # byte or an event byte moves.
        samples = ({}, {'creators': None}, {'coin_creator': OTHER}, {'pool_length': 250}, {'program_key': STRAY},
                   {'pool_length': 100}, {'creators': []}, {'key': 0})
        flip = lambda h, i: h[:2 * i] + format(int(h[2 * i:2 * i + 2], 16) ^ 1, '02x') + h[2 * i + 2:]
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured)
            with self.assertRaises(AssertionError):
                self.assert_matches(answer, dict(captured, unchanged=False))
            if answer.startswith('ok,'):
                _, pool, event = answer.split(',')
                tampered = ['ok,' + flip(pool, 211) + ',' + event, 'ok,' + flip(pool, 290) + ',' + event,
                            'ok,' + pool + ',' + flip(event, 0), 'ok,' + pool + ',' + flip(event, 143),
                            'unchanged,' + pool, 'error:6028']
            elif answer.startswith('unchanged,'):
                pool = answer[10:]
                tampered = ['unchanged,' + flip(pool, 211), 'unchanged,' + flip(pool, 299), 'error:BorshIoError']
            elif answer.startswith('event-then:'):
                name, event = answer[11:].split(',')
                tampered = ['event-then:' + name + ',' + flip(event, 143), 'error:' + name,
                            'event-then:' + ('BorshIoError' if name == 'MissingAccount' else 'MissingAccount') + ',' + event]
            else:
                tampered = ['error:6028', 'error:ProgramFailedToComplete' if answer != 'error:ProgramFailedToComplete'
                            else 'error:BorshIoError']
            for text in tampered:
                with self.subTest(case=repr(c), tampered=text[:60]):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a for a in answers if a.startswith('error:')}, {
            'error:101', 'error:2000', 'error:2006', 'error:3001', 'error:3002', 'error:3003', 'error:3005',
            'error:3007', 'error:6028', 'error:InvalidAccountData', 'error:BorshIoError',
            'error:ProgramFailedToComplete'})
        self.assertEqual({a.split(',')[0] for a in answers if a.startswith('event-then:')},
                         {'event-then:MissingAccount', 'event-then:BorshIoError'})
        events = {bytes.fromhex(a.split(',')[2])[:8] for a in answers if a.startswith('ok,')}
        self.assertEqual(events, {METAPLEX_EVENT_DISC, CURVE_EVENT_DISC})
        self.assertGreater(sum(a.startswith('unchanged,') for a in answers), 5)
        self.assertGreater(sum(a.startswith('ok,') for a in answers), 40)


if __name__ == '__main__':
    unittest.main()
