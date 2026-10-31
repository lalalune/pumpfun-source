"""capir.py must load the harness from its own checkout."""
from pathlib import Path
import subprocess
import sys
import unittest

TOOL = Path(__file__).with_name('tools') / 'capir.py'


class HarnessPathTests(unittest.TestCase):
    def test_tool_starts_from_any_checkout(self):
        result = subprocess.run([sys.executable, '-B', str(TOOL), '--help'], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--src', result.stdout)


if __name__ == '__main__':
    unittest.main()
