"""Funded and unfunded buys in the recovered walk, checked against captured SBF."""
import hashlib
import random
import subprocess
import tempfile
import unittest
from pathlib import Path

import test_curve_walk_captured as walk


def starting_walk(setup, balance, vault):
    vm = walk.Walk(setup)
    vm.vm.with_sigverify(True)
    vm.vm.set_account(walk.USER, walk.Account(balance, b'', walk.base.SYSTEM))
    if vault:
        vm.vm.set_account(vm.vault, walk.Account(vault, b'', walk.base.SYSTEM))
    # The host gets only the common starting state, never a post-transaction state.
    line = ','.join(walk.start_line(setup).split(',')[:7]) + ',' + vm.state()
    return vm, line


def scenarios():
    setup = walk.plan(random.Random(1))[0] | dict(
        buyback=0, tiers=((0, 95, 30),), creator_bps=0)
    buy = ('buy', 10**12, walk.base.U64, b'')
    exact = ('exact', 30_000_000, 1, b'')
    controls = [buy, exact, ('buy', 0, walk.base.U64, b''),
                ('buy', 10**12, 0, b''), ('buy', 10**12, walk.base.U64, b'\x02'),
                ('exact', 30_000_000, 10**15, b'')]
    rows = []
    for creator in (True, False):
        current = setup | dict(creator=creator)
        for balance in (5_000, 10**6, 10**9):
            for op in controls:
                rows.append((current, balance, 0, [op]))
        for vault in (0, 890_880):
            for op in (buy, exact):
                control, _ = starting_walk(current, 10**9, vault)
                assert control.run(op).startswith('ok|')
                required = 10**9 - control.lamports(walk.USER)
                for balance in (required - 1, required, required + 1, required + 10**6):
                    rows.append((current, balance, vault, [op]))
    # Later steps must see the unchanged curve and token balances after failure.
    rows.append((setup | dict(creator=True), 10**6, 0,
                 [buy, ('buy', 1, walk.base.U64, b''), ('sell', 1, 0), ('collect',)]))
    return rows


def compare_case(host, case):
    setup, balance, vault, ops = case
    vm, line = starting_walk(setup, balance, vault)
    inputs = [line, *(walk.op_line(op) for op in ops)]
    captured = [vm.run(op) for op in ops]
    hosted = subprocess.run([str(host)], input='\n'.join(inputs) + '\n',
                            text=True, capture_output=True, check=True).stdout.splitlines()
    return dict(input=inputs, captured=captured, host=hosted[1:],
                matches=hosted[0] == 'started' and captured == hosted[1:])


class CurveWalkFundingCapturedTests(unittest.TestCase):
    def test_buy_payment_failures_preserve_the_walk(self):
        for path, digest in walk.base.ELF_SHA256.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        with tempfile.TemporaryDirectory(prefix='curve-walk-funding-') as directory:
            host = Path(directory) / 'host'
            subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings',
                            str(walk.HOST_SOURCE), '-o', str(host)], check=True)
            for case in scenarios():
                with self.subTest(balance=case[1], vault=case[2], operations=case[3]):
                    result = compare_case(host, case)
                    self.assertTrue(result['matches'], result)


if __name__ == '__main__':
    unittest.main()
