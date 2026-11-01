"""Original Pump admin_cto fee bounds and cross-program validation precedence.

The large-u64 cases use a curve-only pool gate to reach Pump's own fee check.
One AMM-owned pool case keeps the genuine CPI and its separate fee limit.
This is finite captured-binary behavior coverage, not a byte-identity proof.
"""
import base64
import hashlib
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_admin_cto_differential as fixture
from solders.transaction import Transaction

ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'
ORIGINAL_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'


def error_code(result):
    if result['error'] is None:
        return None
    match = re.search(r'InstructionErrorCustom\((\d+)\)', result['error'])
    if match is None:
        raise AssertionError('Expected an executed custom-program error: ' + result['error'])
    return int(match.group(1))


def fee_value(snapshot):
    offset = fixture.fixed_field_offset('BondingCurve', 'creator_fee_bps')
    data = bytes.fromhex(snapshot['bonding_curve']['data'])
    return int.from_bytes(data[offset:offset+8], 'little')


class PumpAdminCtoFeeBoundsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() != ORIGINAL_SHA256:
            raise AssertionError('Captured Pump image changed')
        cls.cases = fixture.fee_bound_cases()
        cls.results = {case['name']: fixture.run(case) for case in cls.cases}

    @classmethod
    def tearDownClass(cls):
        if hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() != ORIGINAL_SHA256:
            raise AssertionError('Captured Pump image changed during tests')

    def assert_contract(self, case, result):
        self.assertEqual(error_code(result), case['expected_fee_error'], case['name'])
        transaction = Transaction.from_bytes(base64.b64decode(result['transaction_base64']))
        verified = transaction.verify_with_results()
        # all() over a transaction with no signatures is vacuously true, so an
        # unsigned transaction satisfied the check without proving anything.
        self.assertTrue(verified, 'transaction carries no signature: ' + case['name'])
        self.assertTrue(all(verified), case['name'])
        self.assertFalse(result['pool_authority_top_level_signer'])
        if case['expected_fee_error'] is not None:
            # Failed instructions roll back state; the transaction payer still pays fees.
            for account in result['before'].keys() - {'transaction_payer'}:
                self.assertEqual(result['before'][account], result['after'][account], account)
            return
        before = fee_value(result['before'])
        expected = case.get('fee', before)
        self.assertEqual(fee_value(result['after']), expected, case['name'])
        discriminator = bytes(next(event['discriminator'] for event in fixture.pump.IDL['events']
                                   if event['name'] == 'AdminCtoEvent'))
        events = [base64.b64decode(line.removeprefix('Program data: ')) for line in result['events']]
        events = [event for event in events if event.startswith(discriminator)]
        self.assertTrue(events, 'AdminCtoEvent was not emitted: ' + case['name'])
        old_offset = fixture.fixed_field_offset('AdminCtoEvent', 'old_creator_fee_bps')
        new_offset = fixture.fixed_field_offset('AdminCtoEvent', 'new_creator_fee_bps')
        for event in events:
            self.assertGreaterEqual(len(event), new_offset+8, case['name'])
            self.assertEqual(int.from_bytes(event[old_offset:old_offset+8], 'little'), before)
            self.assertEqual(int.from_bytes(event[new_offset:new_offset+8], 'little'), expected)

    def test_original_fee_bounds_and_precedence(self):
        self.assertEqual(len(self.cases), 25)
        self.assertEqual(len({case['name'] for case in self.cases}), len(self.cases))
        for case in self.cases:
            with self.subTest(case=case['name']):
                self.assert_contract(case, self.results[case['name']])

    def test_aggregate_expects_the_expanded_corpus(self):
        import pump_validate_all
        self.assertEqual(pump_validate_all.EXPECTED_CASES['admin_cto'], len(fixture.cases()))

    def test_pump_maximum_and_amm_maximum_are_independent(self):
        maximum = 2**64-1
        curve = self.results[f'fee-limit-{maximum}-{maximum}']
        amm = self.results['fee-limit-amm-has-own-limit']
        self.assertIsNone(error_code(curve))
        self.assertEqual(fee_value(curve['after']), maximum)
        self.assertEqual(error_code(amm), 6069)
        self.assertTrue(any('pump-amm/src/instructions/admin/admin_cto_pool.rs:111' in line
                            for line in amm['logs']))
        self.assertEqual(amm['before']['bonding_curve'], amm['after']['bonding_curve'])


if __name__ == '__main__':
    unittest.main()
