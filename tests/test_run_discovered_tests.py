"""The discovery runner must refuse a run that finds fewer cases than stated."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_discovered_tests.py"
CASE_FILE = """
import unittest


class Cases(unittest.TestCase):
    def test_first(self):
        pass

    def test_second(self):
        pass
"""


class DiscoveredTestsRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        (self.directory / "cases.py").write_text(CASE_FILE)

    def run_runner(self, *arguments):
        return subprocess.run([sys.executable, "-B", str(RUNNER), str(self.directory),
                               "cases.py", *arguments], capture_output=True, text=True)

    def test_the_shipped_count_passes(self):
        completed = self.run_runner("--expect", "2")
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Expected 2 cases; ran 2; skipped 0", completed.stderr)

    def test_a_count_the_pattern_no_longer_meets_is_refused(self):
        completed = self.run_runner("--expect", "3")
        self.assertEqual(1, completed.returncode)
        self.assertIn("Expected 3 cases; ran 2", completed.stderr)

    def test_a_pattern_that_matches_nothing_is_refused(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(RUNNER), str(self.directory), "missing*.py",
             "--expect", "1"], capture_output=True, text=True)
        self.assertEqual(1, completed.returncode)
        self.assertIn("ran 0", completed.stderr)


    def test_zero_expected_does_not_admit_empty_discovery(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(RUNNER), str(self.directory), "missing*.py",
             "--expect", "0"], capture_output=True, text=True)
        self.assertEqual(2, completed.returncode)
        self.assertIn("--expect must be positive", completed.stderr)

    def test_all_skipped_is_refused_at_the_expected_count(self):
        (self.directory / "cases.py").write_text(
            CASE_FILE.replace("class Cases", "@unittest.skip('control')\nclass Cases"))
        completed = self.run_runner("--expect", "2")
        self.assertEqual(1, completed.returncode)
        self.assertIn("ran 2; skipped 2", completed.stderr)


if __name__ == "__main__":
    unittest.main()
