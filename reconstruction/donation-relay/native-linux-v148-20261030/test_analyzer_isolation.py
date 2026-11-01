#!/usr/bin/env python3
"""The checkout's analyzer must not be able to reach the verifier's own checks.

verify.py executes the checkout's scripts/analyze.py as part of the
verification and then uses the number it returns. Executed in the verifier's
process, that module shares the verifier's globals: replacing
`sys.modules['__main__'].require` makes every require() after it pass, so a
doctored analyze.py reports a passing check on any input.
"""

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify

TAMPERING_ANALYZER = '''
import sys
sys.modules['__main__'].require = lambda *args, **kwargs: None


def elf_layout(data):
    return {'elf_extent': 1}
'''

# Runs the verifier's helper with a require() the analyzer would replace.
ISOLATED_DRIVER = '''
import sys
sys.path.insert(0, sys.argv[1])
import verify


def original(*args, **kwargs):
    return None


require = original
verify.elf_extent(sys.argv[2], b'\\x7fELF')
print('replaced' if globals()['require'] is not original else 'intact')
'''

# The execution shape verify.py used before: the analyzer runs in this process.
IN_PROCESS_DRIVER = '''
import importlib.util, sys


def original(*args, **kwargs):
    return None


require = original
spec = importlib.util.spec_from_file_location('_relay_official_analyze', sys.argv[2])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print('replaced' if globals()['require'] is not original else 'intact')
'''


def run(driver, analyzer):
    import subprocess
    return subprocess.run([sys.executable, '-c', driver, str(HERE), str(analyzer)],
                          capture_output=True, text=True)


class AnalyzerIsolationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        (self.repo / 'scripts').mkdir()
        self.analyzer = self.repo / 'scripts' / 'analyze.py'
        self.analyzer.write_text(TAMPERING_ANALYZER, encoding='utf-8')

    def test_extent_is_returned_from_a_child_process(self):
        result = run(ISOLATED_DRIVER, self.analyzer)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('intact', result.stdout.strip())

    def test_in_process_execution_is_what_the_tampering_needs(self):
        """Control: the old execution shape hands the analyzer the caller's globals."""
        result = run(IN_PROCESS_DRIVER, self.analyzer)
        self.assertEqual('replaced', result.stdout.strip())

    def test_failed_malformed_or_out_of_range_answer_is_rejected(self):
        for code in ("print('not JSON')", "import sys; print('bad', file=sys.stderr)",
                     "raise SystemExit(3)", "def elf_layout(data): return {'elf_extent': True}",
                     "def elf_layout(data): return {'elf_extent': -1}",
                     "def elf_layout(data): return {'elf_extent': 1000}"):
            with self.subTest(code=code):
                self.analyzer.write_text(code)
                with self.assertRaises(ValueError):
                    verify.elf_extent(self.analyzer, b'ELF')

    def test_child_timeout_is_a_failure(self):
        self.analyzer.write_text('import time\ntime.sleep(10)\n')
        with self.assertRaisesRegex(ValueError, 'timed out'):
            verify.elf_extent(self.analyzer, b'ELF', timeout=0.05)

    def test_helper_returns_the_analyzer_number(self):
        self.assertEqual(1, verify.elf_extent(self.analyzer, b'\x7fELF'))


if __name__ == '__main__':
    unittest.main()
