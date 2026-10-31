#!/usr/bin/env python3
"""Every entry in a staged recipe must be a declared file or a real directory."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from verify_stage import verify

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.name == 'posix', 'needs POSIX links and pipes')
class StageRecipeEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='mayhem-stage-entries-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.stage = Path(cls.temporary.name) / 'stage'
        subprocess.run([sys.executable, '-B', str(ROOT / 'programs/mayhem/build_exact.py'), '--stage-only',
                        '--repo', str(ROOT), '--output', str(cls.stage)],
                       check=True, capture_output=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))

    def test_clean_stage_is_accepted(self):
        self.assertEqual(verify(ROOT, self.stage)['recipe_files'], 98)

    def test_undeclared_special_entries_are_rejected(self):
        extra = self.stage / 'recipe/controller/extra'
        makers = {
            'dangling link': lambda: extra.symlink_to('missing'),
            'directory link': lambda: extra.symlink_to(self.stage, target_is_directory=True),
            'fifo': lambda: os.mkfifo(extra),
        }
        for label, make in makers.items():
            with self.subTest(entry=label):
                make()
                try:
                    with self.assertRaisesRegex(ValueError, 'nonregular staged recipe entry'):
                        verify(ROOT, self.stage)
                finally:
                    extra.unlink()


if __name__ == '__main__':
    unittest.main()
