import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import check_workflow_inputs as check


class WorkflowInputsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.write('scripts/ok.py', 'pass\n')
        self.workflow('python -B scripts/ok.py\n          python scripts/old-missing.py')
        self.git('add', '.')
        self.git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'baseline')

    def git(self, *args):
        return check.git(self.root, *args)

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def workflow(self, commands):
        self.write('.github/workflows/test.yml', 'name: test\non: [push]\njobs:\n  test:\n    steps:\n      - run: |\n          ' + commands + '\n')

    def run_check(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            result = check.main(['--repo', str(self.root), *args])
        return result, json.loads(out.getvalue())

    def test_existing_debt_is_visible_but_new_deletion_fails(self):
        status, report = self.run_check('--base', 'HEAD')
        self.assertEqual(status, 0)
        self.assertEqual(len(report['existing_missing']), 1)
        (self.root / 'scripts/ok.py').unlink()
        status, report = self.run_check('--base', 'HEAD')
        self.assertEqual(status, 1)
        self.assertEqual(report['new_missing'][0][2], 'scripts/ok.py')

    def test_new_bad_command_fails_and_removed_workflow_does_not(self):
        self.workflow('python scripts/typo.py')
        self.assertEqual(self.run_check('--base', 'HEAD')[0], 1)
        (self.root / '.github/workflows/test.yml').unlink()
        self.assertEqual(self.run_check('--base', 'HEAD')[0], 0)

    def test_full_audit_fails_existing_debt(self):
        self.assertEqual(self.run_check('--all')[0], 1)

    def test_committed_head_checks_deleted_files(self):
        self.git('rm', 'scripts/ok.py')
        self.git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'delete')
        self.assertEqual(self.run_check('--base', 'HEAD^', '--head', 'HEAD')[0], 1)

    def test_matrix_commands_and_working_directory(self):
        source = '''jobs:
  test:
    strategy:
      matrix:
        include:
          - commands: python -I -B -X utf8 ok.py
          - commands: bash missing.sh
    defaults:
      run:
        working-directory: scripts
    steps:
      - run: ${{ matrix.commands }}
'''
        refs, _ = check.references('test.yml', source)
        self.assertEqual({r[2] for r in refs}, {'scripts/ok.py', 'scripts/missing.sh'})

    def test_inline_modules_generated_and_dynamic_are_not_missing_inputs(self):
        source = '''jobs:
  test:
    steps:
      - run: |
          python -m pip install something
          python -c "print('research/not-a-script.py')"
          python work/generated.py
          python $SCRIPT
'''
        refs, unsupported = check.references('test.yml', source)
        self.assertFalse(refs)
        self.assertEqual(len(unsupported), 2)

    def test_research_cleanup_reports_all_eight_entrypoints(self):
        packages = ['amm-event-capture-independent-replay',
                    'amm-current-event-capture-20261027',
                    'amm-pool-preparation-boundaries',
                    'pump-amm-migration-composition']
        paths = [f'research/{package}/{script}.py' for package in packages
                 for script in ('verify', 'test_verify')]
        for path in paths:
            self.write(path, 'pass\n')
        self.workflow('\n          '.join('python -B ' + path for path in paths))
        self.git('add', '.')
        self.git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'research baseline')
        for path in paths:
            (self.root / path).unlink()
        status, report = self.run_check('--base', 'HEAD')
        self.assertEqual(status, 1)
        self.assertEqual({r[2] for r in report['new_missing']}, set(paths))

    def test_matrix_axes_and_step_directory_override(self):
        refs, _ = check.references('test.yml', """jobs:
  test:
    strategy:
      matrix:
        script: [one.py, two.py]
    defaults:
      run:
        working-directory: research
    steps:
      - run: python ${{ matrix.script }}
        working-directory: scripts
""")
        self.assertEqual({r[2] for r in refs}, {'scripts/one.py', 'scripts/two.py'})

    def test_include_only_additions_remain_separate_and_missing_input_fails(self):
        matrix = {'os': ['linux'], 'include': [
            {'os': 'macos', 'script': 'one.py'},
            {'os': 'macos', 'script': 'two.py'}]}
        self.assertEqual(check.matrix_rows({'strategy': {'matrix': matrix}}),
                         [{'os': 'linux'}, *matrix['include']])
        self.write('scripts/two.py', 'pass\n')
        self.write('.github/workflows/test.yml', """jobs:
  test:
    strategy:
      matrix:
        os: [linux]
        include:
          - {os: macos, script: one.py}
          - {os: macos, script: two.py}
    steps:
      - run: python scripts/${{ matrix.script }}
""")
        status, report = self.run_check('--base', 'HEAD')
        self.assertEqual(status, 1)
        self.assertEqual([r[2] for r in report['new_missing']], ['scripts/one.py'])

    def test_partial_added_combinations_do_not_require_every_axis(self):
        matrix = {'version': [1, 2], 'os': ['linux', 'windows'],
                  'include': [{'version': 3}, {'os': 'macos'}]}
        self.assertEqual(check.matrix_rows({'strategy': {'matrix': matrix}}), [
            {'version': 1, 'os': 'linux'}, {'version': 1, 'os': 'windows'},
            {'version': 2, 'os': 'linux'}, {'version': 2, 'os': 'windows'},
            {'version': 3}, {'os': 'macos'}])

    def test_later_include_can_override_added_fields_on_original_rows(self):
        matrix = {'fruit': ['apple', 'pear'], 'animal': ['cat', 'dog'],
                  'include': [{'color': 'green'}, {'color': 'pink', 'animal': 'cat'},
                              {'fruit': 'apple', 'shape': 'circle'},
                              {'fruit': 'banana'}, {'fruit': 'banana', 'animal': 'cat'}]}
        self.assertEqual(check.matrix_rows({'strategy': {'matrix': matrix}}), [
            {'fruit': 'apple', 'animal': 'cat', 'color': 'pink', 'shape': 'circle'},
            {'fruit': 'apple', 'animal': 'dog', 'color': 'green', 'shape': 'circle'},
            {'fruit': 'pear', 'animal': 'cat', 'color': 'pink'},
            {'fruit': 'pear', 'animal': 'dog', 'color': 'green'},
            {'fruit': 'banana'}, {'fruit': 'banana', 'animal': 'cat'}])

    def test_malformed_yaml_fails_closed(self):
        self.write('.github/workflows/test.yml', 'jobs: [')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            self.run_check('--base', 'HEAD')
        self.assertEqual(error.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
