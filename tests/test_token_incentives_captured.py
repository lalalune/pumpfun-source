"""Captured-program checks for the recovered token-incentive day rollover and claim.

Every case runs Pump `claim_token_incentives` or `sync_user_volume_accumulator`
from the captured `evidence/original/pump/deployed.so` on LiteSVM, with the
captured SPL Token and Associated Token programs, against a synthetic
GlobalVolumeAccumulator schedule and UserVolumeAccumulator. The same inputs go
to `programs/pump/recovered/token_incentives_host.rs`, and the error or panic,
tokens transferred, stored user accumulator, and emitted event must agree.
This shows matching behavior on these inputs only; it is not a byte-identity
claim.
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
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/token_incentives_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}

PAYER = Keypair.from_seed(bytes([211]) * 32)
USER = Pubkey.from_bytes(bytes([21]) * 32)  # not a signer on either instruction
MINT = Pubkey.from_bytes(bytes([22]) * 32)


def pda(*seeds):
    return Pubkey.find_program_address(list(seeds), PUMP)[0]


GLOBAL_VOLUME = pda(b'global_volume_accumulator')
USER_VOLUME = pda(b'user_volume_accumulator', bytes(USER))
EVENT_AUTHORITY = pda(b'__event_authority')
TOKEN_RENT = 2_039_280
U64 = 2**64 - 1
I64 = 2**63 - 1
DAY = 86_400
START = 1_700_000_000


def ata(owner):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(MINT)], ATA)[0]


def mint_data():
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', U64) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(owner, amount):
    return (bytes(MINT) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def global_volume_data(item):
    supply, volumes = [0] * 30, [0] * 30
    for index, token_supply, sol_volume in item['days']:
        supply[index], volumes[index] = token_supply, sol_volume
    return (ACCOUNT_DISC['GlobalVolumeAccumulator'] + struct.pack('<qqq', item['start'], item['end'], item['secs'])
            + bytes(MINT) + struct.pack('<30Q', *supply) + struct.pack('<30Q', *volumes))


USER_FIELDS = ('needs_claim', 'unclaimed', 'claimed', 'volume', 'last_update', 'has_claimed')


def user_volume_data(item):
    data = bytearray(137)
    data[:8] = ACCOUNT_DISC['UserVolumeAccumulator']
    data[8:40] = bytes(USER)
    struct.pack_into('<?QQQq?', data, 40, *(item[k] for k in USER_FIELDS))
    struct.pack_into('<Q', data, 74, 999)  # cashback_earned: must be left alone
    return bytes(data)


def read_user(data):
    assert data[8:40] == bytes(USER) and struct.unpack_from('<Q', data, 74)[0] == 999
    values = struct.unpack_from('<?QQQq?', data, 40)
    return dict(zip(USER_FIELDS, (int(v) if isinstance(v, bool) else v for v in values)))


DEFAULTS = dict(op='claim', now=START + 3 * DAY + 5, start=START, end=START + 20 * DAY, secs=DAY, vault=10**15,
                user_ata=True, needs_claim=True, unclaimed=0, claimed=0, volume=7 * 10**9,
                last_update=START + DAY + 9, has_claimed=False, days=((1, 10**12, 3 * 10**10),))


def case(**changes):
    return dict(DEFAULTS, **changes)


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(ATA, ATA_ELF)
    vm.set_clock(Clock(100, item['now'], 0, 0, item['now']))
    accounts = {
        PAYER.pubkey(): Account(10**12, b'', SYSTEM),
        MINT: Account(10**9, mint_data(), TOKEN),
        GLOBAL_VOLUME: Account(10**9, global_volume_data(item), PUMP),
        ata(GLOBAL_VOLUME): Account(TOKEN_RENT, token_data(GLOBAL_VOLUME, item['vault']), TOKEN),
        USER_VOLUME: Account(10**9, user_volume_data(item), PUMP),
    }
    if item['user_ata']:
        accounts[ata(USER)] = Account(TOKEN_RENT, token_data(USER, 0), TOKEN)
    for key, account in accounts.items():
        vm.set_account(key, account)
    names = {
        'user': USER, 'user_ata': ata(USER), 'global_volume_accumulator': GLOBAL_VOLUME,
        'global_incentive_token_account': ata(GLOBAL_VOLUME), 'user_volume_accumulator': USER_VOLUME, 'mint': MINT,
        'token_program': TOKEN, 'system_program': SYSTEM, 'associated_token_program': ATA,
        'event_authority': EVENT_AUTHORITY, 'program': PUMP, 'payer': PAYER.pubkey(),
    }
    ix = IX['claim_token_incentives' if item['op'] == 'claim' else 'sync_user_volume_accumulator']
    metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(ix['discriminator']), metas)], PAYER.pubkey(),
                                           [PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    balance = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0] if vm.get_account(key) else None
    return {'error': None, 'events': events, 'user': read_user(vm.get_account(USER_VOLUME).data),
            'tokens': (balance(ata(GLOBAL_VOLUME)), balance(ata(USER)))}


def host_line(item):
    fields = [item['op'], item['now'], item['start'], item['end'], item['secs'], item['vault'],
              int(item['needs_claim']), item['unclaimed'], item['claimed'], item['volume'], item['last_update'],
              int(item['has_claimed']), ';'.join(f'{d}:{s}:{v}' for d, s, v in item['days'])]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    day1 = START + DAY + 9
    # Rollover of the last-updated day into unclaimed tokens, then the claim.
    add()
    add(unclaimed=5, claimed=11, has_claimed=True)
    add(volume=1, days=((1, 10, 3),))
    add(volume=2, days=((1, 10, 3),))
    add(now=START + 25 * DAY, end=START + 29 * DAY + 1)
    add(now=START + 2 * DAY, last_update=START + 2 * DAY - 1)
    add(now=START + 2 * DAY - 1, last_update=START + DAY)
    # No conversion: same day, empty day bucket, or no user volume.
    add(now=START + DAY + 100)
    add(now=START + DAY + 100, unclaimed=40)
    add(days=())
    add(days=(), unclaimed=40)
    add(volume=0)
    add(volume=0, unclaimed=40, needs_claim=False)
    add(days=((1, 0, 3 * 10**10),))
    add(days=((1, 1, 3 * 10**10),))
    add(needs_claim=False, volume=0, days=())
    # Schedule edges: before start, after end, last update past the end day.
    add(now=START - 1, last_update=START - 10, unclaimed=40, claimed=50, has_claimed=True)
    add(now=START - 1, last_update=START - 10, claimed=50, has_claimed=True)
    add(now=START - 1, last_update=START, claimed=50, has_claimed=True)
    add(now=START + 2 * DAY, last_update=START - 10, unclaimed=40)
    add(now=START + 20 * DAY, end=START + 20 * DAY)
    add(now=START + 20 * DAY + 1, end=START + 20 * DAY)
    for now in (START + 20 * DAY + 5, START + 20 * DAY + 6):  # same-day stamp only while now <= end
        add(now=now, end=START + 20 * DAY + 5, last_update=START + 20 * DAY + 1, needs_claim=False, volume=5)
    add(now=START + 25 * DAY, end=START + 5 * DAY)
    add(now=START + 25 * DAY, end=START + DAY)
    add(now=START + 25 * DAY, end=START + DAY - 1, unclaimed=40)
    add(now=START + 25 * DAY, last_update=START + 21 * DAY, end=START + 20 * DAY, days=((21, 10**12, 3 * 10**10),))
    add(secs=0, unclaimed=40)
    # A rollover worth 0 tokens past the end clears needs_claim (no stamp afterwards).
    add(now=START + 25 * DAY, end=START + 20 * DAY, unclaimed=0, needs_claim=True, days=((1, 0, 3 * 10**10),))
    add(now=START + 25 * DAY, end=START + 20 * DAY, unclaimed=0, needs_claim=True, days=((1, 1, 3 * 10**10),))
    add(secs=1, now=START + 29, last_update=START + 3, days=((3, 1000, 7),), volume=5)
    # Panics and errors.
    add(end=START - 1)
    # The stamp indexes the current day: day 29 is fine, day 30 panics.
    for now in (START + 30 * DAY - 1, START + 30 * DAY):
        add(now=now, end=START + 40 * DAY, last_update=now - 1)
    add(now=START + 31 * DAY, end=START + 40 * DAY)
    add(now=START + 31 * DAY, end=START + 40 * DAY, volume=0)
    add(now=START + 31 * DAY, end=START + 30 * DAY)
    add(now=START + 32 * DAY, end=START + 40 * DAY, last_update=START + 30 * DAY + 1)
    add(last_update=-1)
    add(start=-1, end=10)
    add(volume=U64, days=((1, U64, 1),))
    add(volume=U64, days=((1, U64, U64),))
    add(volume=2, days=((1, U64, 2),))
    add(unclaimed=U64, volume=1, days=((1, 1, 1),))
    add(unclaimed=U64 - 233_333_333_333)
    add(claimed=U64 - 233_333_333_332)
    add(claimed=U64 - 233_333_333_333)
    add(vault=233_333_333_332)
    add(vault=233_333_333_333)
    add(user_ata=False)
    add(user_ata=False, volume=0)
    # sync_user_volume_accumulator: only the pre-start reset.
    for claimed, has in ((50, True), (0, False), (0, True)):
        add(op='sync', now=START - 1, last_update=START - 10, claimed=claimed, has_claimed=has)
    add(op='sync', now=START - 1, last_update=START, claimed=50, has_claimed=True)
    add(op='sync', now=START, last_update=START - 10, claimed=50, has_claimed=True)
    add(op='sync', claimed=50, has_claimed=True, unclaimed=9)
    add(op='sync', now=START - 1, last_update=-5, claimed=50, has_claimed=True)
    return cases


def random_cases(count=80, seed=1850):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        secs = rng.choice((DAY, DAY, 3_600, rng.randrange(1, 10**6), 0))
        span = rng.randrange(1, 35)
        end = START + rng.choice((span * secs, span * secs + rng.randrange(0, max(secs, 1)), -rng.randrange(1, 100)))
        last_day = rng.randrange(0, 32)
        last_update = START + last_day * secs + rng.randrange(0, max(secs, 1)) + rng.choice((0, 0, -rng.randrange(1, 10**6)))
        now = max(last_update, START - 10**5) + rng.choice((0, rng.randrange(0, 3 * max(secs, 1)), rng.randrange(0, 40 * max(secs, 1))))
        days = tuple((d, rng.choice((0, rng.randrange(1, 10**12), rng.randrange(1, 2**64))),
                      rng.choice((0, rng.randrange(1, 10**12), rng.randrange(1, 2**64))))
                     for d in sorted(rng.sample(range(30), rng.randrange(0, 6))) )
        if rng.random() < 0.6 and last_day < 30:
            days += ((last_day, rng.randrange(1, 10**13), rng.randrange(1, 10**12)),)
            days = tuple(sorted({d[0]: d for d in days}.values()))
        cases.append(case(op=rng.choice(('claim', 'claim', 'claim', 'sync')), now=now, end=end, secs=secs,
                          vault=rng.choice((10**15, rng.randrange(0, 10**12))), user_ata=rng.random() < 0.8,
                          needs_claim=rng.random() < 0.5, unclaimed=rng.choice((0, rng.randrange(0, 10**12))),
                          claimed=rng.choice((0, rng.randrange(0, 10**12))), volume=rng.choice((0, rng.randrange(0, 10**12))),
                          last_update=last_update, has_claimed=rng.random() < 0.5, days=days))
    return cases


def decode_event(data):
    name = next(n for n, d in EVENT_DISC.items() if data[:8] == d)
    if name == 'ClaimTokenIncentivesEvent':
        assert data[8:40] == bytes(USER) and data[40:72] == bytes(MINT)
        return (name, *struct.unpack_from('<QqQQ', data, 72))
    assert name == 'SyncUserVolumeAccumulatorEvent' and data[8:40] == bytes(USER)
    return (name, *struct.unpack_from('<QQq', data, 40))


class TokenIncentivesCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'token-incentives-host'
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
        if answer == 'panic':
            self.assertIn('ProgramFailedToComplete', str(captured['error']))
            return
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        first, *fields = map(int, answer.split(',')[1:])
        user = dict(zip(USER_FIELDS, fields))
        self.assertEqual(captured['user'], user)
        events = [decode_event(e) for e in captured['events']]
        if item['op'] == 'claim':
            # init_if_needed creates a missing user ATA even when nothing is claimed.
            self.assertEqual(captured['tokens'], (item['vault'] - first, first))
            expected = [('ClaimTokenIncentivesEvent', first, item['now'], user['claimed'], user['volume'])] if first else []
        else:
            self.assertEqual(captured['tokens'], (item['vault'], 0 if item['user_ata'] else None))
            changed = first != user['claimed']
            expected = [('SyncUserVolumeAccumulatorEvent', first, user['claimed'], item['now'])] if changed else []
        self.assertEqual(events, expected)

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.check(item, answer)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_claims(self):
        # Negative control: a passing captured claim must fail once the token
        # movement is reversed (vault credited instead of debited) or the
        # stored claimed total or the event amount is off by one.
        item = case()
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(item, answer, captured)
        vault, user_ata = captured['tokens']
        moved = item['vault'] - vault
        self.assertGreater(moved, 0)
        tampered = {
            'reversed': dict(captured, tokens=(item['vault'] + moved, user_ata)),
            'claimed': dict(captured, user=dict(captured['user'], claimed=captured['user']['claimed'] + 1)),
            'event': dict(captured, events=[e[:72] + struct.pack('<Q', moved - 1) + e[80:] for e in captured['events']]),
        }
        for name, bad in tampered.items():
            with self.subTest(tampered=name):
                with self.assertRaises(AssertionError):
                    self.assert_matches(item, answer, bad)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {'ok', 'panic', 'error:1', 'error:6025'})


if __name__ == '__main__':
    unittest.main()
