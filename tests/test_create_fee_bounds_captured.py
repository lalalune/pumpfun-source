"""Captured-program checks for the creator fee a `create_v2` caller may request.

Every case runs Pump `create_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM (with the captured SPL Token,
Token-2022, Associated Token, Token Metadata and Mayhem programs) against the
captured mainnet Global in `tests/fixtures/pump_global_slot_461019957.json`,
with `creator_fee_configurable` (offset 1045) and
`max_configurable_creator_fee_bps` (offset 1046) patched per case. The quote
mint is admitted five ways: no quote accounts, the native mint, the Global
whitelisted mint, a QuoteControl entry, and a Pump curve created first in the
same VM (nested). The same inputs go to
`programs/pump/recovered/create_fee_bounds_host.rs`. The error code must
agree; on success the curve's `creator_fee_bps` and the CreateEvent's must
equal the model, and every other byte and every signed lamport delta must
equal the fee-0 create for the same quote source, so the fee changes nothing
else. This shows matching behaviour on these inputs only; it is not a
byte-identity claim.
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
DEPENDENCIES = {
    'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA': ROOT / 'evidence/dependencies/spl_token/deployed.so',
    'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb': ROOT / 'evidence/dependencies/spl_token_2022/deployed.so',
    'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL': ROOT / 'evidence/dependencies/associated_token/deployed.so',
    'metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s': ROOT / 'evidence/dependencies/token_metadata/deployed.so',
    'MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e': ROOT / 'evidence/original/mayhem/deployed.so',
}
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    DEPENDENCIES['TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA']: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    DEPENDENCIES['TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb']: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    DEPENDENCIES['ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL']: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
    DEPENDENCIES['metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s']: '31f0a627dba051a938de650464e55cc5397a4be0fd496929c1f9cf02fe5e9011',
    DEPENDENCIES['MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e']: 'a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb',
}
GLOBAL_FIXTURE = json.loads((ROOT / 'tests/fixtures/pump_global_slot_461019957.json').read_text())
GLOBAL_BYTES = base64.b64decode(GLOBAL_FIXTURE['data_base64'])
HOST_SOURCE = ROOT / 'programs/pump/recovered/create_fee_bounds_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
CREATE_V2 = next(i for i in IDL['instructions'] if i['name'] == 'create_v2')
CREATE_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'CreateEvent'))
QUOTE_CONTROL_DISC = bytes(next(a['discriminator'] for a in IDL['accounts'] if a['name'] == 'QuoteControl'))
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
METADATA = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
MAYHEM = Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
NATIVE = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()

USER = Keypair.from_seed(bytes([211]) * 32)
MINT = Keypair.from_seed(bytes([212]) * 32)
QUOTE = Keypair.from_seed(bytes([213]) * 32)
GLOBAL = Pubkey.from_string(GLOBAL_FIXTURE['address'])
QUOTE_CONTROL = Pubkey.find_program_address([b'quote-control'], PUMP)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
NOW = 1_700_000_000
U64 = 2**64 - 1
CURVE_FEE = 115           # BondingCurve.creator_fee_bps
TX_FEE = 2 * 5_000        # payer and mint signatures
SOURCES = ('sol', 'native', 'whitelisted', 'controlled', 'nested')
CAPTURED_MAX = struct.unpack_from('<Q', GLOBAL_BYTES, 1046)[0]


def pda(*seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)[0]


def ata(owner, program, mint):
    return Pubkey.find_program_address([bytes(owner), bytes(program), bytes(mint)], ATA)[0]


def string(text):
    raw = text.encode()
    return struct.pack('<I', len(raw)) + raw


def case(source, requested, configurable=True, max_bps=CAPTURED_MAX, omit=False):
    return dict(source=source, requested=requested, configurable=configurable, max_bps=max_bps, omit=omit)


def host_line(item):
    model_source = {'sol': 'sol', 'native': 'sol'}.get(item['source'], item['source'])
    requested = 0 if item['omit'] else item['requested']
    return f"{model_source},{requested},{int(item['configurable'])},{item['max_bps']}"


def new_vm(global_data):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    for key, path in DEPENDENCIES.items():
        vm.add_program_from_file(Pubkey.from_string(key), path)
    vm.set_clock(Clock(100, NOW, 0, 0, NOW))
    vm.set_account(USER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(GLOBAL, Account(GLOBAL_FIXTURE['lamports'], bytes(global_data), PUMP))
    return vm


def create(vm, mint, quote_metas=(), fee_args=b''):
    """Send one create_v2 for `mint`; return the accounts it touched, before and after."""
    curve = pda(b'bonding-curve', bytes(mint.pubkey()))
    names = {
        'mint': mint.pubkey(), 'mint_authority': pda(b'mint-authority'), 'bonding_curve': curve,
        'associated_bonding_curve': ata(curve, TOKEN22, mint.pubkey()), 'global': GLOBAL, 'user': USER.pubkey(),
        'system_program': SYSTEM, 'token_program': TOKEN22, 'associated_token_program': ATA,
        'mayhem_program_id': MAYHEM, 'global_params': pda(b'global-params', program=MAYHEM),
        'sol_vault': pda(b'sol-vault', program=MAYHEM),
        'mayhem_state': pda(b'mayhem-state', bytes(mint.pubkey()), program=MAYHEM),
        'mayhem_token_vault': Pubkey.from_bytes(bytes([7]) * 32), 'event_authority': EVENT_AUTHORITY,
        'program': PUMP,
    }
    metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False))
             for a in CREATE_V2['accounts']] + list(quote_metas)
    data = (bytes(CREATE_V2['discriminator']) + string('Synthetic Coin') + string('SYNTH')
            + string('https://example.invalid/metadata.json') + bytes(USER.pubkey()) + bytes([0]) + fee_args)
    tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)],
                                           USER.pubkey(), [USER, mint], vm.latest_blockhash())
    keys = sorted({m.pubkey for m in metas if not (vm.get_account(m.pubkey) or Account(0, b'', SYSTEM)).executable},
                  key=bytes)

    def snapshot():
        out = {}
        for key in keys:
            account = vm.get_account(key)
            out[key] = (0, b'', None) if account is None else (account.lamports, bytes(account.data), account.owner)
        return out

    before = snapshot()
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    error = None
    if failed:
        text = str(result.err())
        error = int(text.split('Custom(')[1].split(')')[0]) if 'Custom(' in text else text
    events = [base64.b64decode(line.split(' ', 2)[2]) for line in meta.logs() if line.startswith('Program data: ')]
    return dict(error=error, before=before, after=snapshot(), curve=curve,
                events=[e for e in events if e[:8] == CREATE_EVENT])


class Nested:
    """A Pump curve on QUOTE, created by the captured program, to use as a nested quote."""
    accounts = None

    @classmethod
    def build(cls):
        if cls.accounts is None:
            vm = new_vm(GLOBAL_BYTES)
            run = create(vm, QUOTE)
            assert run['error'] is None, run['error']
            cls.accounts = {k: v for k, v in run['after'].items() if v != run['before'][k]}
        return cls.accounts


def run_captured(item):
    global_data = bytearray(GLOBAL_BYTES)
    global_data[1045] = int(item['configurable'])
    struct.pack_into('<Q', global_data, 1046, item['max_bps'])
    source = item['source']
    if source == 'whitelisted':
        global_data[1013:1045] = bytes(QUOTE.pubkey())
    vm = new_vm(global_data)
    curve = pda(b'bonding-curve', bytes(MINT.pubkey()))
    quote_metas = []
    if source == 'native':
        quote_metas = [AccountMeta(NATIVE, False, False), AccountMeta(ata(curve, TOKEN, NATIVE), False, True),
                       AccountMeta(TOKEN, False, False)]
    elif source in ('whitelisted', 'controlled', 'nested'):
        program = TOKEN22 if source == 'nested' else TOKEN
        if source == 'nested':
            for key, (lamports, data, owner) in Nested.build().items():
                vm.set_account(key, Account(lamports, data, owner))
        else:
            mint_data = (struct.pack('<I', 1) + bytes(USER.pubkey()) + struct.pack('<Q', 10**15) + bytes([6, 1])
                         + bytes(36))
            vm.set_account(QUOTE.pubkey(), Account(10**7, mint_data, TOKEN))
        quote_metas = [AccountMeta(QUOTE.pubkey(), False, False),
                       AccountMeta(ata(curve, program, QUOTE.pubkey()), False, True),
                       AccountMeta(program, False, False)]
        if source in ('controlled', 'nested'):
            entries = [(QUOTE.pubkey(), 123_456_789)] if source == 'controlled' else []
            control = (QUOTE_CONTROL_DISC + bytes(USER.pubkey()) * 2 + bytes(32) + struct.pack('<I', len(entries))
                       + b''.join(bytes(k) + struct.pack('<Q', r) for k, r in entries))
            vm.set_account(QUOTE_CONTROL, Account(10**9, control, PUMP))
            quote_metas.append(AccountMeta(QUOTE_CONTROL, False, False))
        if source == 'nested':
            quote_metas.append(AccountMeta(pda(b'bonding-curve', bytes(QUOTE.pubkey())), False, False))
    fee_args = b'' if item['omit'] else b'\0' + struct.pack('<Q', item['requested']) + b'\0'
    run = create(vm, MINT, quote_metas, fee_args)
    run['delta'] = {k: run['after'][k][0] - run['before'][k][0] for k in run['before']}
    return run


def fixed_cases():
    cap = CAPTURED_MAX
    # 2**32 + 1 is out of range but its low 32 bits are not, so a truncating
    # comparison would accept it.
    fees = (0, 1, cap - 1, cap, cap + 1, 10_000, 2**32 + 1, U64)
    gates = ((True, cap), (False, cap), (True, 0), (True, 1), (True, U64), (False, 0))
    cases = [case(s, f, c, m) for s in SOURCES for f in fees for c, m in gates]
    cases += [case(s, 500, True, cap, omit=True) for s in SOURCES]
    return cases


def random_cases(count=80, seed=1884):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        max_bps = rng.choice((0, 1, 100, CAPTURED_MAX, 10_000, U64, rng.randrange(0, 20_000)))
        requested = rng.choice((0, 1, max_bps, max_bps + 1, rng.randrange(0, 20_000), U64))
        cases.append(case(rng.choice(SOURCES), min(requested, U64), rng.random() > 0.25, max_bps))
    return cases


class CreateFeeBoundsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        assert hashlib.sha256(GLOBAL_BYTES).hexdigest() == GLOBAL_FIXTURE['data_sha256']
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'create-fee-bounds-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host
        cls.baselines = {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        answers = subprocess.run([str(self.host)], input=text, capture_output=True, text=True,
                                 check=True).stdout.splitlines()
        self.assertEqual(len(answers), len(cases))
        return answers

    def baseline(self, source):
        if source not in self.baselines:
            run = run_captured(case(source, 0))
            self.assertIsNone(run['error'], source)
            self.baselines[source] = run
        return self.baselines[source]

    def assert_matches(self, item, answer, captured):
        kind, value = answer.split(',')
        if kind == 'error':
            self.assertEqual(captured['error'], int(value))
            # A rejected create only charges the two signature fees. The
            # expectation takes its keys from the before-snapshot, not from the
            # delta: keyed from the observed delta, a run that stopped recording
            # an account shrank both sides of the comparison to match.
            payer = USER.pubkey()
            self.assertIn(payer, captured['before'])
            self.assertEqual(captured['delta'],
                             {k: -TX_FEE if k == payer else 0 for k in captured['before']})
            self.assertEqual({k: v[1:] for k, v in captured['after'].items()},
                             {k: v[1:] for k, v in captured['before'].items()})
            self.assertEqual(captured['events'], [])
            return
        self.assertIsNone(captured['error'])
        stored = int(value)
        base = self.baseline(item['source'])
        curve = captured['curve']
        # The fee lands in the curve and in the CreateEvent as a u64.
        self.assertEqual(struct.unpack_from('<Q', captured['after'][curve][1], CURVE_FEE)[0], stored)
        self.assertEqual(len(captured['events']), 1)
        event = captured['events'][0]
        self.assertEqual(struct.unpack_from('<Q', event, len(event) - 10)[0], stored)
        # Everything else equals the fee-0 create for the same source: the
        # signed lamport deltas, every owner and every other data byte.
        self.assertEqual(captured['delta'], base['delta'])
        expected_curve = bytearray(base['after'][curve][1])
        struct.pack_into('<Q', expected_curve, CURVE_FEE, stored)
        for key, after in captured['after'].items():
            want = base['after'][key]
            if key == curve:
                want = (want[0], bytes(expected_curve), want[2])
            if key == GLOBAL:
                want = captured['before'][key]
            self.assertEqual(after, want, str(key))
        expected_event = bytearray(base['events'][0])
        struct.pack_into('<Q', expected_event, len(expected_event) - 10, stored)
        self.assertEqual(event, bytes(expected_event))

    def run_cases(self, cases):
        outcomes = set()
        for item, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=item, host=answer):
                self.assert_matches(item, answer, run_captured(item))
            outcomes.add(answer.split(',')[1] if answer.startswith('error') else
                         (item['source'], 'kept' if answer != 'ok,0' else 'zero'))
            if answer == 'ok,0' and item['requested'] and not item['omit']:
                outcomes.add((item['source'], 'dropped'))
        return outcomes

    def test_fixed_cases_match_captured_program(self):
        outcomes = self.run_cases(fixed_cases())
        # Coverage: both errors, a kept fee for each counted source, and a
        # nonzero request dropped to 0 for every uncounted source.
        for needed in ('6077', '6078', ('controlled', 'kept'), ('nested', 'kept'),
                       *((s, 'dropped') for s in ('sol', 'native', 'whitelisted'))):
            self.assertIn(needed, outcomes)

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_captured_global_cap_matches_ui_constants(self):
        # The create form (`app/reconstruction/create-advanced-fee`, PR #1884)
        # accepts 0.01 to 3 percent, i.e. 1 to 300 bps.
        ui_min_bps, ui_max_bps = 1, 300
        self.assertEqual(GLOBAL_BYTES[1045], 1)
        self.assertEqual(CAPTURED_MAX, ui_max_bps)
        for source in ('controlled', 'nested'):
            for bps, answer in ((ui_min_bps, 'ok,1'), (ui_max_bps, 'ok,300'), (ui_max_bps + 1, 'error,6078')):
                item = case(source, bps)
                self.assertEqual(self.host_answers([item]), [answer])
                self.assert_matches(item, answer, run_captured(item))

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: passing captured runs must fail once the stored fee
        # is off by one, an error is claimed instead, a dropped fee is claimed
        # as kept, or the payer's lamport delta changes sign.
        for item in (case('controlled', 300), case('nested', 1), case('sol', 300), case('whitelisted', 1)):
            answer, = self.host_answers([item])
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            stored = int(answer.split(',')[1])
            for text in (f'ok,{stored + 1}', 'error,6078', 'ok,300' if stored == 0 else 'ok,0'):
                with self.subTest(case=item, tampered=text):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(item, text, captured)
            payer = USER.pubkey()
            flipped = dict(captured, delta=dict(captured['delta']))
            flipped['delta'][payer] = -flipped['delta'][payer]
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, flipped)
        item = case('controlled', 301)
        captured = run_captured(item)
        self.assert_matches(item, 'error,6078', captured)
        for text in ('error,6077', 'ok,301', 'ok,0'):
            with self.subTest(case=item, tampered=text):
                with self.assertRaises(AssertionError):
                    self.assert_matches(item, text, captured)


if __name__ == '__main__':
    unittest.main()
