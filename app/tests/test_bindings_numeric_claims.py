"""Numeric ledger fields must not accept Python's Boolean/integer aliases."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('binding_numeric_claims', ROOT / 'scripts/verify-bindings.py')
bindings_verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bindings_verifier)


class NumericClaimTests(unittest.TestCase):
    def test_boolean_zero_claims_do_not_pass_complete_real_verification(self):
        original = json.loads((ROOT / 'contracts/coverage.json').read_text(encoding='utf-8'))
        for field in ['implementedNatively', 'qualified']:
            with self.subTest(field=field):
                coverage = copy.deepcopy(original)
                coverage['developerApi'][field] = False
                with self.assertRaisesRegex(ValueError, field):
                    bindings_verifier.verify(coverage=coverage)

    def test_boolean_schema_version_is_not_version_one(self):
        bindings = json.loads((ROOT / 'contracts/developer-bindings.json').read_text(encoding='utf-8'))
        bindings['schemaVersion'] = True
        with self.assertRaisesRegex(ValueError, 'schema'):
            bindings_verifier.verify(bindings=bindings)

    def test_current_numeric_ledger_and_capture_bindings_remain_valid(self):
        self.assertEqual(bindings_verifier.verify(), (67, 67, 1))

    def test_integral_json_numbers_keep_existing_acceptance(self):
        coverage = json.loads((ROOT / 'contracts/coverage.json').read_text(encoding='utf-8'))
        for field in ['contractBound', 'documentedOperations', 'implementedNatively', 'qualified']:
            coverage['developerApi'][field] = float(coverage['developerApi'][field])
        self.assertEqual(bindings_verifier.verify(coverage=coverage), (67, 67, 1))


if __name__ == '__main__':
    unittest.main()
