import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import match_oracle as oracle

class PreservationTests(unittest.TestCase):
    def run_case(self, candidate, baseline=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'out'; out.mkdir()
            for name in ['original.so', 'functions.tsv']:
                (root / name).write_bytes(b'fixture')
            before = baseline or {8: {'bytes': 8, 'normalized': False, 'raw': False},
                                  16: {'bytes': 8, 'normalized': True, 'raw': True}}
            raw = json.dumps({'windows': {str(k): v for k, v in before.items()}}).encode()
            path = root / 'reference.json'; path.write_bytes(raw)
            with patch.object(oracle.score, 'BASE', root), patch.object(oracle.score, 'original_windows',
                    return_value=[{'start': 8, 'bytes': 8}, {'start': 16, 'bytes': 8}]), \
                 patch.object(oracle.fastbuild, 'build', return_value={'ok': True}) as build, \
                 patch.object(oracle.score, 'score', return_value=candidate):
                try:
                    code = oracle.evaluate(root, root / 'work', out, 8, 'normalized', 'identity', path)
                except ValueError:
                    self.assertFalse(build.called)
                    raise
            self.assertEqual(path.read_bytes(), raw)
            report = json.loads((out / 'verdict.json').read_text())
            self.assertEqual(report['baseline_sha256'], hashlib.sha256(raw).hexdigest())
            return code, report

    def test_target_gain_cannot_hide_raw_or_normalized_loss(self):
        for normalized in [True, False]:
            code, report = self.run_case({8: {'bytes': 8, 'normalized': True, 'raw': False},
                                         16: {'bytes': 8, 'normalized': normalized, 'raw': False}})
            self.assertEqual(code, 1)
            self.assertEqual(report['status'], 'fail')
            self.assertEqual(report['preservation']['raw_losses'], ['0x10'])

    def test_gain_with_preservation_passes(self):
        code, report = self.run_case({8: {'bytes': 8, 'normalized': True, 'raw': False},
                                     16: {'bytes': 8, 'normalized': True, 'raw': True}})
        self.assertEqual(code, 0)
        self.assertTrue(report['preservation']['accepted'])

    def test_inventory_drift_rejected_before_build(self):
        for baseline in [{8: {'bytes': 8, 'normalized': False, 'raw': False}},
                         {8: {'bytes': 8, 'normalized': False, 'raw': False},
                          16: {'bytes': 16, 'normalized': True, 'raw': True}}]:
            with self.assertRaisesRegex(ValueError, 'selected original inventory'):
                self.run_case({}, baseline)

if __name__ == '__main__': unittest.main()
