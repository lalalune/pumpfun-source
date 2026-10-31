#!/usr/bin/env python3
"""Every Surfpool differential must compare the same number of cases per run.

The runners compare prepared fixtures against the original and candidate runs
positionally with zip, which stops at the shortest sequence. A run that returned
fewer rows than it was given therefore compared only a prefix and could still
report no mismatches.
"""
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from surfpool_recording_vm import require_aligned_runs  # noqa: E402

SCRIPTS = sorted((ROOT / 'scripts').glob('*_surfpool.py'))


class SurfpoolRunAlignmentTests(unittest.TestCase):
    def test_equal_runs_are_admitted(self):
        require_aligned_runs([1, 2], [1, 2], [1, 2])
        require_aligned_runs([], [], [])

    def test_short_run_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'do not cover the same cases'):
            require_aligned_runs([1, 2], [1, 2], [1])
        with self.assertRaisesRegex(ValueError, 'do not cover the same cases'):
            require_aligned_runs([1, 2], [1], [1, 2])
        with self.assertRaisesRegex(ValueError, 'do not cover the same cases'):
            require_aligned_runs([1], [], [1])

    def test_every_surfpool_differential_calls_the_guard(self):
        self.assertGreaterEqual(len(SCRIPTS), 16)
        for path in SCRIPTS:
            with self.subTest(script=path.name):
                tree = ast.parse(path.read_text(encoding='utf-8'))
                calls = [node for node in ast.walk(tree)
                         if isinstance(node, ast.Call)
                         and isinstance(node.func, ast.Name)
                         and node.func.id == 'require_aligned_runs']
                self.assertEqual(len(calls), 1, 'guard must be called once')


if __name__ == '__main__':
    unittest.main()
