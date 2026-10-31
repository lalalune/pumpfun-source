"""Unmodified full donation-relay corpus and bounded real-VM publication controls."""
import hashlib
import shutil
import unittest
import publication_cli_support as support
from publication_cli_support import PublicationCase, ROOT


class DonationRelayReportPublicationTests(PublicationCase, unittest.TestCase):
    NAMES = ('donation_relay_differential',)
    DATA = (
        'evidence/dependencies/donation_relay/deployed.so',
        'evidence/dependencies/donation_relay/donation_relay.json',
        'evidence/dependencies/donation_relay/amm-fixture.json',
        'evidence/dependencies/spl_token/deployed.so',
        'evidence/dependencies/associated_token/deployed.so',
    )
    HELPERS = ('pump_differential_output',)
    PROGRAM = 'evidence/dependencies/donation_relay/deployed.so'
    EXPECTED = {'donation_relay_differential': 12}

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
