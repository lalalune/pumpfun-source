"""The scorer refuses a candidate other than the bytes a build reported."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
import score

# The captured images are stripped; with no expected digest the scorer stops at
# the symbol check, which is what distinguishes the gate from ordinary scoring.
CANDIDATE = ROOT / 'reconstruction/base/original.so'


class ScoreBindingTests(unittest.TestCase):
    def test_bytes_other_than_the_build_report_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'do not match the bytes the build published'):
            score.score(CANDIDATE, '0' * 64)

    def test_unbound_bytes_reach_the_symbol_check(self):
        with self.assertRaisesRegex(ValueError, 'no function symbols'):
            score.score(CANDIDATE)


if __name__ == '__main__':
    unittest.main()
