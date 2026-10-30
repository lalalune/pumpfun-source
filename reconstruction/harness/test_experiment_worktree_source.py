"""A linked Git worktree or submodule stores .git as a file, not a directory.

Staging omits that name, so the source identity has to omit it too or the runner
reports a change that never happened.
"""
import sys
import tempfile
import unittest
from pathlib import Path

from experiment_runner import manifest, run_trial

READ_VALUE = ("from pathlib import Path; import sys; "
              "raise SystemExit(0 if Path(sys.argv[1], 'value').is_file() else 1)")


class WorktreeSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'value').write_text('source\n', encoding='utf-8')
        self.command = [sys.executable, '-c', READ_VALUE, '{source}']

    def test_worktree_root_runs_like_a_plain_directory(self):
        plain = manifest(self.source)
        (self.source / '.git').write_text('gitdir: /elsewhere/.git/worktrees/lane\n', encoding='utf-8')
        self.assertEqual(manifest(self.source), plain)
        result = run_trial(self.source, self.command, self.root / 'trial')
        self.assertEqual((result['status'], result['returncode']), ('pass', 0))

    def test_nested_submodule_marker_is_omitted_too(self):
        (self.source / 'vendor/dep').mkdir(parents=True)
        (self.source / 'vendor/dep/lib.rs').write_text('// source\n', encoding='utf-8')
        plain = manifest(self.source)
        (self.source / 'vendor/dep/.git').write_text('gitdir: ../../.git/modules/dep\n', encoding='utf-8')
        self.assertEqual(manifest(self.source), plain)
        result = run_trial(self.source, self.command, self.root / 'trial')
        self.assertEqual((result['status'], result['returncode']), ('pass', 0))

    def test_real_source_changes_are_still_detected(self):
        before = manifest(self.source)
        (self.source / 'value').write_text('changed\n', encoding='utf-8')
        self.assertNotEqual(manifest(self.source), before)


if __name__ == '__main__':
    unittest.main()
