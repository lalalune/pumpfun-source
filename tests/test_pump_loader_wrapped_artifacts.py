"""Exercise real wrapped admin runs and protect their candidate/report paths."""
import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WrappedArtifactBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='loader-artifacts-')
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.candidate = self.work / 'candidate.so'
        shutil.copyfile(ROOT / 'evidence/original/pump/deployed.so', self.candidate)
        self.candidate_bytes = self.candidate.read_bytes()
        self.report = self.work / 'report.json'
        self.receipt = self.work / 'loader.json'

    def make_link(self, target, alias, kind):
        try:
            if kind == 'symlink':
                alias.symlink_to(target)
            else:
                os.link(target, alias)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EPERM, errno.ENOSYS, errno.ENOTSUP):
                self.skipTest(f'{kind} unavailable on this platform: {error}')
            raise

    def invoke(self, receipt, *, equals=False, extra=(), abbreviated=False):
        candidate, output = ('--cand', '--out') if abbreviated else ('--candidate', '--output')
        args = ([f'{candidate}={self.candidate}', f'{output}={self.report}'] if equals else
                [candidate, str(self.candidate), output, str(self.report)])
        return subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/pump_with_captured_loader.py'),
                               '--receipt', str(receipt), str(ROOT / 'scripts/pump_validate_admin.py'),
                               *extra, *args], cwd=self.work, capture_output=True, text=True, timeout=180)

    def reject(self, receipt, equals):
        result = self.invoke(receipt, equals=equals)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('receipt path aliases protected input', result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(self.candidate.read_bytes(), self.candidate_bytes)

    def test_candidate_aliases_are_refused_in_both_option_forms(self):
        for kind in ('direct', 'symlink', 'hardlink'):
            alias = self.candidate if kind == 'direct' else self.work / kind
            if kind == 'symlink':
                self.make_link(self.candidate, alias, kind)
            elif kind == 'hardlink':
                self.make_link(self.candidate, alias, kind)
            for equals in (False, True):
                with self.subTest(kind=kind, equals=equals):
                    self.reject(alias, equals)
                    self.assertFalse(self.report.exists())

    def test_pending_report_path_and_symlink_are_refused(self):
        alias = self.work / 'report-link'
        self.make_link(self.report, alias, 'symlink')
        for receipt in (self.report, alias):
            for equals in (False, True):
                with self.subTest(receipt=receipt.name, equals=equals):
                    self.reject(receipt, equals)
                    self.assertFalse(self.report.exists())

    def test_existing_report_hardlink_is_refused(self):
        self.report.write_bytes(b'previous report\n')
        alias = self.work / 'report-hardlink'
        self.make_link(self.report, alias, 'hardlink')
        for equals in (False, True):
            self.reject(alias, equals)
            self.assertEqual(self.report.read_bytes(), b'previous report\n')

    def test_distinct_receipt_can_be_reused_with_real_corpus(self):
        for equals in (False, True):
            result = self.invoke(self.receipt, equals=equals)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(self.report.read_bytes())
            receipt = json.loads(self.receipt.read_bytes())
            self.assertEqual(report['case_count'], 93)
            self.assertEqual(report['mismatches'], [])
            self.assertIs(receipt['ok'], True)
            self.assertTrue(receipt['loads'])
            self.assertEqual(self.candidate.read_bytes(), self.candidate_bytes)

    def test_last_documented_path_option_wins(self):
        result = self.invoke(self.receipt, extra=('--candidate', str(self.receipt),
                                                 '--output=' + str(self.receipt)))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(self.report.read_bytes())['case_count'], 93)
        self.assertIs(json.loads(self.receipt.read_bytes())['ok'], True)

    def test_argparse_abbreviations_preserve_candidate_and_report(self):
        for equals in (False, True):
            for receipt in (self.candidate, self.report):
                with self.subTest(equals=equals, receipt=receipt.name):
                    result = self.invoke(receipt, equals=equals, abbreviated=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('receipt path aliases protected input', result.stderr)
                    self.assertEqual(result.stdout, '')
                    self.assertEqual(self.candidate.read_bytes(), self.candidate_bytes)
                    self.assertFalse(self.report.exists())

    def test_abbreviated_options_keep_last_occurrence_semantics(self):
        result = self.invoke(self.receipt, extra=('--candidate', str(self.receipt),
                                                 '--output=' + str(self.receipt)), abbreviated=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(self.report.read_bytes())['case_count'], 93)
        self.assertIs(json.loads(self.receipt.read_bytes())['ok'], True)


if __name__ == '__main__':
    unittest.main()
