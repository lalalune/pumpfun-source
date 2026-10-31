"""Captured-program checks for the fee rates of `multi_hop_curve_swap` hops.

Every case runs Pump `multi_hop_curve_swap` from the captured
`evidence/original/pump/deployed.so` through the harness of
`tests/test_multi_hop_route_captured.py`, with its FeeConfig, Global and curves
changed so each hop can select another rate: the SOL tiers, the USDC stable tiers,
the flat or exotic fees, a curve's configurable creator fee, and FeeConfig lengths
around the gates. The same inputs go to
`programs/pump/recovered/multi_hop_fees_host.rs`, and everything the route test
compares must agree. Events are not compared. This shows matching behavior on
these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_multi_hop_route_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOST_SOURCE = ROOT / 'programs/pump/recovered/multi_hop_fees_host.rs'
USDC_KEY = Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
SOL_LIKE_KEY = Pubkey.from_bytes(bytes([131, 13, 252, 159, 222, 95, 230, 184, 170, 124, 4, 164, 118, 233, 30, 138, 198, 187, 38, 74,
                                        173, 144, 250, 25, 201, 223, 73, 216, 92, 62, 91, 94]))
# Mint ids of the route test, then USDC and the second SOL-priced quote.
MINTS = base.MINTS + [USDC_KEY, SOL_LIKE_KEY]
Q, A, B, C, USDC, SOL_LIKE = base.Q, base.A, base.B, base.C, 5, 6
U64 = base.U64
MC = 30_000_000_000                # default supply * vqr / vtr
PROGRAM_KEYS = {base.PUMP, base.pda([bytes(base.PUMP)], base.UPGRADEABLE)}
FIXED_COUNT, FIXED_OK, FIXED_MULTI, FIXED_CROSSING, RANDOM_OK = 1680, 1364, 708, 48, 216
TIERS = [(0, 95, 30)]
STABLE = [(0, 20, 5)]


def curve(b, q, creator_bps=0, **over):
    return dict(base.curve(b, q, **over), creator_bps=creator_bps)


def route(curves, hops, fee_len=4104, tiers=TIERS, stable=STABLE, flat=(90, 20), exotic=(0, 0, 0), configurable=0, supply=base.SUPPLY, **over):
    r = base.route(curves, hops, **over)
    r.update(fee_len=fee_len, tiers=tiers, stable=stable, flat=flat, exotic=exotic, configurable=configurable, supply=supply)
    return r


def fee_config_bytes(r):
    bump = Pubkey.find_program_address([b'fee_config', bytes(base.PUMP)], base.FEES)[1]

    def rows(items):
        return struct.pack('<I', len(items)) + b''.join(t.to_bytes(16, 'little') + struct.pack('<QQQ', 0, p, c) for t, p, c in items)
    data = (bytes([143, 52, 146, 187, 219, 123, 76, 155]) + bytes([bump]) + bytes([93]) * 32 + struct.pack('<QQQ', 0, *r['flat'])
            + rows(r['tiers']) + rows(r['stable']) + struct.pack('<QQQ', *r['exotic']))
    return data.ljust(r['fee_len'], b'\0')[:max(r['fee_len'], len(data))]


class SharedVm:
    """One VM for every case: the route harness reloads its ELFs per route, which costs far more than a transaction."""
    vm = None
    loaded = set()

    def __init__(self):
        if SharedVm.vm is None:
            SharedVm.vm = LiteSVM().with_transaction_history(0).with_sigverify(False)
        SharedVm.vm.expire_blockhash()

    def with_transaction_history(self, _):
        return self

    def with_sigverify(self, _):
        return self

    def set_account(self, key, account):
        if key in PROGRAM_KEYS:
            if key in SharedVm.loaded:
                return
            SharedVm.loaded.add(key)
        SharedVm.vm.set_account(key, account)

    def add_program(self, key, data):
        if key not in SharedVm.loaded:
            SharedVm.loaded.add(key)
            SharedVm.vm.add_program(key, data)

    def __getattr__(self, name):
        return getattr(SharedVm.vm, name)


def patched(r):
    """The route harness, with this route's fees, Global flag, supply and curve bps."""
    curve_data, global_data, mint_data = base.curve_data, base.global_data, base.mint_data

    def with_bps(c):
        data = bytearray(curve_data(c))
        struct.pack_into('<Q', data, 115, c['creator_bps'])
        return bytes(data)

    def with_flag(item):
        data = bytearray(global_data(item))
        data[1045] = item['configurable']
        struct.pack_into('<Q', data, 1046, 10_000)
        return bytes(data)
    return patch.multiple(base, LiteSVM=SharedVm, MINTS=MINTS, curve_data=with_bps, global_data=with_flag, fee_config_data=lambda: fee_config_bytes(r),
                          mint_data=lambda supply=base.SUPPLY, decimals=6: mint_data(r['supply'], decimals))


def run_captured(r):
    with patched(r):
        return base.run_captured(r)


def check(r, got, answer):
    with patched(r):
        return base.check(r, got, answer)


def host_line(r):
    rows = lambda items: '/'.join(f'{t}:{p}:{c}' for t, p, c in items) or '-'
    fees = [r['fee_len'], rows(r['tiers']), rows(r['stable']), ':'.join(map(str, r['flat'])), ':'.join(map(str, r['exotic'])), r['configurable'],
            r['supply'], ':'.join(str(c['creator_bps']) for c in r['curves'])]
    return ';'.join(map(str, fees)) + '$' + base.host_line(r)


_HOST = None


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'multi_hop_fees_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(routes):
    text = ''.join(host_line(r) + '\n' for r in routes)
    answers = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    if len(answers) != len(routes):
        raise ValueError(f'host returned {len(answers)} answers for {len(routes)} routes')
    return answers


def fixed_cases():
    out = []
    add = lambda label, r: out.append((label, r))
    quotes = (('sol', 0), ('spl', Q), ('usdc', USDC), ('sol-like', SOL_LIKE))
    shapes = (('buy', lambda q, **k: route([curve(A, q)], [0], source=q, destination=A, recipient=q, **k)),
              ('sell', lambda q, **k: route([curve(A, q)], [0], source=A, destination=q, recipient=q, **k)),
              ('sell-buy', lambda q, **k: route([curve(A, q), curve(B, q)], [0, 1], source=A, destination=B, recipient=q, **k)),
              ('trip', lambda q, **k: route([curve(A, q)], [0, 0], source=q, destination=q, recipient=q, **k)))
    ladders = (('first', [(0, 100, 10), (MC + 1, 200, 20), (MC * 2, 300, 30)]), ('exact', [(0, 100, 10), (MC, 200, 20), (MC + 1, 300, 30)]),
               ('last', [(0, 100, 10), (1, 200, 20), (2, 300, 30)]), ('below-first', [(MC + 1, 100, 10), (MC + 2, 200, 20)]),
               ('unsorted', [(MC + 1, 100, 10), (0, 200, 20), (MC * 9, 300, 30)]), ('one', [(MC, 150, 15)]))
    for qname, q in quotes:
        for sname, make in shapes:
            for flag in range(4):
                n = 2 if sname in ('sell-buy', 'trip') else 1
                flags = (flag,) * n
                for lname, rows in ladders:
                    add(f'{qname}-{sname}-{lname}-{flag}', make(q, flags=flags, tiers=rows, stable=rows))
                for size in (300, 2511, 2512, 4072, 4073, 4096, 4097, 4104):
                    add(f'{qname}-{sname}-len-{size}-{flag}', make(q, flags=flags, fee_len=size, exotic=(0, 50, 10)))
                add(f'{qname}-{sname}-lp-only-{flag}', make(q, flags=flags, exotic=(7, 0, 0)))
                add(f'{qname}-{sname}-exotic-creator-only-{flag}', make(q, flags=flags, exotic=(0, 0, 11)))
                add(f'{qname}-{sname}-configurable-{flag}', make(q, flags=flags, configurable=1))
                add(f'{qname}-{sname}-empty-{flag}', make(q, flags=flags, tiers=[], stable=[]))
                add(f'{qname}-{sname}-supply-{flag}', make(q, flags=flags, supply=3 * base.SUPPLY, tiers=ladders[0][1], stable=ladders[0][1]))
                add(f'{qname}-{sname}-supply-zero-{flag}', make(q, flags=flags, supply=0, tiers=ladders[2][1], stable=ladders[2][1]))
                add(f'{qname}-{sname}-rate-huge-{flag}', make(q, flags=flags, flat=(U64, 30), tiers=[(0, U64, 30)], stable=[(0, U64, 30)]))
                add(f'{qname}-{sname}-rate-sum-{flag}', make(q, flags=flags, flat=(9_000, 2_000), tiers=[(0, 9_000, 2_000)], stable=[(0, 9_000, 2_000)]))
    for qname, q in quotes:
        for flag in range(4):
            for configurable in (0, 1):
                for bps in (0, 1, 250, 9_000):
                    add(f'{qname}-curve-bps-{bps}-{configurable}-{flag}',
                        route([curve(A, q, creator_bps=bps), curve(B, q)], [0, 1], source=A, destination=B, recipient=q, flags=(flag, flag), configurable=configurable))
                add(f'{qname}-curve-bps-no-creator-{configurable}-{flag}',
                    route([curve(A, q, creator_bps=250, creator=0)], [0], source=A, destination=q, recipient=q, flags=(flag,), configurable=configurable))
        # Two curves on different tiers, and a curve that climbs a tier between visits.
        split = [(0, 100, 10), (MC * 2, 300, 30)]
        add(f'{qname}-two-tiers', route([curve(A, q), curve(B, q, vqr=3 * MC)], [0, 1], source=A, destination=B, recipient=q, flags=(3, 3), tiers=split, stable=split))
        for amount in (MC // 100, MC, 2 * MC, 3 * MC):
            add(f'{qname}-climb-{amount}', route([curve(A, q)], [0, 0], amount=amount, source=q, destination=q, recipient=q, flags=(3, 3), tiers=split, stable=split))
        add(f'{qname}-zero-vtr', route([curve(A, q, vtr=0)], [0], source=A, destination=q, recipient=q))
        add(f'{qname}-short-before-empty', route([curve(A, q)], [0], source=A, destination=q, recipient=q, fee_len=2511, tiers=[], stable=[]))
        add(f'{qname}-huge-creator-no-creator', route([curve(A, q, creator=0)], [0], source=A, destination=q, recipient=q, flat=(0, U64), tiers=[(0, 0, U64)], stable=[(0, 0, U64)]))
        add(f'{qname}-huge-creator-on-small-sell', route([curve(A, q)], [0], amount=1, source=A, destination=q, recipient=q, flat=(0, U64), tiers=[(0, 0, U64)], stable=[(0, 0, U64)]))
        add(f'{qname}-huge-configured-bps', route([curve(A, q, creator_bps=U64)], [0], source=A, destination=q, recipient=q, configurable=1))
        add(f'{qname}-huge-configured-bps-off', route([curve(A, q, creator_bps=U64)], [0], source=A, destination=q, recipient=q))
        # A sell computes the fees on its quote, not on the tokens sold.
        add(f'{qname}-rate-fits-quote-not-tokens', route([curve(A, q)], [0], amount=10**14, source=A, destination=q, recipient=q, source_balance=10**14,
                                                         flat=(2 * 10**9, 0), tiers=[(0, 2 * 10**9, 0)], stable=[(0, 2 * 10**9, 0)]))
        add(f'{qname}-zero-vtr-empty', route([curve(A, q, vtr=0)], [0], source=A, destination=q, recipient=q, tiers=[], stable=[]))
        add(f'{qname}-complete-before-empty', route([curve(A, q, complete=1)], [0], source=A, destination=q, recipient=q, tiers=[], stable=[]))
        add(f'{qname}-discontinuous-before-empty', route([curve(A, q)], [0], source=C, destination=q, recipient=q, tiers=[], stable=[]))
        add(f'{qname}-recipient-before-empty', route([curve(A, q)], [0], source=A, destination=q, recipient=C, flags=(1,), tiers=[], stable=[]))
        # Crossing buys use the hop's tier for both fills.
        ladder = [(0, 100, 10), (MC, 200, 20), (MC + 1, 300, 30)]
        for flag in range(4):
            for amount in (31_000_000, 40_000_000, 10**9):
                add(f'{qname}-cross-{amount}-{flag}', route([curve(A, q, rtr=10**12, creator_bps=70)], [0], amount=amount, source=q, destination=A, recipient=q,
                                                            flags=(flag,), tiers=ladder, stable=ladder, configurable=flag & 1))
    return out


def random_cases(count=300, seed=20261031):
    rng = random.Random(seed)
    out = []
    for i in range(count):
        q = rng.choice([0, Q, USDC, SOL_LIKE])
        rand_curve = lambda b: curve(b, q, vqr=rng.randrange(10**8, 10**11), rtr=rng.choice([10**12, 10**14]), rqr=rng.randrange(10**8, 10**12),
                                     creator=int(rng.random() < .8), cf=rng.randrange(10**6), pf=rng.randrange(10**6),
                                     creator_bps=rng.choice([0, 0, rng.randrange(2_000)]))
        rows = lambda: sorted((rng.randrange(10**11), rng.randrange(1_000), rng.randrange(1_000)) for _ in range(rng.randrange(1, 5)))
        shape = rng.choice(['sell-buy', 'trip', 'three', 'cross'])
        hops, source, dest = {'sell-buy': ([0, 1], A, B), 'trip': ([0, 0], q, q), 'three': ([0, 1, 1], A, q), 'cross': ([0], q, A)}[shape]
        r = route([rand_curve(A), rand_curve(B)], hops, amount=rng.randrange(10**6, 10**11), flags=tuple(rng.randrange(4) for _ in hops), source=source, destination=dest,
                  recipient=q, fee_len=rng.choice([4104, 4104, 4072, 4200, 2512]), tiers=rows(), stable=rows(), flat=(rng.randrange(1_000), rng.randrange(1_000)),
                  exotic=rng.choice([(0, 0, 0), (0, rng.randrange(500), rng.randrange(500))]), configurable=int(rng.random() < .4),
                  supply=rng.choice([base.SUPPLY, 2 * base.SUPPLY, 10**14]), buyback_bps=rng.choice([0, 5_000, 10_000]))
        out.append((f'random-{i}-{shape}', r))
    return out


class MultiHopFeesCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base.captured_program_bytes()

    def run_all(self, labelled):
        answers = model([r for _, r in labelled])
        self.assertEqual(len(answers), len(labelled), 'one model answer is required per captured route')
        for (label, r), answer in zip(labelled, answers):
            with self.subTest(label):
                self.assertEqual(check(r, run_captured(r), answer), [], (label, answer))
        return answers

    def test_fixed_cases(self):
        cases = fixed_cases()
        self.assertEqual(len(cases), FIXED_COUNT)
        results = self.run_all(cases)
        outcomes = {a.split(',')[0] for a in results}
        for want in ('ok', 'error:6004', 'error:6005', 'error:6022', 'error:6024', 'error:6025', 'error:6026', 'error:6096', 'error:6097', 'error:6098'):
            self.assertIn(want, outcomes)
        self.assertEqual(sum(a.startswith('ok,') for a in results), FIXED_OK)
        self.assertEqual(sum(a.startswith('ok,') and len(r['hops']) >= 2 for (_, r), a in zip(cases, results)), FIXED_MULTI, 'successful multi-hop routes')
        self.assertEqual(sum(a.startswith('ok,') and any(int(b.split(',')[6]) > 0 for b in a.split('|')[1:]) for a in results),
                         FIXED_CROSSING, 'successful crossing fills')

    def test_random_cases(self):
        cases = random_cases()
        self.assertEqual(len(cases), 300)
        self.assertEqual(sum(a.startswith('ok,') for a in self.run_all(cases)), RANDOM_OK)

    def test_pinned_programs_are_the_route_tests(self):
        self.assertEqual(base.ELF_SHA256[base.PUMP_ELF], '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d')
        self.assertEqual(len(base.captured_program_bytes()), 2)

    def test_rates_reach_the_vm(self):
        # The patched harness must really change the rate, or every case above would be vacuous.
        low = route([curve(A, 0)], [0], source=A, destination=0, recipient=0, flags=(1,), tiers=[(0, 100, 0)])
        high = route([curve(A, 0)], [0], source=A, destination=0, recipient=0, flags=(1,), tiers=[(0, 900, 0)])
        low_got, high_got = run_captured(low), run_captured(high)
        self.assertNotEqual(low_got['returned'], high_got['returned'])
        self.assertEqual(check(low, low_got, model([low])[0]), [])
        self.assertNotEqual(check(low, high_got, model([low])[0]), [])

    def test_checker_rejects_tampered_outcomes(self):
        r = route([curve(A, Q), curve(B, Q)], [0, 1], source=A, destination=B, recipient=Q, flags=(3, 3))
        answer = model([r])[0]
        got = run_captured(r)
        self.assertEqual(check(r, got, answer), [])
        head, *curves = answer.split('|')
        fields = head.split(',')
        for i in range(1, len(fields)):
            bent = fields[:i] + [str(int(fields[i]) + 1)] + fields[i + 1:]
            self.assertNotEqual(check(r, got, '|'.join([','.join(bent)] + curves)), [], i)
        for bent in ('', head, 'error:6096', answer.replace('ok,', 'unmodelled,', 1)):
            self.assertNotEqual(check(r, got, bent), [], bent)


if __name__ == '__main__':
    unittest.main()
