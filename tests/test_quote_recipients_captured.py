"""Captured-program checks for recipient admission on token quote trades.

Every case runs `sell_v2`, `buy_v2`, or `buy_exact_quote_in_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, through the fixture of
`tests/test_v2_token_quote_captured.py`, with synthetic `Global` key lists and a
chosen fee recipient, buyback recipient, and pair of quote token accounts. The
same inputs go to `programs/pump/recovered/quote_recipients_host.rs`, and the
error, the recipients paid, and the accounts created must agree. Trade amounts
are not re-modelled here. This shows matching behavior on these inputs only; it
is not a byte-identity claim.
"""
from pathlib import Path
import collections
import hashlib
import itertools
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.pubkey import Pubkey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_v2_token_quote_captured as base  # noqa: E402

ELF_SHA256 = {base.PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
              base.FEES_ELF: '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
              base.TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
              base.TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
              base.ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/quote_recipients_host.rs'


def key(n):
    return bytes([n]) * 32


ZERO = bytes(32)
FEE, RESERVED = key(201), key(202)
FEE_LIST = [key(40 + i) for i in range(7)]  # sorted
RESERVED_LIST = [key(90 - i) for i in range(7)]  # searched linearly
BUYBACK_LIST = [key(120 + i) for i in range(8)]
OUTSIDER = key(77)
QUOTES = ('wsol', 'usdc', 'spl', 't22')
OPS = base.OPS


def case(op='sell', quote='spl', whitelisted=0, mayhem=0, fee=FEE, buyback=BUYBACK_LIST[0], fee_list=FEE_LIST,
         reserved_list=RESERVED_LIST, buyback_list=BUYBACK_LIST, fee_account='present', buyback_account='present',
         buyback_bps=5_000):
    return dict(op=op, quote=quote, whitelisted=whitelisted, mayhem=mayhem, fee=fee, buyback=buyback, fee_list=fee_list,
                reserved_list=reserved_list, buyback_list=buyback_list, fee_account=fee_account,
                buyback_account=buyback_account, buyback_bps=buyback_bps)


def host_line(c):
    return ','.join([str(c['whitelisted']), str(c['mayhem']), str(c['buyback_bps']), c['fee_account'], c['buyback_account'],
                     FEE.hex(), b''.join(c['fee_list']).hex(), RESERVED.hex(), b''.join(c['reserved_list']).hex(),
                     b''.join(c['buyback_list']).hex(), c['fee'].hex(), c['buyback'].hex()])


def run_captured(c):
    """Pass `fee` and `buyback` through the base fixture's recipient slots."""
    original = base.global_bytes

    def global_bytes(fixture):
        data = bytearray(original(fixture))
        data[41:73] = FEE
        data[483:515] = RESERVED
        data[162:386] = b''.join(c['fee_list'])
        data[516:740] = b''.join(c['reserved_list'])
        data[741:997] = b''.join(c['buyback_list'])
        return bytes(data)

    fee, buyback = Pubkey.from_bytes(c['fee']), Pubkey.from_bytes(c['buyback'])
    missing = tuple(name for name, state in (('recipient', c['fee_account']), ('buyback', c['buyback_account']))
                    if state == 'absent')
    bad = {'fee': 'recipient_key', 'buyback': 'buyback_key'}.get(
        'fee' if c['fee_account'] == 'wrong' else 'buyback' if c['buyback_account'] == 'wrong' else '', 'none')
    fixture = base.default_case(op=c['op'], quote=c['quote'], whitelisted=c['whitelisted'], mayhem=c['mayhem'],
                                buyback_bps=c['buyback_bps'], missing=missing, bad=bad,
                                supply=2 * 10**15 if c['mayhem'] else 10**15)
    with mock.patch.multiple(base, global_bytes=global_bytes, FEE_RECIPIENT=fee, RESERVED=fee, BUYBACK=buyback):
        result = base.run_captured(fixture)
    base._TOUCHED.discard(base.SYSTEM)  # the zero key is the system program
    mint, program = base.QUOTES[c['quote']][:2]
    fee_ata, buyback_ata = base.ata(fee, mint, program), base.ata(buyback, mint, program)

    def balance(snapshot, account):
        return base.token_amount(snapshot[account][1]) if snapshot.get(account) else 0

    before, after = result['before'], result['after']
    return dict(error=result['error'],
                fee_paid=balance(after, fee_ata) > balance(before, fee_ata),
                buyback_paid=balance(after, buyback_ata) > balance(before, buyback_ata),
                fee_created=before[fee_ata] is None and after[fee_ata] is not None,
                buyback_created=before[buyback_ata] is None and after[buyback_ata] is not None,
                same_key=fee == buyback)


def keys_for(mayhem):
    """Fee keys, buyback keys to try on one route."""
    good = [RESERVED, RESERVED_LIST[0], RESERVED_LIST[6]] if mayhem else [FEE, FEE_LIST[0], FEE_LIST[3], FEE_LIST[6]]
    wrong = [FEE, FEE_LIST[3]] if mayhem else [RESERVED, RESERVED_LIST[2]]
    return good + wrong + [BUYBACK_LIST[1], OUTSIDER, ZERO], [BUYBACK_LIST[0], BUYBACK_LIST[7], FEE, OUTSIDER, ZERO]


def fixed_cases():
    cases = []
    for op, quote, whitelisted, mayhem in itertools.product(OPS, QUOTES, (0, 1), (0, 1)):
        add = lambda **k: cases.append(case(op=op, quote=quote, whitelisted=whitelisted, mayhem=mayhem, **k))
        fees, buybacks = keys_for(mayhem)
        for slot in fees:
            add(fee=slot)
        for slot in buybacks:
            add(buyback=slot)
        add(fee=OUTSIDER, buyback=OUTSIDER)
        add(fee=OUTSIDER, buyback=ZERO)
        good = RESERVED if mayhem else FEE
        for fee_account, buyback_account, buyback_bps in itertools.product(('present', 'absent', 'wrong'), ('present', 'absent', 'wrong'), (5_000, 0)):
            add(fee=good, fee_account=fee_account, buyback_account=buyback_account, buyback_bps=buyback_bps)
            add(fee=OUTSIDER, fee_account=fee_account, buyback_account=buyback_account, buyback_bps=buyback_bps)
            add(fee=good, buyback=OUTSIDER, fee_account=fee_account, buyback_account=buyback_account, buyback_bps=buyback_bps)
        add(fee=good, buyback=ZERO, fee_account='absent', buyback_account='absent')
        # Lists a program-written Global would not hold.
        add(fee=FEE_LIST[1], fee_list=list(reversed(FEE_LIST)))
        add(fee=FEE_LIST[3], fee_list=list(reversed(FEE_LIST)))
        add(fee=FEE_LIST[6], fee_list=FEE_LIST[1:] + FEE_LIST[:1])
        add(fee=RESERVED_LIST[6], reserved_list=list(reversed(RESERVED_LIST)))
        add(fee=key(0x80), fee_list=[key(0x10), key(0x20), key(0x30), key(0x80), key(0x90), key(0xA0), key(0xB0)])
        add(fee=ZERO, fee_list=[ZERO] + FEE_LIST[:6])
        add(fee=ZERO, reserved_list=[ZERO] + RESERVED_LIST[:6])
        add(buyback=ZERO, buyback_list=[ZERO] + BUYBACK_LIST[1:])
    return cases


def random_cases(count=20, seed=736):
    rng = random.Random(seed)
    cases = []
    for op, quote, whitelisted, mayhem in itertools.product(OPS, QUOTES, (0, 1), (0, 1)):
        for _ in range(count):
            fee_list = rng.sample(range(1, 200), 7)
            fee_list = [key(n) for n in (sorted(fee_list) if rng.random() < 0.5 else fee_list)]
            reserved_list = [key(n) for n in rng.sample(range(1, 200), 7)]
            buyback_list = [key(n) for n in rng.sample(range(1, 200), 8)]
            pool = fee_list + reserved_list + buyback_list + [FEE, RESERVED, OUTSIDER]
            fee, buyback = rng.choice(pool), rng.choice(buyback_list + [OUTSIDER, ZERO])
            accounts = [rng.choice(('present', 'present', 'absent', 'wrong')) for _ in range(2)]
            if fee == buyback:
                accounts[1] = accounts[0]  # one key has one token account
            cases.append(case(op, quote, whitelisted, mayhem, fee, buyback, fee_list, reserved_list, buyback_list,
                              *accounts, rng.choice((5_000, 5_000, 0))))
    return cases


class QuoteRecipientsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'quote-recipients-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(c) + '\n' for c in cases)
        return subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()

    def check(self, answer, got):
        if answer.startswith('error:'):
            self.assertEqual(got['error'], int(answer[6:]))
            return answer[6:]
        self.assertIsNone(got['error'])
        fee_paid, buyback_paid, fee_created, buyback_created = (flag == '1' for flag in answer.split(',')[1:])
        if not got['same_key']:
            self.assertEqual(got['fee_paid'], fee_paid)
            self.assertEqual(got['buyback_paid'], buyback_paid)
        self.assertEqual(got['fee_created'], fee_created)
        self.assertEqual(got['buyback_created'], buyback_created)
        return 'ok'

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        outcomes = collections.Counter()
        for c, answer in zip(cases, answers):
            with self.subTest(op=c['op'], quote=c['quote'], wl=c['whitelisted'], mayhem=c['mayhem'], fee=c['fee'][:2].hex(),
                              buyback=c['buyback'][:2].hex(), accounts=(c['fee_account'], c['buyback_account']),
                              bps=c['buyback_bps'], host=answer):
                outcomes[self.check(answer, run_captured(c))] += 1
        return outcomes

    def test_fixed_cases_match_captured_program(self):
        outcomes = self.run_cases(fixed_cases())
        self.assertEqual(set(outcomes), {'ok', '2006', '6000', '6057', '6062'})

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_unsorted_list_refuses_a_member(self):
        # Negative control: a linear scan would admit this key.
        c = case(fee=FEE_LIST[1], fee_list=list(reversed(FEE_LIST)))
        self.assertEqual(run_captured(c)['error'], 6000)
        self.assertEqual(self.host_answers([c]), ['error:6000'])

    def test_checker_rejects_wrong_answers(self):
        got = run_captured(case())
        self.check('ok,1,1,0,0', got)
        for wrong in ('ok,0,1,0,0', 'ok,1,0,0,0', 'ok,1,1,1,0', 'error:6000'):
            with self.assertRaises(AssertionError):
                self.check(wrong, got)


if __name__ == '__main__':
    unittest.main()
