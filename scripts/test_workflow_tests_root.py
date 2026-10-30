"""Workflow commands that run tests/*.py must have their inputs checked too.

verify.yml runs many `python -B tests/test_*.py` commands. The checker only
treated scripts/, research/ and reconstruction/ as checked roots, so a
reference to a missing tests/ file was reported as "outside checked roots"
and the check still passed.
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import check_workflow_inputs as check


class TestsRootTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        check.git(self.root, 'init', '-q')
        self.write('tests/test_ok.py', 'pass\n')
        self.workflow('python -B tests/test_ok.py')
        check.git(self.root, 'add', '.')
        check.git(self.root, '-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
                  '-c', 'commit.gpgsign=false', 'commit', '-qm', 'baseline')

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def workflow(self, commands):
        self.write('.github/workflows/test.yml',
                   'name: test\non: [push]\njobs:\n  test:\n    steps:\n      - run: |\n          '
                   + commands + '\n')

    def run_check(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            status = check.main(['--repo', str(self.root), '--base', 'HEAD'])
        return status, json.loads(out.getvalue())

    def test_existing_tests_input_is_checked_not_skipped(self):
        status, report = self.run_check()
        self.assertEqual(status, 0)
        self.assertEqual(report['checked_references'], 1)
        self.assertEqual(report['uninspected'], [])

    def test_new_missing_tests_input_fails(self):
        self.workflow('python -B tests/test_ok.py\n          python -I -B tests/test_typo.py')
        status, report = self.run_check()
        self.assertEqual(status, 1)
        self.assertEqual([row[2] for row in report['new_missing']], ['tests/test_typo.py'])

    def test_deleted_tests_input_fails(self):
        (self.root / 'tests/test_ok.py').unlink()
        status, report = self.run_check()
        self.assertEqual(status, 1)
        self.assertEqual([row[2] for row in report['new_missing']], ['tests/test_ok.py'])


if __name__ == '__main__':
    unittest.main()
