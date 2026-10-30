"""Real filesystem locks protect trials; no compiler or VM is invoked."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fastbuild


class WorkspaceLockTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.work = self.root / 'work'

    def test_contention_rejects_before_staging(self):
        with fastbuild.workspace_lock(self.work), patch.object(fastbuild, 'stage') as stage:
            with self.assertRaisesRegex(RuntimeError, 'already in use'):
                fastbuild.build(self.root / 'source', self.work, self.root / 'output')
            stage.assert_not_called()

    def test_lock_is_held_for_entire_build(self):
        def trial(*args, **kwargs):
            with self.assertRaisesRegex(RuntimeError, 'already in use'):
                with fastbuild.workspace_lock(self.work):
                    self.fail('same workspace admitted')
            return {'ok': True}
        with patch.object(fastbuild, '_build_locked', side_effect=trial):
            self.assertEqual(fastbuild.build(self.root, self.work, self.root / 'out'), {'ok': True})

    def test_failure_releases_lock_and_preserves_inode(self):
        with patch.object(fastbuild, '_build_locked', side_effect=ValueError('trial failed')):
            with self.assertRaisesRegex(ValueError, 'trial failed'):
                fastbuild.build(self.root, self.work, self.root / 'out')
        inode = (self.work / '.fastbuild.lock').stat().st_ino
        with fastbuild.workspace_lock(self.work):
            self.assertEqual((self.work / '.fastbuild.lock').stat().st_ino, inode)

    def test_different_workspaces_are_independent(self):
        with fastbuild.workspace_lock(self.work), fastbuild.workspace_lock(self.root / 'other'):
            pass

    def test_symlink_alias_cannot_bypass_lock(self):
        self.work.mkdir()
        alias = self.root / 'alias'
        alias.symlink_to(self.work, target_is_directory=True)
        with fastbuild.workspace_lock(self.work), self.assertRaisesRegex(RuntimeError, 'already in use'):
            with fastbuild.workspace_lock(alias):
                self.fail('alias admitted')

    def test_separate_process_observes_contention_and_release(self):
        script = (
            'import sys; from pathlib import Path; import fastbuild\n'
            'try:\n'
            ' with fastbuild.workspace_lock(Path(sys.argv[1])): pass\n'
            'except RuntimeError: sys.exit(7)\n'
        )
        command = [sys.executable, '-B', '-c', script, str(self.work)]
        with fastbuild.workspace_lock(self.work):
            result = subprocess.run(command, cwd=Path(fastbuild.__file__).parent, capture_output=True)
            self.assertEqual(result.returncode, 7, result.stderr)
        result = subprocess.run(command, cwd=Path(fastbuild.__file__).parent, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
