"""Experiment commands must run under the name they were declared with.

Virtual environments and rustup proxies select their behaviour from argv[0], so
starting only the symlink target runs a different command than the one declared.
"""
import contextlib
import sys
import tempfile
import unittest
import venv
from pathlib import Path

from experiment_runner import run_trial

COMPARE_NAME = 'import sys; raise SystemExit(0 if sys.orig_argv[0] == sys.argv[1] else 1)'


class DeclaredNameTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'value').write_text('source\n', encoding='utf-8')

    def test_virtual_environment_interpreter_keeps_its_environment(self):
        venv.create(self.root / 'venv', symlinks=True, with_pip=False)
        python = self.root / 'venv/bin/python'
        in_venv = 'import sys; raise SystemExit(0 if sys.prefix != sys.base_prefix else 1)'
        result = run_trial(self.source, [str(python), '-c', in_venv], self.root / 'trial')
        self.assertEqual((result['status'], result['returncode']), ('pass', 0))

    def test_symlinked_tool_starts_the_hashed_binary_under_its_declared_name(self):
        real = Path(sys.executable).resolve()
        tool = self.root / 'cargo'
        tool.symlink_to(real)
        result = run_trial(self.source, [str(tool), '-c', COMPARE_NAME, str(tool)], self.root / 'trial')
        self.assertEqual((result['status'], result['returncode']), ('pass', 0))
        self.assertIn(str(real), result['inputs']['inputs'])

    def test_relative_tool_still_starts_from_the_isolated_work_directory(self):
        tool = self.root / 'cargo'
        tool.symlink_to(Path(sys.executable).resolve())
        with contextlib.chdir(self.root):
            result = run_trial(self.source, ['./cargo', '-c', COMPARE_NAME, str(tool)], self.root / 'trial')
        self.assertEqual((result['status'], result['returncode']), ('pass', 0))


if __name__ == '__main__':
    unittest.main()
