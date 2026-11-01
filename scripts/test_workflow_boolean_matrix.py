"""Typed boolean matrix paths use GitHub's spelling, not Python's."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import check_workflow_inputs as check


class BooleanWorkflowMatrixTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        check.git(self.root, 'init', '-q')

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def workflow(self, axis):
        self.source = '''jobs:
  audit:
    strategy:
      matrix:
        flag: AXIS
    steps:
      - run: python -B scripts/flag-${{ matrix.flag }}.py
'''.replace('AXIS', axis)
        self.write('.github/workflows/test.yml', self.source)

    def run_check(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            status = check.main(['--repo', str(self.root), '--all'])
        return status, json.loads(output.getvalue())

    def test_boolean_paths_use_existing_lowercase_files(self):
        self.workflow('[true, false]')
        for flag in ('true', 'false'):
            self.write('scripts/flag-' + flag + '.py', 'pass\n')
        status, report = self.run_check()
        self.assertEqual(status, 0)
        self.assertEqual(report['checked_references'], 2)
        self.assertEqual(report['new_missing'], [])
        self.assertEqual(report['uninspected'], [])

    def test_uppercase_decoys_do_not_hide_missing_boolean_paths(self):
        self.workflow('[true, false]')
        for flag in ('True', 'False'):
            self.write('scripts/flag-' + flag + '.py', 'pass\n')
        # Git inventory names retain exact case even on a case-folding worktree.
        # The checker compares those names, matching the paths GitHub checks out.
        status, report = self.run_check()
        self.assertEqual(status, 1)
        self.assertEqual({row[2] for row in report['new_missing']},
                         {'scripts/flag-true.py', 'scripts/flag-false.py'})
        self.assertEqual(report['checked_references'], 2)
        self.assertEqual(report['uninspected'], [])

    def test_literal_uppercase_strings_keep_their_case(self):
        self.workflow('["True", "False"]')
        for flag in ('True', 'False'):
            self.write('scripts/flag-' + flag + '.py', 'pass\n')
        status, report = self.run_check()
        self.assertEqual(status, 0)
        self.assertEqual(report['new_missing'], [])
        found, unsupported = check.references('test.yml', self.source)
        self.assertEqual({row[2] for row in found},
                         {'scripts/flag-True.py', 'scripts/flag-False.py'})
        self.assertEqual(unsupported, set())


if __name__ == '__main__':
    unittest.main()
