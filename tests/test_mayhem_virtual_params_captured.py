"""Captured-program checks for Pump `set_mayhem_virtual_params`.

`sol_vault_authority` must be Mayhem's `["sol-vault"]` PDA and must sign, so
every case goes through `scripts/fixtures/signer_stub.so` deployed at the
Mayhem program id, which signs that PDA with `invoke_signed` and forwards the
eight accounts to the captured `evidence/original/pump/deployed.so` (the
unsigned cases call Pump directly). The captured Token-2022, SPL Token and
Associated Token programs from `evidence/dependencies/` are loaded too. The
same inputs go to `programs/pump/recovered/mayhem_virtual_params_host.rs`.
The error, the signed delta of `virtual_quote_reserves` (and that no other
curve byte, vault byte or lamport balance moves), the
`UpdateMayhemVirtualParamsEvent` bytes in the log and the same bytes in the
`emit_cpi!` self-call must agree. This is matching behaviour on these inputs
only, not a byte-identity claim. `scripts/pump_set_mayhem_virtual_params_differential.py`
and `scripts/pump_virtual_reserve_differential.py` compare candidate builds
with the captured program; this test pins the outcomes to a model instead and
does not read `research/`.
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
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN_2022_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
STUB_ELF = ROOT / 'scripts/fixtures/signer_stub.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN_2022_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/mayhem_virtual_params_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
INSTRUCTION = next(i for i in IDL['instructions'] if i['name'] == 'set_mayhem_virtual_params')
GLOBAL_DISC = next(bytes(a['discriminator']) for a in IDL['accounts'] if a['name'] == 'Global')
CURVE_DISC = next(bytes(a['discriminator']) for a in IDL['accounts'] if a['name'] == 'BondingCurve')
EVENT_DISC = next(bytes(e['discriminator']) for e in IDL['events'] if e['name'] == 'UpdateMayhemVirtualParamsEvent')
# Anchor's EVENT_IX_TAG, the u64 0x1d9acb512ea545e4 in little-endian order.
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
MAYHEM = Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN_2022 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
PAYER = Keypair.from_seed(bytes([211]) * 32)
MINT = Keypair.from_seed(bytes([212]) * 32).pubkey()
OTHER_MINT = Keypair.from_seed(bytes([213]) * 32).pubkey()
SOL_VAULT, SOL_VAULT_BUMP = Pubkey.find_program_address([b'sol-vault'], MAYHEM)
FAKE_VAULT_AUTHORITY, FAKE_BUMP = Pubkey.find_program_address([b'sol-vaulx'], MAYHEM)
GLOBAL = Pubkey.find_program_address([b'global'], PUMP)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
NOW = 1_700_000_123
# Global.initial_real_token_reserves: discriminator, initialized, authority, fee_recipient, two u64s.
IRTR_OFFSET = 8 + 1 + 32 + 32 + 8 + 8
FLAGS = ('global_ok', 'token_program_ok', 'signed', 'seeds_ok', 'vault_program_ok', 'vault_owner_ok',
         'vault_address_ok', 'curve_ok')
BASE = dict(vtr=10**15, vqr=3 * 10**10, rtr=8 * 10**14, rqr=5 * 10**9, supply=10**15, complete=False,
            mayhem=True, native=True, irtr=793_100_000_000_000, vault=0)


def ata(owner, mint, program):
    return Pubkey.find_program_address([bytes(owner), bytes(program), bytes(mint)], ATA_PROGRAM)[0]


def case(bad=(), **overrides):
    item = dict(BASE)
    item.update(overrides)
    item['flags'] = {name: name not in bad for name in FLAGS}
    return item


def host_line(item):
    flags = ''.join('1' if item['flags'][name] else '0' for name in FLAGS)
    return ','.join([flags] + [str(item[k]) for k in ('vtr', 'vqr', 'rtr', 'rqr', 'supply')]
                    + [str(int(item[k])) for k in ('complete', 'mayhem', 'native')]
                    + [str(item['irtr']), str(item['vault'])])


def curve_bytes(item):
    quote = bytes(32) if item['native'] else bytes(WSOL)
    data = (CURVE_DISC + struct.pack('<QQQQQ', item['vtr'], item['vqr'], item['rtr'], item['rqr'], item['supply'])
            + bytes([item['complete']]) + bytes(Keypair.from_seed(bytes([214]) * 32).pubkey())
            + bytes([item['mayhem'], 0]) + quote + struct.pack('<Q', 0) + bytes(2) + struct.pack('<QQ', 0, 0)
            + bytes(1) + struct.pack('<QQQ', 0, 0, 0))
    assert len(data) == 166
    return data


def run_captured(item):
    flags = item['flags']
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.add_program_from_file(MAYHEM, STUB_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(TOKEN_2022, TOKEN_2022_ELF)
    vm.add_program_from_file(ATA_PROGRAM, ATA_ELF)
    clock = vm.get_clock()
    vm.set_clock(Clock(clock.slot, clock.epoch_start_timestamp, clock.epoch, clock.leader_schedule_epoch, NOW))
    vm.airdrop(PAYER.pubkey(), 10**10)
    global_data = bytearray(1088 if flags['global_ok'] else 500)
    global_data[:8] = GLOBAL_DISC
    global_data[8] = 1
    global_data[IRTR_OFFSET:IRTR_OFFSET + 8] = struct.pack('<Q', item['irtr'])
    vm.set_account(GLOBAL, Account(10**9, bytes(global_data), PUMP))
    mint = bytearray(82)
    mint[44], mint[45] = 6, 1
    vm.set_account(MINT, Account(10**9, bytes(mint), TOKEN_2022))
    token_program = TOKEN_2022 if flags['token_program_ok'] else TOKEN
    vault_key = ata(SOL_VAULT, MINT, token_program) if flags['vault_address_ok'] else Pubkey.from_bytes(bytes([99]) * 32)
    vault = bytearray(165)
    vault[0:32] = bytes(MINT)
    vault[32:64] = bytes(SOL_VAULT if flags['vault_owner_ok'] else PAYER.pubkey())
    vault[64:72] = struct.pack('<Q', item['vault'])
    vault[108] = 1
    vm.set_account(vault_key, Account(10**9, bytes(vault), TOKEN_2022 if flags['vault_program_ok'] else TOKEN))
    curve = Pubkey.find_program_address([b'bonding-curve', bytes(MINT if flags['curve_ok'] else OTHER_MINT)], PUMP)[0]
    vm.set_account(curve, Account(10**9, curve_bytes(item), PUMP))
    authority, seed, bump = ((SOL_VAULT, b'sol-vault', SOL_VAULT_BUMP) if flags['seeds_ok']
                             else (FAKE_VAULT_AUTHORITY, b'sol-vaulx', FAKE_BUMP))
    vm.set_account(authority, Account(10**9, b'', MAYHEM))
    keys = {'sol_vault_authority': authority, 'mayhem_token_vault': vault_key, 'mint': MINT, 'global': GLOBAL,
            'bonding_curve': curve, 'token_program': token_program, 'event_authority': EVENT_AUTHORITY,
            'program': PUMP}
    metas = [AccountMeta(keys[a['name']], False, bool(a.get('writable'))) for a in INSTRUCTION['accounts']]
    data = bytes(INSTRUCTION['discriminator'])
    if flags['signed']:
        stub_data = struct.pack('<H', len(data)) + data + bytes([2, len(seed)]) + seed + bytes([1, bump])
        instruction = Instruction(MAYHEM, stub_data, [AccountMeta(PUMP, False, False)] + metas)
    else:
        instruction = Instruction(PUMP, data, metas)
    watched = [curve, vault_key, authority, GLOBAL, MINT]
    before = {k: vm.get_account(k) for k in watched}
    tx = Transaction.new_signed_with_payer([instruction], PAYER.pubkey(), [PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        err = result.err()
        code = getattr(getattr(err, 'err', None), 'code', None)
        return {'error': code if code is not None else str(err)}
    after = {k: vm.get_account(k) for k in watched}
    cpi_events = [bytes(ix.instruction().data) for group in result.inner_instructions() for ix in group
                  if bytes(ix.instruction().data)[:8] == EVENT_CPI_TAG]
    return {
        'error': None,
        'curve_before': bytes(before[curve].data), 'curve_after': bytes(after[curve].data),
        'unchanged': all(bytes(before[k].data) == bytes(after[k].data) and before[k].lamports == after[k].lamports
                         and before[k].owner == after[k].owner for k in watched if k != curve)
        and before[curve].lamports == after[curve].lamports,
        'events': [base64.b64decode(l[len('Program data: '):]) for l in result.logs() if l.startswith('Program data: ')],
        'cpi_events': cpi_events,
    }


def fixed_cases():
    big = 2**64 - 1
    cases = [case()]
    # Thresholds: SOL quote needs 10_000_000 real quote, SPL quote 1_000_000.
    cases += [case(rqr=r) for r in (0, 1, 999_999, 1_000_000, 9_999_999, 10_000_000, 10_000_001)]
    cases += [case(native=False, rqr=r) for r in (0, 999_999, 1_000_000, 1_000_001, 9_999_999)]
    # Denominator 2*supply - irtr - vault around 1e12 (vault drives it).
    cases += [case(vault=v) for v in (1_205_900_000_000_000, 1_205_900_000_000_001, 1_206_900_000_000_000)]
    cases += [case(native=False, vault=1_205_900_000_000_001), case(native=False, vault=1_205_900_000_000_000)]
    # Caps (vtr=0 makes the quotient equal real quote reserves).
    cases += [case(vtr=0, rqr=r) for r in (2 * 10**12 - 1, 2 * 10**12, 2 * 10**12 + 1, 5 * 10**12)]
    cases += [case(vtr=0, native=False, rqr=r) for r in (16 * 10**10 - 1, 16 * 10**10, 16 * 10**10 + 1)]
    cases += [case(rqr=10_000_000, vqr=10**12), case(rqr=10**11), case(rqr=10**11, native=False)]
    # Skips: complete or not in mayhem mode never computes, even when it would fail.
    cases += [case(complete=True), case(mayhem=False), case(complete=True, mayhem=False),
              case(complete=True, supply=3 * 10**14), case(mayhem=False, supply=big),
              case(complete=True, rqr=big, vtr=big, supply=10**15, irtr=10**15 - 10**12)]
    # Overflow: 2*supply, minus irtr, minus vault; the u128 product; the u64 narrowing.
    cases += [case(supply=2**63), case(supply=3 * 10**14), case(supply=3 * 10**14, rqr=1),
              case(supply=10**15, irtr=10**15, vault=10**15 + 1), case(supply=10**15, irtr=2 * 10**15 + 1),
              case(supply=2**63 - 1, irtr=0, vtr=big, rqr=big),
              case(supply=2**63 - 1, irtr=0, vtr=big, rqr=big, native=False),
              case(supply=10**15, irtr=10**15 - 10**12, vtr=2**63, rqr=2**63),
              case(supply=10**15, irtr=10**15 - 10**12, vtr=2**63, rqr=2**63, native=False),
              case(supply=10**15, irtr=10**15 - 10**12, vtr=2**63, rqr=2**40),
              case(supply=2**62, irtr=0, vtr=0, rqr=2**62)]
    # Account checks, one at a time and in pairs that pin the order.
    cases += [case(bad=(name,)) for name in FLAGS]
    cases += [case(bad=pair) for pair in (('global_ok', 'token_program_ok'), ('token_program_ok', 'signed'),
                                          ('signed', 'seeds_ok'), ('seeds_ok', 'vault_program_ok'),
                                          ('vault_program_ok', 'vault_owner_ok'),
                                          ('vault_owner_ok', 'vault_address_ok'),
                                          ('vault_address_ok', 'curve_ok'), ('global_ok', 'signed'))]
    cases += [case(bad=('curve_ok',), supply=3 * 10**14), case(bad=('signed',), complete=True)]
    return cases


def random_cases():
    rng = random.Random(20261029)
    cases = []
    for _ in range(120):
        bad = tuple(n for n in FLAGS if rng.random() < 0.04)
        rqr = rng.choice([rng.randint(0, 2 * 10**7), rng.randint(10**8, 10**11), rng.randint(10**11, 10**13),
                          rng.randint(0, 2**64 - 1)])
        supply = (rng.randint(5, 40) * 10**14 if rng.random() < 0.7
                  else rng.choice([rng.randint(1, 2**63), rng.randint(0, 2**64 - 1)]))
        irtr = rng.choice([793_100_000_000_000, rng.randint(0, 2 * supply) if supply < 2**63 else 0])
        room = max(0, 2 * supply - irtr) if supply < 2**63 else 0
        vault = rng.choice([0, rng.randint(0, room), max(0, room - rng.randint(0, 2 * 10**12)), room + 1])
        cases.append(case(bad, rqr=rqr, supply=supply, irtr=irtr, vault=min(vault, 2**64 - 1),
                          vtr=rng.choice([0, rng.randint(10**14, 2 * 10**15), rng.randint(0, 2**64 - 1)]),
                          vqr=rng.randint(0, 10**12), rtr=rng.randint(0, 10**15),
                          complete=rng.random() < 0.1, mayhem=rng.random() < 0.85, native=rng.random() < 0.5))
    return cases


class MayhemVirtualParamsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'mayhem-virtual-params-host'
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
        fields = [int(x) for x in answer.split(',')[1:]]
        # Signed delta of virtual_quote_reserves; every other byte stays.
        before, after = captured['curve_before'], captured['curve_after']
        delta = struct.unpack('<Q', after[16:24])[0] - struct.unpack('<Q', before[16:24])[0]
        self.assertEqual(delta, fields[3] - item['vqr'])
        self.assertEqual(after[:16] + after[24:], before[:16] + before[24:])
        self.assertTrue(captured['unchanged'])
        event = EVENT_DISC + struct.pack('<q', NOW) + bytes(MINT) + struct.pack('<6Q', *fields)
        self.assertEqual(captured['events'], [event])
        self.assertEqual(captured['cpi_events'], [EVENT_CPI_TAG + event])

    def run_cases(self, cases):
        for item, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item))

    def test_fixed_cases_match_captured_programs(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_programs(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: a passing captured run must fail once the new
        # quote reserve, an echoed field or the error code moves.
        samples = (case(), case(vtr=0, native=False, rqr=16 * 10**10 + 1), case(rqr=9_999_999), case(supply=2**63))
        for item, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            if answer.startswith('error:'):
                tampered = ['error:6023', 'ok,' + ','.join(str(item[k]) for k in ('vtr', 'vqr', 'vtr', 'vqr', 'rtr', 'rqr'))]
            else:
                fields = answer.split(',')
                tampered = []
                for index in range(1, 7):
                    changed = list(fields)
                    changed[index] = str(int(changed[index]) + 1)
                    tampered.append(','.join(changed))
                tampered.append('error:6024')
            for text in tampered:
                with self.subTest(case=host_line(item), tampered=text):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(item, text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        cases = fixed_cases()
        answers = self.host_answers(cases)
        self.assertEqual({a for a in answers if a.startswith('error:')}, {
            'error:2002', 'error:2006', 'error:2009', 'error:2015', 'error:2023', 'error:3003', 'error:3008',
            'error:4102', 'error:6024'})
        oks = [(item, [int(x) for x in a.split(',')[1:]]) for item, a in zip(cases, answers) if a.startswith('ok,')]
        self.assertTrue(any(f[3] == 2 * 10**12 for _, f in oks))
        self.assertTrue(any(f[3] == 16 * 10**10 for _, f in oks))
        self.assertTrue(any(f[3] < item['vqr'] for item, f in oks))
        self.assertTrue(any(f[3] > item['vqr'] for item, f in oks))
        self.assertTrue(any(f[3] == item['vqr'] for item, f in oks))


if __name__ == '__main__':
    unittest.main()
