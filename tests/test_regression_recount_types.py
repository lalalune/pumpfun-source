"""Real offline verifier drivers reject coerced counters and malformed rows.

These reuse owned synthetic bookkeeping packages. Differential/VM modules are
stubbed, so these are receipt-admission tests, not execution of stopped lanes.
"""
import gzip
import hashlib
import json
from unittest import mock
import unittest

import test_admin_token_incentives_optimization as admin
import test_claim_token_incentives_8099_optimization as claim8099
import test_claim_token_incentives_source_binding as claim


def fixture(test, cls):
    method = next(name for name in dir(cls) if name.startswith('test_'))
    case = cls(method)
    case.setUp()
    test.addCleanup(case.doCleanups)
    return case


def rewrite(package, target, key, value):
    path = package / ('quote-control-regression.json.gz' if target == 'quote' else 'multi-hop-regression.json.gz')
    report = json.loads(gzip.decompress(path.read_bytes()))
    if key == 'row':
        report['results' if target == 'quote' else 'cases'][0] = value
    else:
        report[key] = value
    path.write_bytes(gzip.compress(json.dumps(report).encode(), mtime=0))
    summary_path = package / 'regression-summary.json'
    summary = json.loads(summary_path.read_text())
    for name, field in (('quote-control-regression.json.gz', 'quote_control'),
                        ('multi-hop-regression.json.gz', 'multi_hop_curve')):
        summary[field]['receipt_sha256'] = hashlib.sha256((package / name).read_bytes()).hexdigest()
    summary_path.write_text(json.dumps(summary))


VARIANTS = [('quote', 'cases', 507.0), ('quote', 'mismatches', False),
            ('curve', 'case_count', 56.0), ('curve', 'passed', 56.0),
            ('quote', 'row', None), ('curve', 'row', None)]


class RegressionRecountTypes(unittest.TestCase):
    def test_admin_counter_types_and_rows_are_checked_in_all_modes(self):
        case = fixture(self, admin.AdminTokenIncentivesOptimizationTests)
        original = case.write_regression_package
        for target, key, value in VARIANTS:
            def altered(*args, **kwargs):
                original(*args, **kwargs)
                rewrite(case.build.parent, target, key, value)
            with self.subTest(target=target, key=key), mock.patch.object(case, 'write_regression_package', side_effect=altered):
                for result in case.run_regression_baseline(case.stub_quote_input()):
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn('regression case', result.stderr)

    def test_8099_counter_types_and_rows_are_checked_in_all_modes(self):
        case = fixture(self, claim8099.Claim8099OptimizationTests)
        original = {name: (case.pkg / name).read_bytes() for name in
                    ('quote-control-regression.json.gz', 'multi-hop-regression.json.gz', 'regression-summary.json')}
        for target, key, value in VARIANTS:
            for name, raw in original.items(): (case.pkg / name).write_bytes(raw)
            case.write_receipt('none')
            rewrite(case.pkg, target, key, value)
            for mode in claim8099.MODES:
                with self.subTest(target=target, key=key, mode=mode):
                    result = case.run_driver(mode)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn('claim verification failed', result.stderr)

    def test_inherited_quote_counter_types_and_rows_are_checked_in_all_modes(self):
        case = fixture(self, claim.ClaimInheritedBindingTests)
        for key, value in [('cases', 507.0), ('mismatches', False), ('row', None)]:
            case.write_inherited(*case.valid_maps())
            path = case.repro_dir / 'quote_control.json.gz'
            report = json.loads(gzip.decompress(path.read_bytes()))
            if key == 'row': report['results'][0] = value
            else: report[key] = value
            raw = json.dumps(report).encode()
            compressed = gzip.compress(raw, mtime=0)
            path.write_bytes(compressed)
            index = case.repro_dir / 'inherited-regressions.json'
            summary = json.loads(index.read_text())
            entry = next(row for row in summary['receipts'] if row['name'] == 'quote_control')
            entry.update(compressed_sha256=hashlib.sha256(compressed).hexdigest(),
                         json_sha256=hashlib.sha256(raw).hexdigest(), json_bytes=len(raw))
            index.write_text(json.dumps(summary))
            for mode, result in case.run_full():
                with self.subTest(key=key, mode=mode):
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn('claim verification failed', result.stderr)


if __name__ == '__main__':
    unittest.main()
