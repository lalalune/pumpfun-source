"""Tooling packet verifiers must refuse optimized Python instead of printing a report."""
from pathlib import Path
import os, subprocess, sys, unittest
ROOT = Path(__file__).resolve().parents[1]
PACKETS = (
    'research/tooling-legacy-capture-metadata-20261029',
    'research/tooling-roadmap-call-classification-20261029',
    'research/tooling-source-manifest-symlinks-20261029',
    'research/tooling-token-program-constant-detector-20261029',
)
GUARD = 'Normal Python is required; do not use -O.'


class OptimizedPacketVerifiers(unittest.TestCase):

    def test_optimized_runs_exit_with_the_guard_message(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        for packet in PACKETS:
            for flag in ('-O', '-OO'):
                with self.subTest(packet=packet, flag=flag):
                    result = subprocess.run(
                        [sys.executable, flag, '-B', str(ROOT / packet / 'verify.py'), '--repo', str(ROOT)],
                        cwd=ROOT, env=env, capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, '')
                    self.assertIn(GUARD, result.stderr)


if __name__ == '__main__':
    unittest.main()
