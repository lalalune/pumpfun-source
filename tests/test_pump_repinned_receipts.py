"""Real producer receipts retain image identity across temporary pin paths."""
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_validate_parallel as validator
from pump_amm_reusable_harness import pin_program

SUITES = (
    ('creator_collection', 'pump_creator_collect_differential.py'),
    ('creator_collection_v2', 'pump_creator_collect_v2_differential.py'),
    ('fee_sweeps', 'pump_fee_sweep_differential.py'),
    ('minimum_distribution', 'pump_minimum_fee_differential.py'),
    ('set_params', 'pump_set_params_differential.py'),
)


class RepinnedReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        output = Path(cls.temporary.name)
        cls.original = ROOT / 'evidence/original/pump/deployed.so'
        copy = output / 'same-image.so'
        shutil.copyfile(cls.original, copy)
        cls.first, cls.second = pin_program(cls.original), pin_program(copy)

        def run_suite(entry):
            name, script = entry
            receipt = output / (name + '.json')
            subprocess.run([sys.executable, str(ROOT / 'scripts' / script),
                            '--candidate', str(cls.first), '--output', str(receipt)],
                           capture_output=True, text=True, check=True, timeout=180)
            raw = receipt.read_bytes()
            return name, json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)

        with ThreadPoolExecutor(max_workers=4) as pool:
            cls.receipts = dict(pool.map(run_suite, SUITES))

    def test_same_image_at_new_pin_path_is_admitted(self):
        self.assertNotEqual(self.first, self.second)
        self.assertEqual(self.first.read_bytes(), self.second.read_bytes())
        for name, receipt in self.receipts.items():
            with self.subTest(suite=name):
                self.assertEqual(receipt['candidate_sha256'], receipt['provenance'][str(self.first)])
                self.assertEqual(receipt['original_sha256'], receipt['provenance'][str(self.original)])
                self.assertEqual(validator.validate_result(name, receipt, self.first, self.original),
                                 validator.base.EXPECTED_CASES[name])
                self.assertEqual(validator.validate_result(name, receipt, self.second, self.original),
                                 validator.base.EXPECTED_CASES[name])

    def test_different_image_remains_rejected(self):
        wrong = ROOT / 'evidence/original/pump_fees/deployed.so'
        for name, receipt in self.receipts.items():
            with self.subTest(suite=name, side='candidate'), self.assertRaises(AssertionError):
                validator.validate_result(name, receipt, wrong, self.original)
            with self.subTest(suite=name, side='original'), self.assertRaises(AssertionError):
                validator.validate_result(name, receipt, self.first, wrong)


if __name__ == '__main__':
    unittest.main()
