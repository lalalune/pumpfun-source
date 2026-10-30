"""The call-sequence report must preserve existing paths before reading ELF inputs."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).with_name('callseq.py')

class ReportAdmission(unittest.TestCase):
    def test_existing_report_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary)/'report.json'
            report.write_bytes(b'prior report\n')
            result = subprocess.run([sys.executable, '-B', str(TOOL), '--cand', 'missing.so',
                                     '--orig-names', 'missing.so', '--json', str(report)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('report already exists', result.stderr)
            self.assertEqual(report.read_bytes(), b'prior report\n')

    def test_dangling_output_link_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary)/'report.json'; target = Path(temporary)/'missing'
            report.symlink_to(target)
            result = subprocess.run([sys.executable, '-B', str(TOOL), '--cand', 'missing.so',
                                     '--orig-names', 'missing.so', '--json', str(report)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('report already exists', result.stderr)
            self.assertTrue(report.is_symlink())
            self.assertFalse(target.exists())

if __name__ == '__main__':
    unittest.main()
