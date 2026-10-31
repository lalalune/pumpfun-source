"""Run both offline analyzers against the repository's retained program captures."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeepAnalysisCaptureRoutes(unittest.TestCase):
    def generate(self, tool, program, group):
        capture = ROOT / 'evidence' / group / program / 'deployed.so'
        self.assertTrue(capture.is_file(), capture)
        # The regression must exercise the dependency route, with no duplicate
        # original-group capture available to hide the lookup error.
        if group == 'dependencies':
            self.assertFalse((ROOT / 'evidence/original' / program).exists())
        with tempfile.TemporaryDirectory(prefix='deep-capture-route-') as temporary:
            output = Path(temporary) / 'packet'
            completed = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts' / (tool + '.py')),
                 '--program', program, '--output', str(output)],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            summary = json.loads((output / 'summary.json').read_bytes())
            self.assertEqual(summary['deployed_sha256'],
                             hashlib.sha256(capture.read_bytes()).hexdigest())
            verified = subprocess.run([sys.executable, '-I', '-B', str(output / 'verify.py')],
                                      capture_output=True, text=True, timeout=20)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

    def test_deep_disassembly_reads_relay_dependency(self):
        self.generate('deep_disassembly', 'donation_relay', 'dependencies')

    def test_deep_section_reads_relay_dependency(self):
        self.generate('deep_section_analysis', 'donation_relay', 'dependencies')

    def test_deep_disassembly_keeps_original_program_route(self):
        self.generate('deep_disassembly', 'mayhem', 'original')

    def test_deep_section_keeps_original_program_route(self):
        self.generate('deep_section_analysis', 'mayhem', 'original')


if __name__ == '__main__':
    unittest.main()
