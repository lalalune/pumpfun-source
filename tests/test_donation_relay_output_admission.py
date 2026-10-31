#!/usr/bin/env python3
"""A donation-relay report must not be written over an input the oracle reads."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/donation_relay_differential.py'
ORIGINAL = ROOT / 'evidence/dependencies/donation_relay/deployed.so'


class DonationRelayOutputAdmissionTests(unittest.TestCase):
    def invoke(self, candidate, output):
        return subprocess.run(
            [sys.executable, '-B', str(SCRIPT), '--candidate', str(candidate),
             '--output', str(output)],
            capture_output=True, text=True, timeout=120)

    def candidate_copy(self, root):
        candidate = Path(root) / 'candidate.so'
        candidate.write_bytes(ORIGINAL.read_bytes())
        return candidate

    def test_candidate_destination_is_refused_before_the_cases_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = self.candidate_copy(temporary)
            before = candidate.read_bytes()
            result = self.invoke(candidate, candidate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('report output aliases an input', result.stderr)
            # Refusal precedes the oracle, so no fixture lookup has happened yet.
            self.assertNotIn('missing input', result.stderr)
            self.assertEqual(candidate.read_bytes(), before)

    def test_captured_original_destination_is_refused(self):
        # Exercise the guard directly: a CLI run that failed to refuse would
        # overwrite the tracked capture this test reads.
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            import donation_relay_differential as oracle
        except Exception as error:  # solders or its LiteSVM binding is required
            self.skipTest(f'oracle module unavailable: {error}')
        with self.assertRaisesRegex(ValueError, 'report output aliases an input'):
            oracle.protect_output(ORIGINAL, [oracle.ORIGINAL])

    def test_linked_destinations_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = self.candidate_copy(temporary)
            before = candidate.read_bytes()
            hard = Path(temporary) / 'hard.json'
            soft = Path(temporary) / 'soft.json'
            try:
                os.link(candidate, hard)
                soft.symlink_to(candidate)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f'links are unavailable: {error}')
            for destination in (hard, soft):
                result = self.invoke(candidate, destination)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('report output aliases an input', result.stderr)
            self.assertEqual(candidate.read_bytes(), before)
            self.assertTrue(soft.is_symlink())

    def test_unrelated_destination_is_not_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = self.candidate_copy(temporary)
            result = self.invoke(candidate, Path(temporary) / 'report.json')
            self.assertNotIn('report output aliases an input', result.stderr)


if __name__ == '__main__':
    unittest.main()
