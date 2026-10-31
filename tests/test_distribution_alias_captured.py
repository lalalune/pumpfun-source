"""Captured-program checks for shareholders that share a key with another slot.

Every case runs Pump `distribute_creator_fees` or the token route of
`distribute_creator_fees_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token
and Associated Token programs, where a sharing config names the creator vault,
the payer, the curve, the config, the mint, the event authority or the same
wallet twice. The same inputs go to
`programs/pump/recovered/distribution_alias_host.rs`, and the error, the final
balance of every key and token account, the event total and the return data
must agree. This shows matching behavior on these inputs only; it is not a
byte-identity claim.
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
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/distribution_alias_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}

PAYER = Keypair.from_seed(bytes([224]) * 32)
MINT = Pubkey.from_bytes(bytes([61]) * 32)
QUOTE = Pubkey.from_bytes(bytes([62]) * 32)
ADMIN = Pubkey.from_bytes(bytes([63]) * 32)
HOLDER0 = Pubkey.from_bytes(bytes([64]) * 32)
HOLDER1 = Pubkey.from_bytes(bytes([65]) * 32)
TIMESTAMP = 1_700_000_000
TX_FEE = 5000
ZERO_RENT = 890_880
TOKEN_RENT = 2_039_280
MINT_RENT = 1_461_600
PAYER_START = 10**12
U64 = 2**64 - 1


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)[0]


def ata_of(wallet):
    return pda([bytes(wallet), bytes(TOKEN), bytes(QUOTE)], ATA)


CURVE = pda([b'bonding-curve', bytes(MINT)])
SHARING = pda([b'sharing-config', bytes(MINT)], FEES)
VAULT = pda([b'creator-vault', bytes(SHARING)])
EVENT_AUTHORITY = pda([b'__event_authority'])
ROLES = {'payer': PAYER.pubkey(), 'vault': VAULT, 'curve': CURVE, 'config': SHARING, 'mint': MINT,
         'ea': EVENT_AUTHORITY, 'h0': HOLDER0, 'h1': HOLDER1, 'pump': PUMP, 'system': SYSTEM}
WATCHED = ('payer', 'vault', 'curve', 'config', 'mint', 'ea', 'h0', 'h1')
SHAREHOLDERS = ('payer', 'vault', 'curve', 'config', 'mint', 'ea', 'h0', 'h1')


def mint_data():
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(mint, owner, amount):
    return bytes(mint) + bytes(owner) + struct.pack('<Q', amount) + bytes(36) + bytes([1]) + bytes(56)


def curve_data(quote):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, 10**15, 3 * 10**10, 10**14, 10**9, 10**15)
    data[49:81] = bytes(SHARING)
    if quote:
        data[83:115] = bytes(QUOTE)
    return bytes(data)


def shareholders_bytes(slots):
    return b''.join(bytes(ROLES[s[0]]) + struct.pack('<H', s[1]) for s in slots)


def sharing_data(slots):
    return (ACCOUNT_DISC['SharingConfig'] + bytes([255, 1, 1]) + bytes(MINT) + bytes(ADMIN) + bytes([0])
            + struct.pack('<I', len(slots)) + shareholders_bytes(slots))


def slot(role, bps, writable=True):
    return (role, bps, writable)


def v1(slots, vault=ZERO_RENT + 10**9, h0=10**9, h1=10**9, ea=0, curve=10**9, config=10**9, mint=10**9):
    return dict(op='v1', slots=tuple(slots), vault=vault, h0=h0, h1=h1, ea=ea, curve=curve, config=config, mint=mint)


def v2(slots, tokens=10**9, have=('h0', 'h1'), init=False):
    return dict(op='v2', slots=tuple(slots), tokens=tokens, have=tuple(have), init=init)


class Vm:
    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(PUMP, PUMP_ELF)
        self.vm.add_program_from_file(TOKEN, TOKEN_ELF)
        self.vm.add_program_from_file(ATA, ATA_ELF)
        self.vm.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
        self.stale = [ata_of(ROLES[r]) for r in WATCHED]

    def lamports(self, key):
        account = self.vm.get_account(key)
        return account.lamports if account else 0

    def tokens(self, key):
        account = self.vm.get_account(key)
        return struct.unpack_from('<Q', bytes(account.data), 64)[0] if account else 0

    def base(self, item):
        vm = self.vm
        for key in self.stale:
            vm.set_account(key, Account(0, b'', SYSTEM))
        vm.set_account(PAYER.pubkey(), Account(PAYER_START, b'', SYSTEM))
        quote = item['op'] == 'v2'
        vm.set_account(CURVE, Account(item.get('curve', 10**9), curve_data(quote), PUMP))
        vm.set_account(SHARING, Account(item.get('config', 10**9), sharing_data(item['slots']), FEES))
        vm.set_account(MINT, Account(item.get('mint', 10**9), mint_data(), TOKEN))
        vm.set_account(QUOTE, Account(10**9, mint_data(), TOKEN))
        vm.set_account(VAULT, Account(item.get('vault', 10**9), b'', SYSTEM))
        vm.set_account(HOLDER0, Account(item.get('h0', 10**9), b'', SYSTEM))
        vm.set_account(HOLDER1, Account(item.get('h1', 10**9), b'', SYSTEM))
        vm.set_account(EVENT_AUTHORITY, Account(item.get('ea', 0), b'', SYSTEM))

    def send(self, data, metas):
        vm = self.vm
        vm.expire_blockhash()
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)],
                                               PAYER.pubkey(), [PAYER], vm.latest_blockhash())
        return vm.send_transaction(tx)

    def run(self, item):
        self.base(item)
        slots = item['slots']
        names = {'payer': PAYER.pubkey(), 'mint': MINT, 'bonding_curve': CURVE, 'sharing_config': SHARING,
                 'creator_vault': VAULT, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
                 'creator_vault_quote_token_account': ata_of(VAULT), 'quote_mint': QUOTE, 'quote_token_program': TOKEN,
                 'associated_token_program': ATA}
        if item['op'] == 'v1':
            ix = IX['distribute_creator_fees']
            data = bytes(ix['discriminator'])
            wallets = [AccountMeta(ROLES[s[0]], False, s[2]) for s in slots]
            atas = []
        else:
            ix = IX['distribute_creator_fees_v2']
            data = bytes(ix['discriminator']) + bytes([int(item['init'])])
            wallets = [AccountMeta(ROLES[s[0]], False, s[2]) for s in slots]
            atas = [AccountMeta(ata_of(ROLES[s[0]]), False, s[2]) for s in slots]
            self.vm.set_account(ata_of(VAULT), Account(TOKEN_RENT, token_data(QUOTE, VAULT, item['tokens']), TOKEN))
            for role in (r for r in item['have'] if r != 'vault'):
                self.vm.set_account(ata_of(ROLES[role]), Account(TOKEN_RENT, token_data(QUOTE, ROLES[role], 0), TOKEN))
        metas = [AccountMeta(names[a['name']], a['name'] == 'payer', a.get('writable', False)) for a in ix['accounts']]
        result = self.send(data, metas + wallets + atas)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            if code:
                return {'error': int(code.group(1))}
            return {'error': re.search(r'(\w+)\)*$', text).group(1)}
        out = {'error': None, 'balances': [self.lamports(ROLES[r]) for r in WATCHED],
               'tokens': [self.tokens(ata_of(ROLES[r])) for r in WATCHED],
               'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')],
               'return_data': bytes(result.return_data().data)}
        return out


def host_line(item):
    slots = ';'.join(f"{s[0]}:{s[1]}:{'w' if s[2] else 'r'}" for s in item['slots'])
    if item['op'] == 'v1':
        held = [PAYER_START - TX_FEE, item['vault'], item['curve'], item['config'], item['mint'], item['ea'],
                item['h0'], item['h1']]
        return f"v1|{','.join(map(str, held))}|{slots}"
    return f"v2|{item['tokens']}|{int(item['init'])}|{','.join(item['have'])}|{slots}"


def event_total(event):
    # The total sits ahead of the trailing quote mint.
    return struct.unpack_from('<Q', event, len(event) - 40)[0]


def fixed_cases():
    cases = []
    S = slot
    rest = dict(vault=ZERO_RENT + 10**9)
    # Every ordered pair of shareholder keys at three share splits.
    for a in SHAREHOLDERS:
        for b in SHAREHOLDERS:
            for pair in ((5000, 5000), (10_000, 10_000), (20_000, 1)):
                cases.append(v1([S(a, pair[0]), S(b, pair[1])], **rest))
                cases.append(v2([S(a, pair[0]), S(b, pair[1])], have=SHAREHOLDERS))
                cases.append(v2([S(a, pair[0]), S(b, pair[1])], have=(), init=True))
                cases.append(v2([S(a, pair[0]), S(b, pair[1])], have=('h0',), init=True))
            cases.append(v2([S(a, 5000), S(b, 5000)], have=('h0', 'h1')))
        # Single and read-only slots.
        for bps in (1, 5000, 10_000, 20_000, 65_535):
            cases.append(v1([S(a, bps)]))
            cases.append(v2([S(a, bps)], have=SHAREHOLDERS))
        for writable in ((True, False), (False, True), (False, False)):
            for b in ('h0', 'vault', a):
                cases.append(v1([S(a, 5000, writable[0]), S(b, 5000, writable[1])]))
                cases.append(v2([S(a, 5000, writable[0]), S(b, 5000, writable[1])], have=SHAREHOLDERS))
                cases.append(v2([S(a, 5000, writable[0]), S(b, 5000, writable[1])], have=(), init=True))
        # A share rounded to nothing, and an empty vault token account.
        cases.append(v1([S(a, 1, False)], vault=ZERO_RENT + 9_999))
        cases.append(v2([S(a, 1, False)], tokens=9_999, have=SHAREHOLDERS))
        cases.append(v2([S(a, 5000, False)], tokens=0, have=SHAREHOLDERS))
        cases.append(v2([S(a, 5000, False)], tokens=0, have=(), init=True))
        # Programs and zero shares keep their order against an alias.
        for bad in (S('pump', 5000), S('system', 5000), S(a, 0)):
            cases.append(v1([S(a, 5000), bad]))
            cases.append(v1([bad, S(a, 5000)]))
            cases.append(v2([S(a, 5000), bad], have=(), init=True))
            cases.append(v2([S(a, 5000), bad], have=()))
            cases.append(v2([bad, S(a, 5000)], have=()))
    # Rent thresholds of keys that appear twice, or that are the vault.
    for extra in (-1, 0, 1):
        for bps in ((5000, 5000), (3000, 7000), (1, 9_999)):
            for role in ('h0', 'ea'):
                need = max((ZERO_RENT * 10_000 + b - 1) // b for b in bps)
                cases.append(v1([S(role, bps[0]), S(role, bps[1])], vault=ZERO_RENT + need + extra, h0=0))
                cases.append(v1([S(role, bps[0]), S('h1', bps[1])], vault=ZERO_RENT + need + extra, h0=0))
        for held in (0, 1, ZERO_RENT - 1):
            need = (ZERO_RENT - held) * 2
            cases.append(v1([S('ea', 5000), S('ea', 5000)], ea=held, vault=ZERO_RENT + need + extra))
            cases.append(v1([S('h0', 10_000), S('h0', 1)], h0=held, vault=ZERO_RENT + (ZERO_RENT - held) * 10_000 + extra))
        for role, size in (('curve', 166), ('config', 148), ('mint', 82)):
            short = 1_000
            need = (short * 10_000 + 4_999) // 5_000
            floor = (128 + size) * 6960 - short
            cases.append(v1([S(role, 5000), S('h0', 5000)], vault=ZERO_RENT + need + extra, **{role: floor}))
    # The vault below or around its own rent, paying itself.
    for held in (0, 1, ZERO_RENT - 1, ZERO_RENT, ZERO_RENT + 1, ZERO_RENT + 10_000, 900_000, 2 * ZERO_RENT, U64 // 70_000):
        for slots in ([S('vault', 5000)], [S('vault', 10_000)], [S('vault', 30_000)], [S('vault', 10_000), S('h0', 10_000)],
                      [S('h0', 10_000), S('vault', 10_000)], [S('vault', 5000), S('h0', 5000), S('vault', 5000)],
                      [S('h0', 15_000)], [S('h0', 9_999), S('vault', 2)]):
            cases.append(v1(slots, vault=held or 1))
    # Vault token balances, a repeated new wallet, and order of the failures.
    for tokens in (0, 1, 3, 9_999, 10_000, 10**9, U64 // 65_535, U64 // 65_535 + 1):
        for slots in ([S('vault', 10_000), S('h0', 10_000)], [S('h0', 10_000), S('vault', 10_000)],
                      [S('vault', 5000), S('vault', 5000)], [S('h0', 5000), S('h0', 5000)],
                      [S('vault', 20_000)], [S('h0', 65_535)], [S('h0', 3333), S('h1', 3333), S('vault', 3334)]):
            cases.append(v2(slots, tokens=tokens, have=('h0', 'h1')))
            cases.append(v2(slots, tokens=tokens, have=(), init=True))
    return cases


def random_cases(count=1500, seed=3341):
    rng = random.Random(seed)
    roles = SHAREHOLDERS + ('h0', 'h0', 'vault', 'vault', 'pump')
    bps = lambda: rng.choice((0, 1, 2500, 3333, 5000, 7500, 10_000, 15_000, rng.randrange(1, 12_000)))
    cases = []
    for _ in range(count):
        slots = [slot(rng.choice(roles), bps(), rng.random() < 0.85) for _ in range(rng.randrange(1, 6))]
        if rng.random() < 0.5:
            vault = rng.choice((ZERO_RENT, ZERO_RENT + rng.randrange(0, 5 * 10**6), ZERO_RENT + rng.randrange(0, 10**10)))
            cases.append(v1(slots, vault=vault, h0=rng.choice((0, 1, ZERO_RENT, 10**9)), h1=rng.choice((ZERO_RENT, 10**9)),
                            ea=rng.choice((0, 1, ZERO_RENT))))
        else:
            cases.append(v2(slots, tokens=rng.choice((0, 7, rng.randrange(0, 10**6), 10**12)),
                            have=rng.sample(SHAREHOLDERS, rng.randrange(0, 9)), init=rng.random() < 0.7))
    return cases


class DistributionAliasCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'distribution-alias-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.vm = Vm()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        return subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()

    def assert_matches(self, item, answer, captured):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        if not answer.startswith('ok'):
            self.assertEqual(captured['error'], answer)
            return
        self.assertIsNone(captured['error'])
        fields = list(map(int, answer.split(',')[1:]))
        distributed, flag, balances = fields[0], fields[1], fields[2:]
        if item['op'] == 'v1':
            self.assertEqual(captured['balances'], balances)
            self.assertEqual(event_total(captured['return_data']), distributed)
            events = captured['events']
            self.assertEqual(len(events), flag)
            if flag:
                self.assertEqual(event_total(events[0]), distributed)
        else:
            self.assertEqual(captured['tokens'], balances)
            self.assertEqual(captured['balances'][0], PAYER_START - TX_FEE - flag * TOKEN_RENT)
            self.assertEqual(event_total(captured['events'][0]), distributed)
            self.assertEqual(captured['return_data'], captured['events'][0][8:])

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, self.vm.run(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_changed_answers(self):
        # Negative control: a passing captured payout must fail once a balance
        # or the total changes.
        for item in (v1([slot('vault', 5000), slot('h0', 5000)]), v2([slot('vault', 5000), slot('h0', 5000)])):
            answer = self.host_answers([item])[0]
            captured = self.vm.run(item)
            self.assert_matches(item, answer, captured)
            fields = answer.split(',')
            for index in (1, len(fields) - 2):
                changed = ','.join(str(int(f) + 1) if i == index else f for i, f in enumerate(fields))
                with self.subTest(index=index), self.assertRaises(AssertionError):
                    self.assert_matches(item, changed, captured)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {'ok', 'PrivilegeEscalation', 'IllegalOwner', 'error:1', 'error:6024', 'error:6052',
                                    'error:6055', 'error:6070'})


if __name__ == '__main__':
    unittest.main()
