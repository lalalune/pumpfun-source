"""Captured-program checks for Pump `distribute_creator_fees_v2` on SPL quote coins.

Every case runs `distribute_creator_fees_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token
and Associated Token programs, for a bonding curve whose quote mint is an SPL
mint. Synthetic mint, curve, pump_fees SharingConfig, creator-vault, vault
quote token account, shareholder wallet and token accounts are used. The same
inputs go to `programs/pump/recovered/creator_fee_distribution_quote_host.rs`,
and the error, signed lamport and token movements, return data,
DistributeCreatorFeesEvent and its self-CPI copy must agree. This shows
matching behavior on these inputs only; it is not a byte-identity claim.
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
DEPS = ROOT / 'evidence/dependencies'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/creator_fee_distribution_quote_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}
EVENT_IX_TAG = bytes([228, 69, 165, 46, 81, 203, 154, 29])

PAYER = Keypair.from_seed(bytes([223]) * 32)
MINT = Pubkey.from_bytes(bytes([51]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([52]) * 32)
QUOTE = Pubkey.from_bytes(bytes([53]) * 32)
OTHER_QUOTE = Pubkey.from_bytes(bytes([54]) * 32)
ADMIN = Pubkey.from_bytes(bytes([55]) * 32)
OTHER = Pubkey.from_bytes(bytes([56]) * 32)
# An unrelated captured program loaded here stands in for an executable shareholder.
EXECUTABLE = Pubkey.from_bytes(bytes([57]) * 32)
HOLDERS = [Pubkey.from_bytes(bytes([70 + i]) * 32) for i in range(8)]
TX_FEE = 5000
TOKEN_RENT = 2_039_280
VAULT_LAMPORTS = 10**9
TIMESTAMP = 1_700_000_000
U64 = 2**64 - 1


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)[0]


def ata(wallet, mint=QUOTE):
    return pda([bytes(wallet), bytes(TOKEN), bytes(mint)], ATA)


CURVE = pda([b'bonding-curve', bytes(MINT)])
SHARING = pda([b'sharing-config', bytes(MINT)], FEES)
VAULT = pda([b'creator-vault', bytes(SHARING)])
EVENT_AUTHORITY = pda([b'__event_authority'])


def mint_data(decimals):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(mint, owner, amount):
    return bytes(mint) + bytes(owner) + struct.pack('<Q', amount) + bytes(36) + bytes([1]) + bytes(56)


def curve_data(item):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, 10**15, 3 * 10**10, 10**14, 10**9, 10**15)
    data[49:81] = bytes(SHARING if item['curve_creator'] == 'sharing' else OTHER)
    data[83:115] = bytes(QUOTE)
    struct.pack_into('<Q', data, 125, item['creator_fee'])
    return bytes(data)


def holder_address(i, h):
    return EXECUTABLE if h['wallet'] == 'exec' else HOLDERS[i]


def shareholders_bytes(item):
    return b''.join(bytes(holder_address(i, h)) + struct.pack('<H', h['bps']) for i, h in enumerate(item['holders']))


def sharing_data(item):
    return (ACCOUNT_DISC['SharingConfig'] + bytes([255, 1, int(item['active'])])
            + bytes(MINT if item['config_mint'] == 'mint' else OTHER_MINT) + bytes(ADMIN) + bytes([0])
            + struct.pack('<I', len(item['holders'])) + shareholders_bytes(item))


def holder(bps, wallet='ok', ata='exists'):
    # wallet: 'ok', 'wrong' (another account in the slot) or 'exec' (the
    # configured address is an executable program); ata: 'exists', 'absent'
    # (correct address, no account) or 'wrong' (another wallet's ATA).
    return dict(bps=bps, wallet=wallet, ata=ata)


DEFAULTS = dict(vault_tokens=10**9, holders=None, active=True, creator_fee=0, curve_creator='sharing',
                config_mint='mint', quote='quote', initialize_ata=False, remaining=None)


def case(**changes):
    item = dict(DEFAULTS, **changes)
    if item['holders'] is None:
        item['holders'] = [holder(5000), holder(3000), holder(2000)]
    if item['remaining'] is None:
        item['remaining'] = 2 * len(item['holders'])
    return item


def flat(data):
    return bytes(data[1:]) if data and isinstance(data[0], list) else bytes(data)


def error_name(text):
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return code.group(1)
    return 'invalid_account_data' if 'InvalidAccountData' in text else text


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    for name, key in (('spl_token', TOKEN), ('associated_token', ATA)):
        vm.add_program_from_file(key, DEPS / name / 'deployed.so')
    vm.add_program_from_file(EXECUTABLE, DEPS / 'donation_relay/deployed.so')
    vm.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(MINT, Account(10**9, mint_data(6), TOKEN))
    for quote in (QUOTE, OTHER_QUOTE):
        vm.set_account(quote, Account(10**9, mint_data(6), TOKEN))
    vm.set_account(CURVE, Account(10**9, curve_data(item), PUMP))
    vm.set_account(SHARING, Account(10**9, sharing_data(item), FEES))
    vm.set_account(VAULT, Account(VAULT_LAMPORTS, b'', SYSTEM))
    quote = QUOTE if item['quote'] == 'quote' else OTHER_QUOTE
    vault_ata = ata(VAULT, quote)
    if item['vault_tokens'] is not None:
        vm.set_account(vault_ata, Account(TOKEN_RENT, token_data(quote, VAULT, item['vault_tokens']), TOKEN))
    wallets, atas, holder_atas = [], [], []
    for i, h in enumerate(item['holders']):
        address = holder_address(i, h)
        wallets.append(OTHER if h['wallet'] == 'wrong' else address)
        if h['wallet'] != 'exec':
            vm.set_account(address, Account(10**9, b'', SYSTEM))
        holder_atas.append(ata(address))
        atas.append(ata(OTHER) if h['ata'] == 'wrong' else ata(address))
        if h['ata'] == 'exists':
            vm.set_account(ata(address), Account(TOKEN_RENT, token_data(QUOTE, address, 0), TOKEN))
    vm.set_account(OTHER, Account(10**9, b'', SYSTEM))
    vm.set_account(ata(OTHER), Account(TOKEN_RENT, token_data(QUOTE, OTHER, 0), TOKEN))
    remaining = (wallets + atas)[:item['remaining']]
    names = {'payer': PAYER.pubkey(), 'mint': MINT, 'bonding_curve': CURVE, 'sharing_config': SHARING,
             'creator_vault': VAULT, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
             'creator_vault_quote_token_account': vault_ata, 'quote_mint': quote, 'quote_token_program': TOKEN,
             'associated_token_program': ATA}
    ix = IX['distribute_creator_fees_v2']
    metas = [AccountMeta(names[a['name']], a['name'] == 'payer', a.get('writable', False)) for a in ix['accounts']]
    metas += [AccountMeta(key, False, True) for key in remaining]

    def lamports(key):
        account = vm.get_account(key)
        return account.lamports if account else 0

    def tokens(key):
        account = vm.get_account(key)
        return struct.unpack_from('<Q', bytes(account.data), 64)[0] if account and len(account.data) >= 72 else 0

    lamport_keys = [PAYER.pubkey(), VAULT]
    token_keys = [vault_ata] + holder_atas
    before = [lamports(k) for k in lamport_keys]
    tokens_before = [tokens(k) for k in token_keys]
    data = bytes(ix['discriminator']) + bytes([int(item['initialize_ata'])])
    # Creating up to eight ATAs needs more than the default compute budget.
    tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)],
                                           PAYER.pubkey(), [PAYER],
                                           vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        return {'error': error_name(str(result.err()))}
    # Signed after - before for every watched lamport and token balance.
    delta = [lamports(k) - b for k, b in zip(lamport_keys, before)]
    token_delta = [tokens(k) - b for k, b in zip(token_keys, tokens_before)]
    inner = [i for group in json.loads(result.to_json()).get('inner_instructions') or [] for i in group]
    return {'error': None, 'payer': delta[0], 'vault': delta[1], 'vault_tokens': token_delta[0],
            'holder_tokens': token_delta[1:],
            'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')],
            'self_cpi': [d for d in (flat(i['instruction']['data']) for i in inner) if d.startswith(EVENT_IX_TAG)],
            'return_data': bytes(result.return_data().data)}


def host_line(item):
    n = len(item['holders'])
    holders = ';'.join(f"{h['bps']}:{h['wallet'] if i < item['remaining'] else '-'}:"
                       f"{h['ata'] if n + i < item['remaining'] else '-'}" for i, h in enumerate(item['holders']))
    fields = ['-' if item['vault_tokens'] is None else item['vault_tokens'], int(item['active']), item['creator_fee'],
              int(item['curve_creator'] == 'sharing'), int(item['config_mint'] == 'mint'), int(item['quote'] == 'quote'),
              int(item['initialize_ata']), holders]
    return ','.join(str(f) for f in fields)


def event_payload(item, distributed):
    return (struct.pack('<q', TIMESTAMP) + bytes(MINT) + bytes(CURVE) + bytes(SHARING) + bytes(ADMIN)
            + struct.pack('<I', len(item['holders'])) + shareholders_bytes(item) + struct.pack('<Q', distributed)
            + bytes(QUOTE))


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    H = holder
    add()
    for tokens in (None, 0, 1, 9_999, 10_000, 10**9 + 7, U64 // 10_000, U64 // 10_000 + 1, U64):
        add(vault_tokens=tokens)
    # Account and config checks, and their order.
    add(curve_creator='other')
    add(config_mint='other')
    add(quote='other')
    add(curve_creator='other', config_mint='other', quote='other')
    add(config_mint='other', active=False)
    add(quote='other', active=False)
    add(active=False)
    add(creator_fee=1)
    add(active=False, creator_fee=1)
    add(creator_fee=1, vault_tokens=None)
    add(vault_tokens=None, holders=[H(5000, wallet='wrong')])
    # Per-shareholder checks, in slot order.
    add(holders=[H(5000), H(5000, wallet='wrong')])
    add(holders=[H(5000), H(5000, ata='wrong')])
    add(holders=[H(5000), H(5000, wallet='exec')])
    add(holders=[H(5000), H(5000, wallet='exec', ata='absent')], initialize_ata=True)
    add(holders=[H(5000), H(0)])
    add(holders=[H(0, wallet='wrong')])
    add(holders=[H(0, ata='wrong')])
    add(holders=[H(0, wallet='exec')])
    add(holders=[H(0, ata='absent')])
    add(holders=[H(5000, ata='absent'), H(5000, wallet='wrong')])
    add(holders=[H(2, ata='absent'), H(5000)], vault_tokens=U64 // 2)
    add(holders=[H(5000, ata='absent'), H(2)], vault_tokens=U64 // 2)
    for remaining in range(6):
        add(remaining=remaining)
    add(holders=[])
    # Missing ATAs: rejected without initialize_ata, payer-funded with it.
    add(holders=[H(5000), H(5000, ata='absent')])
    add(holders=[H(5000), H(5000, ata='absent')], initialize_ata=True)
    add(holders=[H(5000, ata='absent'), H(3000, ata='absent'), H(2000, ata='absent')], initialize_ata=True)
    add(holders=[H(1, ata='absent'), H(9_999)], vault_tokens=9_999, initialize_ata=True)
    add(holders=[H(1, ata='absent')] * 8, vault_tokens=0, initialize_ata=True)
    add(initialize_ata=True)
    # Rounding and totals.
    add(holders=[H(10_000)])
    add(holders=[H(1)], vault_tokens=9_999)
    add(holders=[H(3333), H(3333), H(3334)], vault_tokens=10**9 + 7)
    add(holders=[H(1)] * 8, vault_tokens=10**9)
    add(holders=[H(9_999)], vault_tokens=10**9)
    # Shares above 100% run past the vault balance in the token program.
    add(holders=[H(10_001)])
    add(holders=[H(10_000), H(1)], vault_tokens=9_999)
    add(holders=[H(10_000), H(1)], vault_tokens=10_000)
    add(holders=[H(6000), H(5000)])
    add(holders=[H(6000), H(5000, ata='absent')], initialize_ata=True)
    add(holders=[H(65_535), H(65_535)], vault_tokens=10**6)
    return cases


def random_cases(count=60, seed=1781):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        n = rng.randrange(0, 8)
        cut = sorted(rng.sample(range(1, 10_000), n - 1)) if n > 1 else []
        shares = [b - a for a, b in zip([0] + cut, cut + [10_000])] if n else []
        holders = []
        for bps in shares:
            if rng.random() < 0.04:
                bps = rng.choice((0, 10_001, 65_535))
            holders.append(holder(bps, rng.choice(('ok',) * 25 + ('wrong', 'exec')),
                                  rng.choice(('exists',) * 6 + ('absent',) * 3 + ('wrong',))))
        cases.append(case(holders=holders,
                          vault_tokens=rng.choice((None, 0, rng.randrange(0, 10**5), rng.randrange(0, 10**15),
                                                   rng.randrange(0, 10**15))),
                          active=rng.random() < 0.94, creator_fee=0 if rng.random() < 0.94 else rng.randrange(1, 10**6),
                          curve_creator='sharing' if rng.random() < 0.96 else 'other',
                          config_mint='mint' if rng.random() < 0.96 else 'other',
                          quote='quote' if rng.random() < 0.96 else 'other', initialize_ata=rng.random() < 0.6,
                          remaining=2 * n if rng.random() < 0.94 else rng.randrange(0, 2 * n + 1)))
    return cases


class CreatorFeeDistributionQuoteCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'creator-fee-distribution-quote-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def check(self, item, answer):
        self.assert_matches(item, answer, run_captured(item))

    def assert_matches(self, item, answer, captured):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], answer[6:])
            return
        self.assertIsNone(captured['error'])
        fields = answer.split(',')
        distributed, ata_rent = int(fields[1]), int(fields[2])
        transfers = [int(t) for t in fields[3].split(';') if t]
        # Signed after - before: the payer funds new ATAs, the vault token
        # account pays, each shareholder ATA is credited, vault lamports stay.
        self.assertEqual(captured['payer'], -TX_FEE - ata_rent)
        self.assertEqual(captured['vault'], 0)
        self.assertEqual(captured['vault_tokens'], -distributed)
        self.assertEqual(captured['holder_tokens'], transfers)
        payload = event_payload(item, distributed)
        self.assertEqual(captured['return_data'], payload)
        self.assertEqual(captured['events'], [EVENT_DISC['DistributeCreatorFeesEvent'] + payload])
        self.assertEqual(captured['self_cpi'], [EVENT_IX_TAG + EVENT_DISC['DistributeCreatorFeesEvent'] + payload])

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), remaining=item['remaining'], host=answer):
                self.check(item, answer)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_reversed_balance_movements(self):
        # Negative control: a passing captured payout that also creates an ATA
        # must fail once the payer, vault-token or any shareholder delta is reversed.
        item = case(holders=[holder(5000), holder(3000, ata='absent'), holder(2000)], initialize_ata=True)
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(item, answer, captured)
        flips = [dict(captured, payer=-captured['payer']), dict(captured, vault_tokens=-captured['vault_tokens'])]
        for i in range(3):
            holder_tokens = list(captured['holder_tokens'])
            holder_tokens[i] = -holder_tokens[i]
            flips.append(dict(captured, holder_tokens=holder_tokens))
        for flipped in flips:
            with self.subTest(flipped=(flipped['payer'], flipped['vault_tokens'], flipped['holder_tokens'])):
                with self.assertRaises(AssertionError):
                    self.assert_matches(item, answer, flipped)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers},
                         {'ok', 'error:1', 'error:6004', 'error:6024', 'error:6027', 'error:6051', 'error:6052',
                          'error:6053', 'error:6054', 'error:6055', 'error:6070', 'error:6095',
                          'error:invalid_account_data'})
        paid = [a.split(',') for a in answers if a.startswith('ok')]
        self.assertTrue(any(p[2] != '0' and p[1] == '0' for p in paid))  # payer funds ATAs for a zero payout
        self.assertTrue(any(p[2] != '0' and p[1] != '0' for p in paid))
        self.assertTrue(any(p[2] == '0' and p[1] != '0' for p in paid))


if __name__ == '__main__':
    unittest.main()
