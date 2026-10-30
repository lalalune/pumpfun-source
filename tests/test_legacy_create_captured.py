"""Captured-program checks for the recovered legacy Pump `create`.

Every case runs Pump `create` from the captured
`evidence/original/pump/deployed.so` (upgradeable loader) on LiteSVM, with the
captured token-metadata program and LiteSVM's built-in SPL Token, ATA and
system programs, against a synthetic Global built from the IDL layout. The
same inputs go to `programs/pump/recovered/legacy_create_host.rs`, and the
error, the new bonding curve, the curve's token balance, the revoked mint
authority, and the CreateEvent must agree. This shows matching behavior on
these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
METADATA_ELF = ROOT / 'evidence/dependencies/token_metadata/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    METADATA_ELF: '31f0a627dba051a938de650464e55cc5397a4be0fd496929c1f9cf02fe5e9011',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/legacy_create_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
CREATE = next(i for i in IDL['instructions'] if i['name'] == 'create')
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
CREATE_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'CreateEvent'))
METADATA = Pubkey.from_string(next(a['address'] for a in CREATE['accounts'] if a['name'] == 'mpl_token_metadata'))
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
RENT = Pubkey.from_string('SysvarRent111111111111111111111111111111111')
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
SYSTEM = Pubkey.default()

USER = Keypair.from_seed(bytes([221]) * 32)
MINT = Keypair.from_seed(bytes([77]) * 32)
CREATOR = Pubkey.from_bytes(bytes([60]) * 32)
STRANGER = Pubkey.from_bytes(bytes([200]) * 32)
TS = 1_800_000_000
U64 = 2**64 - 1


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(seeds, program)[0]


GLOBAL = pda([b'global'])
CURVE = pda([b'bonding-curve', bytes(MINT.pubkey())])
CURVE_ATA = pda([bytes(CURVE), bytes(TOKEN), bytes(MINT.pubkey())], ATA)
ACCOUNTS = {
    'mint': MINT.pubkey(), 'mint_authority': pda([b'mint-authority']), 'bonding_curve': CURVE,
    'associated_bonding_curve': CURVE_ATA, 'global': GLOBAL, 'mpl_token_metadata': METADATA,
    'metadata': pda([b'metadata', bytes(METADATA), bytes(MINT.pubkey())], METADATA), 'user': USER.pubkey(),
    'system_program': SYSTEM, 'token_program': TOKEN, 'associated_token_program': ATA, 'rent': RENT,
    'event_authority': pda([b'__event_authority']), 'program': PUMP,
}
# Host fault letter -> account passed as a stranger (`U`, `B` change account state instead).
FAULTS = {'A': 'mint_authority', 'C': 'bonding_curve', 'G': 'global', 'M': 'metadata'}


def global_data(item):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 2 if 'B' in item['faults'] else item['initialized']
    struct.pack_into('<QQQQQ', data, 73, item['vtr'], item['vsr'], item['rtr'], item['supply'], 95)
    data[450] = 1
    return bytes(data)


DEFAULTS = dict(faults='', name='Coin', symbol='CN', uri='https://x', creator_zero=0, initialized=1,
                vtr=1_073_000_000_000_000, vsr=30_000_000_000, rtr=793_100_000_000_000, supply=10**15,
                prefund=())


def case(**changes):
    unknown = set(changes) - set(DEFAULTS)
    assert not unknown, unknown
    return dict(DEFAULTS, **changes)


def host_line(item):
    return ','.join(map(str, [item['faults'] or '-', len(item['name'].encode()), len(item['symbol'].encode()),
                              len(item['uri'].encode()), item['creator_zero'], item['vtr'], item['vsr'],
                              item['rtr'], item['supply']]))


def borsh_string(text):
    raw = text.encode()
    return struct.pack('<I', len(raw)) + raw


def run_captured(item):
    vm = LiteSVM().with_transaction_history(0)
    programdata = pda([bytes(PUMP)], UPGRADEABLE)
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + PUMP_ELF.read_bytes(),
                                        UPGRADEABLE, False))
    vm.set_account(PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    vm.add_program(METADATA, METADATA_ELF.read_bytes())
    vm.set_clock(Clock(1000, 0, 0, 0, TS))
    vm.set_account(GLOBAL, Account(10**9, global_data(item), PUMP))
    vm.set_account(USER.pubkey(), Account(10**12, b'', SYSTEM))
    if 'U' in item['faults']:
        vm.set_account(MINT.pubkey(), Account(10**7, bytes(82), TOKEN))
    for name in item['prefund']:   # system-owned, funded: `init` only tops up
        vm.set_account(ACCOUNTS[name], Account(10**7, b'', SYSTEM))
    wrong = {FAULTS[f] for f in item['faults'] if f in FAULTS}
    metas = [AccountMeta(STRANGER if a['name'] in wrong else ACCOUNTS[a['name']], a.get('signer', False),
                         a.get('writable', False)) for a in CREATE['accounts']]
    creator = SYSTEM if item['creator_zero'] else CREATOR
    data = (bytes(CREATE['discriminator']) + borsh_string(item['name']) + borsh_string(item['symbol'])
            + borsh_string(item['uri']) + bytes(creator))
    tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)],
                                           USER.pubkey(), [USER, MINT], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    curve, ata, mint = (vm.get_account(k) for k in (CURVE, CURVE_ATA, MINT.pubkey()))
    return {'error': str(result.err()) if failed else None,
            'events': [base64.b64decode(line[14:]) for line in meta.logs() if line.startswith('Program data: ')],
            'curve': bytes(curve.data) if curve is not None and curve.owner == PUMP else None,
            'ata': bytes(ata.data) if ata is not None and ata.owner == TOKEN else None,
            'mint': bytes(mint.data) if mint is not None and mint.owner == TOKEN else None}


def fixed_cases():
    cases = [case()]
    add = lambda **k: cases.append(case(**k))
    for f in 'UACGBM':
        add(faults=f)
    add(faults='UA')
    add(faults='AC')
    add(faults='CG')
    add(faults='GM')
    add(faults='AG')
    add(faults='UG')
    add(faults='BC')
    add(faults='AM')
    add(faults='M', creator_zero=1)
    add(faults='B', creator_zero=1)
    add(creator_zero=1)
    add(creator_zero=1, name='x' * 33, symbol='x' * 11, uri='x' * 201)
    # Metaplex limits are UTF-8 bytes, checked name, symbol, uri.
    add(name='x' * 32)
    add(name='x' * 33)
    add(name='é' * 16)
    add(name='é' * 16 + 'x')
    add(symbol='x' * 10)
    add(symbol='x' * 11)
    add(uri='x' * 200)
    add(uri='x' * 201)
    add(name='x' * 33, symbol='x' * 11)
    add(symbol='x' * 11, uri='x' * 201)
    add(name='', symbol='', uri='')
    # Global is copied as is: no initialized check, no reserve/supply checks.
    add(initialized=0)
    add(vtr=5, vsr=777, rtr=2 * 10**15, supply=123_456_789)
    add(vtr=0, vsr=0, rtr=0, supply=0)
    add(vtr=U64, vsr=U64, rtr=U64, supply=U64)
    add(supply=1)
    add(prefund=('mint',))
    add(prefund=('bonding_curve', 'associated_bonding_curve'))
    return cases


def random_cases(count=24, seed=621):
    rng = random.Random(seed)
    return [case(faults=rng.choice(['', '', '', 'A', 'M']), creator_zero=int(rng.random() < 0.15),
                 name='n' * rng.randrange(28, 36), symbol='s' * rng.randrange(7, 13), uri='u' * rng.randrange(190, 206),
                 vtr=rng.randrange(U64), vsr=rng.randrange(U64), rtr=rng.randrange(U64), supply=rng.randrange(U64))
            for _ in range(count)]


class LegacyCreateCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'legacy-create-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, item, answer, captured):
        if answer.startswith('error:'):
            self.assertIn(f'InstructionErrorCustom({answer[6:]})', str(captured['error']))
            self.assertEqual((captured['curve'], captured['events']), (None, []))
            return
        self.assertIsNone(captured['error'])
        vtr, vqr, rtr, supply, initial_vqr, minted = map(int, answer.split(',')[1:])
        curve = bytearray(166)
        curve[:8] = ACCOUNT_DISC['BondingCurve']
        struct.pack_into('<QQQQQ', curve, 8, vtr, vqr, rtr, 0, supply)
        curve[49:81] = bytes(CREATOR)
        struct.pack_into('<Q', curve, 142, initial_vqr)
        self.assertEqual(captured['curve'], bytes(curve))
        self.assertEqual(struct.unpack_from('<Q', captured['ata'], 64)[0], minted)
        # Supply minted, decimals 6, mint authority revoked (COption::None).
        self.assertEqual(captured['mint'][:4] + captured['mint'][36:45], bytes(4) + struct.pack('<QB', minted, 6))
        event = (CREATE_EVENT + borsh_string(item['name']) + borsh_string(item['symbol']) + borsh_string(item['uri'])
                 + bytes(MINT.pubkey()) + bytes(CURVE) + bytes(USER.pubkey()) + bytes(CREATOR)
                 + struct.pack('<qQQQQ', TS, vtr, vqr, rtr, supply) + bytes(TOKEN) + bytes(2) + bytes(32)
                 + struct.pack('<QQBB', vqr, 0, 0, 0))
        self.assertEqual(captured['events'], [event])

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

    def test_checker_rejects_swapped_reserves(self):
        # Negative control: a passing create must fail once the host swaps the two virtual reserves.
        item = case(vtr=5, vsr=777)
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(item, answer, captured)
        fields = answer.split(',')
        with self.assertRaises(AssertionError):
            self.assert_matches(item, ','.join([fields[0], fields[2], fields[1]] + fields[3:]), captured)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {'ok', 'error:0', 'error:11', 'error:12', 'error:13', 'error:2006', 'error:3003',
                                    'error:3012', 'error:6030'})


if __name__ == '__main__':
    unittest.main()
