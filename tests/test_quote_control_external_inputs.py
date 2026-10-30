"""Real QuoteControl VM runs must support independently supplied ELF paths."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_validate_all as aggregate
import pump_validate_parallel as parallel


class ExternalQuoteControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json').is_file():
            raise RuntimeError('The retained config snapshot is required; see PR #2164 or the packet reproduce.py')
        cls.external = tempfile.TemporaryDirectory(prefix='pump-external-elf-')
        cls.internal = tempfile.TemporaryDirectory(prefix='pump-internal-elf-', dir=ROOT)
        cls.addClassCleanup(cls.external.cleanup)
        cls.addClassCleanup(cls.internal.cleanup)
        cls.image = gzip.decompress((ROOT / 'reconstruction/pump-main/lanes/v3-sell-payment-layout/candidate.so.gz').read_bytes())
        if hashlib.sha256(cls.image).hexdigest() != '969811b0e0f673b693695ea651008cacd93eafa5a663dd8bec0e61d3b22d09a9':
            raise RuntimeError('retained unstripped candidate changed')

    def run_vm(self, directory, label):
        candidate = Path(directory) / 'candidate.so'
        candidate.write_bytes(self.image)
        output = Path(self.external.name) / (label + '.json.gz')
        command = [sys.executable, '-B', str(ROOT / 'scripts/pump_quote_control_fresh_differential.py'),
                   '--candidate', str(candidate), '--output', str(output)]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=600)
        retained = os.environ.get('PUMP_EXTERNAL_PROOF_OUT')
        if retained:
            destination = Path(retained)
            destination.mkdir(parents=True, exist_ok=True)
            (destination / (label + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
            if output.is_file():
                shutil.copyfile(output, destination / output.name)
        self.assertEqual(result.returncode, 0, result.stdout[-3000:] + result.stderr[-3000:])
        report = json.loads(gzip.decompress(output.read_bytes()))
        self.assertEqual(report['cases'], 507)
        self.assertEqual(report['mismatches'], 0)
        self.assertEqual(len(report['results']), 507)
        self.assertTrue(all(row['matches'] and not row['different_fields'] for row in report['results']))
        return candidate, report

    def test_external_elf_and_real_aggregate_admission(self):
        candidate, report = self.run_vm(self.external.name, 'external')
        original = ROOT / 'evidence/original/pump/deployed.so'
        self.assertEqual(aggregate.validate_quote_control(report, candidate, original), 507)
        self.assertEqual(parallel.validate_result('quote_control', report, candidate, original), 507)
        # A real post-run input mutation must still invalidate the bound report.
        candidate.write_bytes(self.image + b'changed')
        try:
            with self.assertRaises(AssertionError):
                parallel.validate_result('quote_control', report, candidate, original)
        finally:
            candidate.write_bytes(self.image)

    def test_repository_local_positive_control(self):
        candidate, report = self.run_vm(self.internal.name, 'internal')
        original = ROOT / 'evidence/original/pump/deployed.so'
        self.assertEqual(parallel.validate_result('quote_control', report, candidate, original), 507)


if __name__ == '__main__':
    unittest.main()
