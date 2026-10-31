"""Captured-program checks for the `sharing_config` read of the v2 trades.

Every case runs `sell_v2`, `buy_v2` or `buy_exact_quote_in_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, on the fixtures of
`tests/test_v2_token_quote_captured.py`, with chosen bytes in the sharing-config
account, and then the same trade with no such account. The bytes also go to
`programs/pump/recovered/trade_shareholders_host.rs`.

A passing answer must equal the twin run in every stored account, and in the
TradeEvent and CompleteEvent bytes of the log and the `emit_cpi!` self-call once
the host's shareholder list replaces the twin's empty one. No pricing is
modelled here. State is synthetic, and this pins observed behavior on these
inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_v2_token_quote_captured as base  # noqa: E402

from solders.account import Account  # noqa: E402
from solders.pubkey import Pubkey  # noqa: E402

PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
FEES_ELF = ROOT / 'evidence/original/pump_fees/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    FEES_ELF: '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/trade_shareholders_host.rs'
DISC = base.ACCOUNT_DISC['SharingConfig']
FEES, PUMP, SYSTEM, TOKEN = base.FEES, base.PUMP, base.SYSTEM, base.TOKEN
TX_FEE = base.TX_FEE
FUNDED = base.rent(166) + 6_000_000_000  # a native sell pays out of the curve
OOM_LOG = 'memory allocation failed'

# route -> (op, family, largest list, trade fixture)
MAYHEM = dict(whitelisted=1, mayhem=1)
ROUTES = {
    'token-sell': ('sell', 'token', 56, dict(quote='spl')),
    'token-buy': ('buy', 'token', 51, dict(quote='spl')),
    'token-exact': ('exact', 'token', 50, dict(quote='spl')),
    'usdc-sell': ('sell', 'token', 56, dict(quote='usdc')),
    'usdc-buy': ('buy', 'token', 51, dict(quote='usdc')),
    'usdc-exact': ('exact', 'token', 50, dict(quote='usdc')),
    'wsol-sell': ('sell', 'token', 56, dict(quote='wsol')),
    'wsol-buy': ('buy', 'token', 51, dict(quote='wsol')),
    'wsol-exact': ('exact', 'token', 50, dict(quote='wsol')),
    't22-sell': ('sell', 't22', 55, dict(quote='t22')),
    't22-buy': ('buy', 't22', 50, dict(quote='t22')),
    't22-exact': ('exact', 't22', 50, dict(quote='t22')),
    'native-sell': ('sell', 'native', 66, dict(quote='wsol', native=1, curve_lamports=FUNDED)),
    'native-buy': ('buy', 'native', 56, dict(quote='wsol', native=1)),
    'native-exact': ('exact', 'native', 55, dict(quote='wsol', native=1)),
    'wl-sell': ('sell', 'wl', 71, dict(quote='spl', **MAYHEM)),
    'wl-buy': ('buy', 'wl', 66, dict(quote='spl', **MAYHEM)),
    'wl-exact': ('exact', 'wl', 66, dict(quote='spl', **MAYHEM)),
    'wl-native-sell': ('sell', 'wl_native', 74, dict(quote='wsol', native=1, curve_lamports=FUNDED, **MAYHEM)),
    'wl-native-buy': ('buy', 'wl_native', 66, dict(quote='wsol', native=1, **MAYHEM)),
    'wl-native-exact': ('exact', 'wl_native', 66, dict(quote='wsol', native=1, **MAYHEM)),
    'complete-buy': ('buy', 'token', 48, dict(quote='spl', rtr=10**9, amount=10**9)),
}
FAILING = {'sell': dict(limit=2**63), 'buy': dict(limit=1), 'exact': dict(limit=2**63)}


def config(rows=2, count=None, status=1, version=1, bump=255, revoked=0, mint=None, admin=bytes([7]) * 32, tail=b'',
           disc=DISC, row=None):
    data = disc + bytes([bump, version, status]) + bytes(base.BASE if mint is None else mint) + admin + bytes([revoked])
    data += struct.pack('<I', rows if count is None else count)
    for i in range(rows):
        data += row(i) if row else bytes([1 + i % 200]) * 32 + struct.pack('<H', 1000 + i)
    return data + tail


def case(route, data=None, owner=FEES, lamports=10**9, key_ok=True, failing=False):
    return dict(route=route, data=data, owner=owner, lamports=lamports, key_ok=key_ok, failing=failing)


def host_line(c):
    op, family, _, fixture = ROUTES[c['route']]
    hexed = c['data'].hex() if c['data'] else '-'
    return f"{op} {family} {int('rtr' in fixture)} {int(c['key_ok'])} {int(c['failing'])} {hexed}"


class Runner:
    def __init__(self):
        self.share = None
        self.twins = {}
        self.fresh_vm = base.fresh_vm
        self.curve_bytes = base.curve_bytes

    def vm(self):
        vm = self.fresh_vm()
        base._TOUCHED.add(base.SHARING)
        if self.share is not None:
            vm.set_account(base.SHARING, self.share)
        return vm

    def curve(self, c, quote_mint):
        data = bytearray(self.curve_bytes(c, quote_mint))
        if c.get('native'):
            data[83:115] = bytes(32)
        return bytes(data)

    def trade(self, c, share):
        op, _, _, fixture = ROUTES[c['route']]
        item = base.default_case(op=op, **fixture, **(FAILING[op] if c['failing'] else {}))
        self.share = share
        with mock.patch.multiple(base, fresh_vm=self.vm, curve_bytes=self.curve):
            return base.run_captured(item)

    def run(self, c):
        twin_key = (c['route'], c['failing'])
        if twin_key not in self.twins:
            self.twins[twin_key] = self.trade(c, None)
        share = None if c['data'] is None else Account(c['lamports'], c['data'], c['owner'])
        if c['key_ok']:
            got = self.trade(c, share)
        else:
            with mock.patch.object(base, 'SHARING', Pubkey.from_bytes(bytes([99]) * 32)):
                got = self.trade(c, share)
        stored = base._VM.get_account(base.SHARING)
        got['sharing'] = None if stored is None or stored.lamports == 0 else (bytes(stored.data), stored.owner)
        return got, self.twins[twin_key]


def list_at(event):
    """Offset of `shareholders`: past `ix_name`, `mayhem_mode` and four u64 fields."""
    at = 258
    return at + 4 + struct.unpack_from('<I', event, at)[0] + 1 + 32


def splice(event, listed):
    if event[:8] != base.EVENT_DISC['TradeEvent']:
        return event
    at = list_at(event)
    assert event[at:at + 4] == bytes(4)
    return event[:at] + listed + event[at + 4:]


def splice_cpi(data, listed):
    return data[:8] + splice(data[8:], listed)


def rollback_only(got):
    user = base.USER.pubkey()
    before, after = dict(got['before']), dict(got['after'])
    lamports, data, owner = before[user]
    before[user] = (lamports - TX_FEE, data, owner)
    return before == after


def verdict(c, answer, got, twin):
    """None when the captured run agrees with the host's answer, else a reason."""
    if c['key_ok'] and c['data'] and got['sharing'] != (c['data'], c['owner']):
        return 'config changed'
    word, _, rest = answer.partition(' ')
    if word == 'refused':
        return None if got['error'] == int(rest) else f"error {got['error']}"
    if word == 'trade_failed':
        return None if twin['error'] is not None and got['error'] == twin['error'] else f"error {got['error']}"
    if word == 'oom':
        if got['error'] != 'panic' or not any(OOM_LOG in line for line in got['logs']):
            return f"error {got['error']}"
        return None if rollback_only(got) else 'state moved'
    if twin['error'] is not None or got['error'] is not None:
        return f"error {got['error']} twin {twin['error']}"
    listed = bytes.fromhex(rest)
    if got['after'] != twin['after'] or got['before'] != twin['before']:
        return 'state differs'
    if got['events'] != [splice(e, listed) for e in twin['events']]:
        return 'log event differs'
    if got['cpi'] != [splice_cpi(e, listed) for e in twin['cpi']]:
        return 'cpi event differs'
    return None


def shape_cases():
    two = config()
    shapes = [None, b'', two, config(0), config(1), config(10), config(rows=2, tail=b'\xff' * 50),
              config(rows=2, tail=bytes(5000)), config(rows=2, count=1), config(rows=2, count=0), config(rows=2, count=3),
              config(rows=1, count=2, tail=bytes(33)), config(rows=1, count=2, tail=bytes(34)),
              config(rows=2, count=2**31), config(rows=2, count=2**32 - 1), config(rows=0, count=2**32 - 1),
              config(rows=200, count=300), config(rows=500, count=1000), config(mint=bytes(32)), config(mint=bytes([9]) * 32),
              config(admin=bytes(32)), config(rows=3, row=lambda i: bytes(32) + struct.pack('<H', 65_535)),
              config(rows=3, row=lambda i: bytes([5]) * 32 + struct.pack('<H', 0)), config(disc=bytes(8)),
              DISC, DISC + bytes(100), bytes(200)]
    shapes += [config(status=v) for v in (0, 1, 2, 3, 127, 128, 255)]
    shapes += [config(version=v) for v in (0, 2, 255)]
    shapes += [config(bump=v) for v in (0, 1)]
    shapes += [config(revoked=v) for v in (0, 1, 2, 3, 255)]
    shapes += [two[:i] + bytes([two[i] ^ 0x40]) + two[i + 1:] for i in range(8)]
    shapes += [two[:n] for n in range(len(two))]
    cases = [case(r, s) for s in shapes for r in ('token-sell', 'token-buy', 'token-exact')]
    for owner in (SYSTEM, PUMP, TOKEN, Pubkey.from_bytes(bytes([44]) * 32)):
        cases += [case(r, two, owner=owner) for r in ('token-sell', 'native-buy', 'wl-exact')]
    cases += [case('token-buy', two, lamports=v) for v in (1, 10**13)]
    return cases


def route_cases():
    cases = []
    for route, (_, _, limit, _) in ROUTES.items():
        for rows in (0, 1, 2, 10, limit - 1, limit, limit + 1, limit + 2, 120, 200):
            cases.append(case(route, config(rows)))
        cases += [case(route, config(rows=limit + 1, count=limit + 2)), case(route, config(rows=500, count=501)),
                  case(route, config(rows=240, count=241)), case(route, config(rows=241, count=242)),
                  case(route, config(rows=240, count=2**32 - 1)), case(route, config(rows=241, count=2**32 - 1)),
                  case(route, config(rows=240, count=241, tail=bytes(33))), case(route, config(rows=241, count=241)),
                  case(route, config(rows=300, count=2)), case(route, config(rows=300, count=241, revoked=2)),
                  case(route, config(rows=limit + 1, status=2)), case(route, config(rows=2), key_ok=False)]
        if route != 'complete-buy':
            cases += [case(route, config(200), failing=True), case(route, config(2), failing=True)]
    return cases


def random_cases(count=600, seed=20261031):
    rng = random.Random(seed)
    cases = []
    routes = sorted(ROUTES)
    for _ in range(count):
        rows = rng.choice((0, 1, 2, 3, rng.randrange(0, 45), rng.randrange(0, 200)))
        data = bytearray(config(rows=rows, status=rng.choice((0, 1, 1, 1, 2, rng.randrange(256))),
                                version=rng.randrange(256), bump=rng.randrange(256),
                                revoked=rng.choice((0, 0, 1, 2, rng.randrange(256))),
                                count=rng.choice((None, None, None, rng.randrange(0, 60), rng.randrange(2**32))),
                                tail=rng.randbytes(rng.choice((0, 0, 1, 33, 34, 70)))))
        if rng.random() < 0.25:
            data[rng.randrange(len(data))] ^= 1 << rng.randrange(8)
        if rng.random() < 0.25:
            del data[rng.randrange(len(data)):]
        owner = rng.choice((FEES, FEES, SYSTEM, PUMP))
        cases.append(case(rng.choice(routes), bytes(data), owner=owner))
    return cases


class TradeShareholdersCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        base.program_images()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'trade-shareholders-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)], check=True)
        cls.runner = Runner()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def answers(self, cases):
        text = ''.join(host_line(c) + '\n' for c in cases)
        lines = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(len(lines), len(cases))
        return lines

    def run_cases(self, cases):
        wrong = []
        for c, answer in zip(cases, self.answers(cases)):
            reason = verdict(c, answer, *self.runner.run(c))
            if reason:
                wrong.append((host_line(c)[:120], answer[:40], reason))
        self.assertEqual(wrong, [], f'{len(wrong)} of {len(cases)}')

    def test_account_shapes_match_captured_program(self):
        self.run_cases(shape_cases())

    def test_routes_and_heap_limits_match_captured_program(self):
        self.run_cases(route_cases())

    def test_seeded_random_shapes_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_wrong_answers(self):
        # Negative control: the same captured run must fail against a wrong list or stop.
        c = case('token-sell', config(2))
        got, twin = self.runner.run(c)
        answer = self.answers([c])[0]
        self.assertIsNone(verdict(c, answer, got, twin))
        for bad in ('listed 00000000', answer[:-2] + 'ff', 'oom', 'refused 2006', 'trade_failed'):
            self.assertIsNotNone(verdict(c, bad, got, twin), bad)

    def test_cases_cover_every_outcome(self):
        cases = shape_cases() + route_cases()
        answers = self.answers(cases)
        words = {a.split(' ')[0] for a in answers}
        self.assertEqual(words, {'listed', 'oom', 'refused', 'trade_failed'})
        self.assertIn('listed 00000000', answers)
        self.assertTrue(any(a.startswith('listed') and len(a) > 20 for a in answers))


if __name__ == '__main__':
    unittest.main()
