"""A stripped deployed image must not become a misleading scoring baseline."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import score
from test_elf_symbols import fixture

ROOT = Path(__file__).resolve().parents[2]

class ScoreSymbolAdmissionTests(unittest.TestCase):
    def test_deployed_stripped_pump_cannot_publish_a_baseline(self):
        candidate = ROOT / 'evidence/original/pump/deployed.so'
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / 'baseline.json'
            args = ['score.py', str(candidate), '--no-baseline', '--json', str(report), '--quiet']
            with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, 'function symbols'):
                    score.main()
            self.assertFalse(report.exists())

    def test_symbols_are_still_read_for_unstripped_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / 'candidate.so'
            image = fixture()
            candidate.write_bytes(image)
            raw = bytes(image[424:432])
            windows = [{'start': 0x1000, 'bytes': 8, 'raw': raw, 'norm': raw}]
            with patch.object(score, 'original_windows', return_value=windows):
                result, _ = score.score_with_hash(candidate)
            self.assertTrue(result[0x1000]['normalized'])
            self.assertTrue(result[0x1000]['raw'])

    def test_rejected_input_preserves_an_existing_report(self):
        candidate = ROOT / 'evidence/original/pump/deployed.so'
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / 'baseline.json'
            report.write_text('previous report', encoding='utf-8')
            args = ['score.py', str(candidate), '--no-baseline', '--json', str(report)]
            with patch.object(sys, 'argv', args):
                with self.assertRaisesRegex(ValueError, 'function symbols'):
                    score.main()
            self.assertEqual(report.read_text(encoding='utf-8'), 'previous report')

if __name__ == '__main__':
    unittest.main()
