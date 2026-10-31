"""The real quote-control producer remains reusable after a candidate re-pin."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'research/runtime-quote-control-repin-20261101/probe.py'


class QuoteControlRepinnedReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='test-quote-control-repin-')
        cls.addClassCleanup(temporary.cleanup)
        output = Path(temporary.name) / 'run'
        result = subprocess.run([sys.executable, '-B', str(PROBE), '--repo', str(ROOT),
                                 '--output', str(output)], cwd=ROOT, capture_output=True,
                                text=True, timeout=240)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        cls.result = json.loads((output / 'results.json').read_text(encoding='utf-8'))
        cls.receipt = json.loads(gzip.decompress((output / 'receipt.json.gz').read_bytes()))

    def test_real_receipt_admits_both_identical_candidate_paths(self):
        self.assertEqual(self.result['producer_returncode'], 0)
        self.assertEqual(self.result['case_count'], 507)
        self.assertEqual(self.result['mismatches'], 0)
        self.assertNotEqual(self.result['first_pin'], self.result['second_pin'])
        for name in ('first_admission', 'same_byte_second_pin_admission'):
            self.assertEqual(self.result[name], {'accepted': True, 'count': 507}, name)

    def test_image_roles_are_derived_from_the_bound_input_bytes(self):
        expected = hashlib.sha256((ROOT / 'evidence/original/pump/deployed.so').read_bytes()).hexdigest()
        self.assertEqual(self.receipt['candidate_sha256'], expected)
        self.assertEqual(self.receipt['original_sha256'], expected)
        bound = self.receipt['bound_inputs_sha256']
        self.assertEqual(bound[Path(self.result['first_pin']).resolve().as_posix()], expected)
        self.assertEqual(bound['evidence/original/pump/deployed.so'], expected)
        self.assertTrue(self.result['inputs_unchanged'])
        self.assertTrue(self.result['receipt_unchanged_by_admission'])

    def test_wrong_images_and_contradictory_retained_results_still_reject(self):
        self.assertEqual(len(self.result['negative_controls']), 13)
        for name, result in self.result['negative_controls'].items():
            with self.subTest(control=name):
                self.assertFalse(result['accepted'], result)

    def test_legacy_path_bound_receipt_keeps_its_existing_admission(self):
        self.assertEqual(self.result['legacy_first_admission'], {'accepted': True, 'count': 507})
        self.assertFalse(self.result['legacy_second_admission']['accepted'])


if __name__ == '__main__':
    unittest.main()
