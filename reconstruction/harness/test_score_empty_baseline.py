"""An explicit empty baseline must not conceal lost Pump windows."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import score
from test_elf_symbols import fixture

class EmptyBaselineTests(unittest.TestCase):
    def test_empty_saved_baseline_is_rejected_but_opt_out_is_available(self):
        original = next(w for w in score.original_windows()
                        if w['bytes'] == 8 and w['raw'][0] != 0x18)
        image = fixture()
        image[424:432] = original['raw']
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / 'candidate.so'
            candidate.write_bytes(image)
            baseline = root / 'baseline.json'
            report = root / 'report.json'
            for windows in ({}, []):
                with self.subTest(windows=windows):
                    baseline.write_text(json.dumps({'windows': windows}), encoding='utf-8')
                    argv = ['score.py', str(candidate), '--baseline', str(baseline), '--json', str(report)]
                    with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaisesRegex(ValueError, 'nonempty'):
                            score.main()
                    self.assertFalse(report.exists())
            argv = ['score.py', str(candidate), '--no-baseline', '--json', str(report), '--quiet']
            with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                score.main()
            summary = json.loads(report.read_text(encoding='utf-8'))['summary']
            self.assertGreater(summary['normalized'], 0)
            self.assertFalse(summary['losses'])

if __name__ == '__main__':
    unittest.main()
