"""Unmodified full donation-relay corpus and bounded real-VM publication controls."""
import hashlib
import gzip
import json
import subprocess
import sys
import shutil
import unittest
import publication_cli_support as support
from publication_cli_support import PublicationCase, ROOT


class DonationRelayReportPublicationTests(PublicationCase, unittest.TestCase):
    NAMES = ('donation_relay_differential',)
    DATA = (
        'evidence/dependencies/donation_relay/deployed.so',
        'scripts/fixtures/donation-relay/idl.json',
        'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',
        'evidence/dependencies/spl_token/deployed.so',
        'evidence/dependencies/associated_token/deployed.so',
    )
    HELPERS = ('pump_differential_output',)
    PROGRAM = 'evidence/dependencies/donation_relay/deployed.so'
    EXPECTED = {'donation_relay_differential': 12}
    CANDIDATE_REQUIRED = True

    def report(self):
        result = super().report()
        # Adapt the unchanged relay schema for shared publication assertions.
        result['mismatches'] = result['mismatched_cases']
        return result

    def test_full_business_rejection_group(self):
        self.ARGS = {self.NAMES[0]: ['--group', 'business_rejection']}
        result = self.invoke(self.NAMES[0], 'full')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report()
        self.assertEqual(report['group'], 'business_rejection')
        self.assertEqual(report['case_count'], 3)
        self.assertEqual(report['mismatched_cases'], [])

    def test_real_gzip_publication(self):
        self.output = self.output.with_suffix('.json.gz')
        result = self.invoke(self.NAMES[0])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        raw = self.output.read_bytes()
        self.assertEqual(raw[:2], b'\x1f\x8b')
        self.assertEqual(int.from_bytes(raw[4:8], 'little'), 0)
        report = json.loads(gzip.decompress(raw))
        self.assertEqual(report['case_count'], 2)
        self.assertEqual(report['mismatched_cases'], [])

    def test_direct_execute_refuses_candidate_alias_before_running_cases(self):
        code = """import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'scripts'))
import donation_relay_differential as oracle
def forbidden(*args):
    raise AssertionError('cases ran before output admission')
oracle.cases = forbidden
try:
    oracle.execute(root / 'candidate.so', 'ordinary', root / 'candidate.so')
except ValueError as error:
    assert 'report output aliases an input' in str(error), str(error)
else:
    raise AssertionError('direct execute overwrote its candidate')
"""
        before = (self.root / 'candidate.so').read_bytes()
        result = subprocess.run([sys.executable, '-B', '-c', code, str(self.root)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / 'candidate.so').read_bytes(), before)

    def test_wrong_real_image_preserves_failed_report(self):
        shutil.copyfile(ROOT / 'evidence/original/mayhem/deployed.so', self.root / 'candidate.so')
        result = self.invoke(self.NAMES[0])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = self.report()
        self.assertEqual(len(report['cases']), 2)
        self.assertTrue(report['mismatched_cases'])
        self.assertEqual(report['candidate_sha256'], hashlib.sha256((self.root / 'candidate.so').read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
