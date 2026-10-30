"""Checked arithmetic for the recovered Pump curve fragments.

The sell-v3 reserve fixture only compares successful u64 trades. It does not
compare u128 overflow or a zero denominator, and it does not run without the
captured LiteSVM fixture. These cases compile the same host binaries and check
them against an independent integer model.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOVERED = ROOT / 'programs' / 'pump' / 'recovered'
U64_MAX = 2 ** 64 - 1
U128_MAX = 2 ** 128 - 1


def compile_host(source, output):
    result = subprocess.run(
        ['rustc', '--edition=2021', '-O', str(source), '-o', str(output)],
        cwd=RECOVERED,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)


def run_host(binary, lines):
    result = subprocess.run(
        [str(binary)],
        input=''.join(line + '\n' for line in lines),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.splitlines()


def constant_product(amount_in, reserve_in, reserve_out):
    if amount_in > U128_MAX or reserve_in > U128_MAX or reserve_out > U128_MAX:
        raise ValueError('input does not fit in u128')
    if amount_in * reserve_out > U128_MAX:
        return 'error:6024'
    if reserve_in + amount_in > U128_MAX:
        return 'error:6024'
    denominator = reserve_in + amount_in
    if denominator == 0:
        return 'error:6026'
    return str((amount_in * reserve_out) // denominator)


def ceil_fee(amount, bps):
    result = (amount * bps + 9999) // 10000
    if result > U64_MAX:
        return None
    return result


def sell_accounting(quote_out, protocol_bps, creator_bps, buyback_bps):
    protocol_fee = ceil_fee(quote_out, protocol_bps)
    if protocol_fee is None:
        return 'error:6025'
    creator_fee = ceil_fee(quote_out, creator_bps)
    if creator_fee is None:
        return 'error:6025'
    buyback_fee = (protocol_fee * buyback_bps) // 10000
    if buyback_fee > U64_MAX:
        return 'error:6025'
    if protocol_fee > quote_out:
        return 'error:6024'
    after_protocol = quote_out - protocol_fee
    if creator_fee > after_protocol:
        return 'error:6024'
    if buyback_fee > protocol_fee:
        return 'error:6024'
    user_output = after_protocol - creator_fee
    retained = protocol_fee - buyback_fee
    return f'{protocol_fee},{creator_fee},{buyback_fee},{user_output},{retained}'


class RecoveredCurveArithmeticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        root = Path(cls.temporary.name)
        cls.curve = root / 'constant-product'
        cls.sell = root / 'sell-accounting'
        compile_host(RECOVERED / 'constant_product_host.rs', cls.curve)
        compile_host(RECOVERED / 'sell_accounting_host.rs', cls.sell)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_constant_product_matches_checked_floor_division(self):
        cases = [
            (3, 5, 10),
            (0, 5, 10),
            (1, 1, 0),
            (1, 2, 3),
            (2, 5, 4),
            (0, 0, 5),
            (U128_MAX, 1, 1),
            (2 ** 127, 1, 4),
        ]
        lines = [f'{amount},{reserve_in},{reserve_out}' for amount, reserve_in, reserve_out in cases]
        actual = run_host(self.curve, lines)
        expected = [constant_product(amount, reserve_in, reserve_out) for amount, reserve_in, reserve_out in cases]
        self.assertEqual(actual, expected)
        self.assertEqual(actual[cases.index((0, 0, 5))], 'error:6026')
        self.assertEqual(actual[cases.index((U128_MAX, 1, 1))], 'error:6024')
        self.assertEqual(actual[cases.index((2 ** 127, 1, 4))], 'error:6024')

    def test_sell_accounting_rounds_fees_up_and_buyback_down(self):
        cases = [
            (1, 1, 0, 0),
            (10000, 1, 0, 0),
            (10001, 1, 0, 0),
            (3, 10000, 0, 5000),
            (1, 1, 1, 0),
            (10000, 10000, 0, 10001),
            (U64_MAX, 10001, 0, 0),
        ]
        lines = [f'{quote},{protocol},{creator},{buyback}' for quote, protocol, creator, buyback in cases]
        actual = run_host(self.sell, lines)
        expected = [sell_accounting(quote, protocol, creator, buyback) for quote, protocol, creator, buyback in cases]
        self.assertEqual(actual, expected)
        self.assertEqual(actual[0], '1,0,0,0,1')
        self.assertEqual(actual[3], '3,0,1,0,2')
        self.assertEqual(actual[4], 'error:6024')
        self.assertEqual(actual[5], 'error:6024')
        self.assertEqual(actual[6], 'error:6025')


if __name__ == '__main__':
    unittest.main(verbosity=2)
