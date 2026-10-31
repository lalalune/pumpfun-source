#!/usr/bin/env python3
"""Retained patterns remain bounded while aggregate counts include all matches."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deep_section_analysis as analysis
from window_elf_reader import Elf

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'associated_token': 86, 'donation_relay': 483, 'spl_token': 24,
    'spl_token_2022': 420, 'token_metadata': 314, 'mayhem': 441,
    'pump': 1208, 'pump_amm': 742, 'pump_fees': 578,
}


class SectionPatternCountTests(unittest.TestCase):
    def test_retained_totals_distinguish_complete_and_capped_examples(self):
        captures = sorted((ROOT / 'evidence').glob('*/*/deployed.so'))
        self.assertEqual({path.parent.name for path in captures}, set(EXPECTED))
        for path in captures:
            with self.subTest(program=path.parent.name):
                result = analysis.recover_anchor_idl(Elf(path))
                expected = EXPECTED[path.parent.name]
                self.assertEqual(result['deserialization_pattern_count'], expected)
                self.assertEqual(result['displayed_deserialization_pattern_count'], min(expected, 100))
                self.assertEqual(len(result['deserialization_patterns']), min(expected, 100))

    def test_actual_pump_cli_publishes_total_and_displayed_count_consistently(self):
        capture = ROOT / 'evidence/original/pump/deployed.so'
        before = hashlib.sha256(capture.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix='section-pattern-count-') as temporary:
            output = Path(temporary) / 'packet'
            result = subprocess.run([
                sys.executable, '-B', str(ROOT / 'scripts/deep_section_analysis.py'),
                '--program', 'pump', '--output', str(output),
            ], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads((output / 'summary.json').read_text())['layer4_anchor_idl']
            layer = json.loads((output / 'layer4-anchor-idl.json').read_text())
            self.assertEqual(summary['deser_patterns'], 1208)
            self.assertEqual(summary['displayed_deser_patterns'], 100)
            self.assertEqual(layer['deserialization_pattern_count'], summary['deser_patterns'])
            self.assertEqual(len(layer['deserialization_patterns']), summary['displayed_deser_patterns'])
            self.assertIn('Deserialization patterns: 1208 (100 displayed)',
                          (output / 'README.md').read_text())
            verified = subprocess.run([sys.executable, '-B', str(output / 'verify.py')],
                                      cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertEqual(hashlib.sha256(capture.read_bytes()).hexdigest(), before)


if __name__ == '__main__':
    unittest.main()
