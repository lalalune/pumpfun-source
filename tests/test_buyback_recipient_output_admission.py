"""The buyback recipient differential must refuse a symlinked ``--output``.

It admitted a destination with ``args.output.exists()``, which is False for a
dangling symlink, and then wrote the receipt with ``write_text``, which follows
the link. A dangling ``--output`` therefore left the requested path a dangling
link, published the whole report in another directory and exited 0, so the
"fresh output path" guard did not guard the path that was actually written.

The fresh-path control runs the real 42-case differential, so it also proves
the admission change leaves normal publication untouched.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/pump_buyback_recipient_differential.py'
CANDIDATE = ROOT / 'evidence/original/pump/deployed.so'


class BuybackRecipientOutputAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='buyback-output-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'private root'
        self.root.mkdir()

    def run_cli(self, output):
        return subprocess.run(
            [sys.executable, '-B', str(SCRIPT), '--candidate', str(CANDIDATE),
             '--output', str(output)],
            cwd=ROOT, capture_output=True, text=True, timeout=300)

    def test_dangling_output_symlink_is_refused_before_the_run(self):
        destination = self.root / 'escaped dir' / 'escaped report.json'
        destination.parent.mkdir()
        output = self.root / 'report.json'
        output.symlink_to(destination)
        result = self.run_cli(output)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('Use a fresh output path', result.stderr)
        self.assertFalse(os.path.lexists(destination))
        self.assertTrue(output.is_symlink())

    def test_existing_output_file_is_refused_unchanged(self):
        output = self.root / 'report.json'
        output.write_text('keep me\n', encoding='utf-8')
        result = self.run_cli(output)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('Use a fresh output path', result.stderr)
        self.assertEqual(output.read_text(encoding='utf-8'), 'keep me\n')

    def test_fresh_output_still_publishes_the_full_report(self):
        output = self.root / 'nested' / 'reports' / 'report.json'
        result = self.run_cli(output)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual(receipt['case_count'], 42)
        self.assertEqual(receipt['mismatches'], [])


if __name__ == '__main__':
    unittest.main()
