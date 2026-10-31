"""Captured-program checks for the pool record of the recovered `create_v2`.

Every case runs Pump `create_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, through the fixture of
`tests/test_create_v2_captured.py`, on a coin quoted by a migrated curve: its
reserves are zero, so the program prices the coin from a synthetic PumpSwap pool
and its two vaults. The same pool shape goes to
`programs/pump/recovered/create_v2_quote_pool_host.rs`, and the error code or
the new curve's virtual quote reserves must agree. This shows matching behavior
on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.instruction import AccountMeta
from solders.pubkey import Pubkey

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_create_v2_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOST_SOURCE = ROOT / 'programs/pump/recovered/create_v2_quote_pool_host.rs'
AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
POOL_DISCRIMINATOR = bytes([241, 154, 109, 4, 17, 177, 109, 188])
BASE_VAULT = Pubkey.from_bytes(bytes([80]) * 32)
QUOTE_VAULT = Pubkey.from_bytes(bytes([81]) * 32)
ELSEWHERE = Pubkey.from_bytes(bytes([82]) * 32)
I128 = 2**127 - 1
U64 = 2**64 - 1
ROOTS = {'sol': base.NATIVE, 'whitelisted': base.WHITELISTED}
DEFAULT_VAULT = dict(owner='token', len=165, state=1, account_type=2, amount=None)
DEFAULT_POOL = dict(tail=4, key_ok=1, owner_ok=1, len=301, discriminator_ok=1, base_key_ok=1, quote_key_ok=1,
                    adjustment=0, extra=0, root='sol')
BASE_AMOUNT, QUOTE_AMOUNT = 2 * 10**14, 8 * 10**10


def pool_case(base_vault=None, quote_vault=None, **changes):
    pool = dict(DEFAULT_POOL, **changes)
    pool['base'] = {**DEFAULT_VAULT, 'amount': BASE_AMOUNT, **(base_vault or {})}
    pool['quote'] = {**DEFAULT_VAULT, 'amount': QUOTE_AMOUNT, **(quote_vault or {})}
    item = base.quoted(vt=0, vq=0, rt=0, rq=0, root=pool['root'])
    item['pool'] = pool
    return item


def seed_of(item):
    root = item['pool']['root']
    if root == 'sol':
        return item['vsr']
    return item['ivqr'] if root == 'whitelisted' else root


def host_line(item):
    p = item['pool']
    vault = lambda v: [int(v['owner'] != 'system'), v['len'], v['state'], v['account_type'], v['amount']]
    return ','.join(map(str, [
        p['tail'], p['key_ok'], p['owner_ok'], p['len'], p['discriminator_ok'], p['base_key_ok'], p['quote_key_ok'],
        *vault(p['base']), *vault(p['quote']), p['adjustment'], item['vtr'], item['rtr'], seed_of(item)]))


def vault_data(v):
    data = bytearray(max(v['len'], 166))
    data[32:64] = bytes(base.USER.pubkey())
    struct.pack_into('<Q', data, 64, v['amount'])
    data[108] = v['state']
    data[165] = v['account_type']
    return bytes(data[:v['len']])


def pool_data(p):
    data = bytearray(max(p['len'], 301))
    data[:8] = POOL_DISCRIMINATOR if p['discriminator_ok'] else bytes(8)
    data[139:171] = bytes(BASE_VAULT)
    data[171:203] = bytes(QUOTE_VAULT)
    data[245:261] = p['adjustment'].to_bytes(16, 'little', signed=True)
    return bytes(data[:p['len']])


def canonical_pool(root):
    mint = base.CONTROLLED
    authority = base.pda(b'pool-authority', bytes(mint))
    quote = ROOTS.get(root, base.ROOT_QUOTE)
    return Pubkey.find_program_address([b'pool', bytes(2), bytes(authority), bytes(mint), bytes(quote)], AMM)[0]


PROGRAMS = {'token': base.TOKEN, 'token22': base.TOKEN22, 'system': base.SYSTEM}
original_setup = base.quote_setup


def quote_setup(vm, item):
    metas = original_setup(vm, item)
    p = item['pool']
    key = canonical_pool(p['root']) if p['key_ok'] else ELSEWHERE
    vm.set_account(key, Account(10**7, pool_data(p), AMM if p['owner_ok'] else base.PUMP))
    base_key = BASE_VAULT if p['base_key_ok'] else ELSEWHERE
    quote_key = QUOTE_VAULT if p['quote_key_ok'] else ELSEWHERE
    vm.set_account(base_key, Account(10**7, vault_data(p['base']), PROGRAMS[p['base']['owner']]))
    vm.set_account(quote_key, Account(10**7, vault_data(p['quote']), PROGRAMS[p['quote']['owner']]))
    tail = [AccountMeta(k, False, False) for k in (key, base_key, quote_key, ELSEWHERE)]
    return metas + tail[:p['tail'] - 1 + p['extra']]


def fixed_cases():
    cases = []
    add = lambda *a, **k: cases.append(pool_case(*a, **k))
    # Priced from the pool, by every root seed, with and without the adjustment.
    add()
    add(root='whitelisted')
    add(root=2_000_000_000)
    add(extra=1)
    add(adjustment=10**9)
    add(adjustment=-10**9)
    add(len=261, adjustment=10**9)
    for length in (211, 212, 244, 245, 260):
        add(len=length, adjustment=10**9)
    add(len=211, adjustment=-I128)
    # Account shape, in the order the program looks.
    for tail in (1, 2, 3):
        add(tail=tail)
    add(key_ok=0)
    add(owner_ok=0)
    add(len=210)
    add(len=139)
    add(len=0)
    add(discriminator_ok=0)
    add(base_key_ok=0)
    add(quote_key_ok=0)
    add(key_ok=0, owner_ok=0)
    add(owner_ok=0, discriminator_ok=0)
    add(tail=3, key_ok=0)
    # Vault shapes, on either vault.
    for side in ('base_vault', 'quote_vault'):
        add(**{side: dict(owner='token22')})
        add(**{side: dict(owner='system')})
        for length, account_type in ((0, 2), (164, 2), (165, 0), (166, 2), (166, 1), (166, 0), (200, 2), (200, 3),
                                     (355, 2), (354, 2), (356, 2)):
            add(**{side: dict(len=length, account_type=account_type)})
        for state in (0, 2, 3):
            add(**{side: dict(state=state)})
    add(base_vault=dict(owner='system'), quote_vault=dict(state=0))
    add(base_key_ok=0, base_vault=dict(owner='system'))
    # Value edges: empty vaults, a negative adjustment, and overflow.
    add(base_vault=dict(amount=0))
    add(quote_vault=dict(amount=0))
    add(quote_vault=dict(amount=0), base_vault=dict(amount=0))
    add(adjustment=-QUOTE_AMOUNT)
    add(adjustment=-QUOTE_AMOUNT - 1)
    add(adjustment=-QUOTE_AMOUNT + 1)
    add(adjustment=I128)
    add(adjustment=-I128)
    add(quote_vault=dict(amount=1), base_vault=dict(amount=U64))
    add(base_vault=dict(amount=U64), quote_vault=dict(amount=U64))
    add(base_vault=dict(amount=U64))
    add(base_vault=dict(amount=1))
    add(base_vault=dict(amount=2))
    add(base_vault=dict(amount=1), quote_vault=dict(amount=U64))
    return cases


def random_cases(count=60, seed=159):
    rng = random.Random(seed)
    cases = []
    amount = lambda: rng.choice((0, 1, rng.randrange(1, 10**6), rng.randrange(1, 10**14), rng.randrange(1, U64)))
    for _ in range(count):
        pool = dict(root=rng.choice(('sol', 'whitelisted', rng.randrange(1, 10**12))), len=rng.choice((211, 260, 261, 301)),
                    adjustment=rng.choice((0, rng.randrange(-10**12, 10**12), rng.randrange(-I128, I128))),
                    tail=rng.choice((4, 4, 4, 3)), key_ok=int(rng.random() < 0.95), owner_ok=int(rng.random() < 0.95))
        vault = lambda: dict(amount=amount(), owner=rng.choice(('token', 'token', 'token22', 'system')),
                             len=rng.choice((165, 165, 166, 200, 355)), account_type=rng.choice((2, 2, 1)),
                             state=rng.choice((1, 1, 1, 0)))
        cases.append(pool_case(vault(), vault(), **pool))
    return cases


class CreateV2QuotePoolCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in base.ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'create-v2-quote-pool-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.patch = mock.patch.object(base, 'quote_setup', quote_setup)
        cls.patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, answer, captured):
        if answer.startswith('error:'):
            code = re.search(r'Custom\((\d+)\)', str(captured['error']))
            self.assertEqual(int(code.group(1)) if code else captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        reserves = int(answer.split(',')[1])
        curve = bytes(captured['curve'].data)
        self.assertEqual(struct.unpack_from('<Q', curve, 16)[0], reserves)
        self.assertEqual(struct.unpack_from('<Q', curve, 142)[0], reserves)
        self.assertEqual(curve[141], 1)
        self.assertEqual(curve[83:115], bytes(base.CONTROLLED))

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(answer, base.run_captured(item))
        return answers

    def test_fixed_cases_match_captured_program(self):
        answers = self.run_cases(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers},
                         {'ok', 'error:6024', 'error:6026', 'error:6101', 'error:6102', 'error:6103', 'error:6104'})

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_adjustment_changes_the_price(self):
        # Negative control: the checker must see the adjustment the pool stores.
        plain, adjusted = pool_case(), pool_case(adjustment=10**10)
        self.assertNotEqual(*self.host_answers([plain, adjusted]))
        with self.assertRaises(AssertionError):
            self.assert_matches(self.host_answers([plain])[0], base.run_captured(adjusted))


if __name__ == '__main__':
    unittest.main()
