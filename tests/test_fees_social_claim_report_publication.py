"""Unmodified full social-claim corpus and bounded real-VM publication controls."""
import hashlib
import shutil
import unittest
import publication_cli_support as support
from publication_cli_support import PublicationCase, ROOT


class FeesSocialClaimReportPublicationTests(PublicationCase, unittest.TestCase):
    NAMES = ('fees_social_claim_differential',)
    DATA = ('evidence/upstream/pump_fees.json', 'evidence/original/pump_fees/deployed.so')
    HELPERS = ('fees_admin_differential', 'pump_amm_reusable_harness')
    PROGRAM = 'evidence/original/pump_fees/deployed.so'
    EXPECTED = {'fees_social_claim_differential': 347}

    def test_wrong_real_image_preserves_failed_report(self):
        shutil.copyfile(ROOT / 'evidence/original/mayhem/deployed.so', self.root / 'candidate.so')
        result = self.invoke(self.NAMES[0])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = self.report()
        self.assertEqual(len(report['cases']), 2)
        self.assertTrue(report['mismatches'])
        self.assertEqual(report['candidate_sha256'], hashlib.sha256((self.root / 'candidate.so').read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
