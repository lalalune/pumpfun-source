import contextlib
import io
import json
import subprocess
import sys
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

    def test_absolute_interpreter_spellings_are_inspected(self):
        for command in ('/usr/bin/python3 scripts/typo.py',
                        '/usr/bin/env python3 scripts/typo.py',
                        '/bin/bash scripts/typo.sh'):
            with self.subTest(command=command):
                self.workflow(command)
                status, report = self.run_check('--base', 'HEAD')
                self.assertEqual(status, 1)
                expected = 'scripts/typo.py' if 'python' in command else 'scripts/typo.sh'
                self.assertIn(expected, [entry[2] for entry in report['new_missing']])

    def test_full_audit_fails_existing_debt(self):
        self.assertEqual(self.run_check('--all')[0], 1)

    def test_env_chdir_resolves_the_actual_script_and_detects_missing_inputs(self):
        for option in ('-C scripts', '--chdir scripts', '-Cscripts', '--chdir=scripts'):
            with self.subTest(option=option):
                self.workflow('env ' + option + ' python ok.py')
                status, report = self.run_check('--all')
                self.assertEqual(status, 0)
                self.assertEqual(report['checked_references'], 1)
                self.assertFalse(report['uninspected'])
                # The root-relative name exists, but env actually invokes
                # scripts/scripts/ok.py, which does not exist.
                self.workflow('env ' + option + ' python scripts/ok.py')
                status, report = self.run_check('--all')
                self.assertEqual(status, 1)
                self.assertEqual([entry[2] for entry in report['new_missing']],
                                 ['scripts/scripts/ok.py'])

    def test_env_chdir_uses_the_step_directory_without_changing_later_commands(self):
        self.write('scripts/nested.py', 'pass\n')
        self.workflow('env -C scripts python nested.py\n          python scripts/ok.py')
        status, report = self.run_check('--all')
        self.assertEqual(status, 0)
        self.assertEqual(report['checked_references'], 2)
        self.write('research/README.md', 'fixture\n')
        self.write('.github/workflows/test.yml', '''jobs:
  test:
    steps:
      - run: env -C ../scripts python ok.py
        working-directory: research
''')
        status, report = self.run_check('--all')
        self.assertEqual(status, 0)
        self.assertEqual(report['checked_references'], 1)

    def test_nonliteral_env_chdir_is_reported_as_uninspected(self):
        for directory in ('$CHECK_DIR', '$CHECK_DIR/..', '/outside'):
            with self.subTest(directory=directory):
                self.workflow('env -C ' + directory + ' python scripts/ok.py')
                _, report = self.run_check('--all')
                self.assertEqual(report['checked_references'], 0)
                self.assertEqual(report['uninspected'][0][2], 'dynamic command/directory')

    def test_clustered_python_value_options_resolve_the_script(self):
        self.write('scripts/probe.py', "print('cluster probe')\n")
        for options in (['-IBW', 'error'], ['-IBX', 'utf8'],
                        ['-I', '-BW', 'error'], ['-IBWmodule'], ['-IBXutf8']):
            with self.subTest(options=options):
                # Run a real interpreter to establish which token is the
                # script, rather than only testing a tokenization helper.
                native = subprocess.run([sys.executable, *options, 'scripts/probe.py'],
                                        cwd=self.root, capture_output=True, text=True)
                self.assertEqual(native.returncode, 0, native.stderr)
                self.assertEqual(native.stdout.strip(), 'cluster probe')
                self.workflow('python ' + ' '.join(options) + ' scripts/probe.py')
                status, report = self.run_check('--all')
                self.assertEqual(status, 0)
                self.assertEqual(report['checked_references'], 1)
                self.assertFalse(report['uninspected'])

    def test_clustered_python_option_cannot_hide_a_missing_script(self):
        self.workflow('python -IBW error scripts/missing.py')
        native = subprocess.run([sys.executable, '-IBW', 'error', 'scripts/missing.py'],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(native.returncode, 2)
        status, report = self.run_check('--all')
        self.assertEqual(status, 1)
        self.assertEqual([entry[2] for entry in report['new_missing']], ['scripts/missing.py'])

    def test_clustered_python_inline_modes_have_no_script_input(self):
        for command in ('python -IBc "print(1)"', 'python -IBm json.tool --help'):
            with self.subTest(command=command):
                self.workflow(command)
                status, report = self.run_check('--all')
                self.assertEqual(status, 0)
                self.assertEqual(report['checked_references'], 0)
                self.assertFalse(report['uninspected'])

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

    def test_retained_dependency_workflow_detects_deleted_script(self):
        repository = Path(__file__).resolve().parents[1]
        workflow = '.github/workflows/search-dependency.yml'
        script = 'scripts/search_dependency_commit.py'
        self.write(workflow, (repository / workflow).read_text(encoding='utf-8'))
        self.write(script, (repository / script).read_text(encoding='utf-8'))
        self.git('add', '.')
        self.git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'retained dependency workflow')
        self.assertEqual(self.run_check('--base', 'HEAD')[0], 0)
        (self.root / script).unlink()
        completed = subprocess.run([
            sys.executable, '-B', check.__file__, '--repo', str(self.root), '--base', 'HEAD',
        ], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual({tuple(row) for row in report['new_missing']}, {
            (workflow, job, script) for job in (
                'associated-token', 'token-metadata-plain',
                'token-metadata-resize', 'token-metadata-resize-padded')})

    def test_continuations_preserve_shell_quote_and_comment_boundaries(self):
        cases = [
            ('python \\\n-B scripts/ok.py', 'python -B scripts/ok.py'),
            ('python scripts/o\\\nk.py', 'python scripts/ok.py'),
            ('python "scripts/o\\\nk.py"', 'python "scripts/ok.py"'),
            ("python 'scripts/o\\\nk.py'", "python 'scripts/o\\\nk.py'"),
            ('# comment \\\npython scripts/ok.py', '# comment \\\npython scripts/ok.py'),
            ('echo ># comment \\\npython scripts/ok.py', 'echo ># comment \\\npython scripts/ok.py'),
            ('echo <# comment \\\npython scripts/ok.py', 'echo <# comment \\\npython scripts/ok.py'),
            ('python scripts/ok.py # comment \\\npython scripts/next.py',
             'python scripts/ok.py # comment \\\npython scripts/next.py'),
            ('python scripts/ok.py \\\\\npython scripts/next.py',
             'python scripts/ok.py \\\\\npython scripts/next.py'),
        ]
        for command, expected in cases:
            with self.subTest(command=command):
                self.assertEqual(check.join_line_continuations(command), expected)

    def test_continued_commands_and_comments_keep_distinct_references(self):
        source = 'jobs:\n  test:\n    steps:\n      - run: |\n          python -B scripts/o\\\n          k.py\n          # comment \\\n          python scripts/next.py\n'
        refs, unsupported = check.references('test.yml', source)
        self.assertEqual({row[2] for row in refs}, {'scripts/ok.py', 'scripts/next.py'})
        self.assertFalse(unsupported)

    def test_continued_heredoc_operator_does_not_expose_body_commands(self):
        source = 'jobs:\n  test:\n    steps:\n      - run: |\n          cat <\\\n          <EOF\n          python scripts/not-executed.py\n          EOF\n'
        refs, unsupported = check.references('test.yml', source)
        self.assertFalse(refs)
        self.assertIn(('test.yml', 'test', 'heredoc body requires shell parsing'), unsupported)

    def test_numeric_job_ids_are_reported_as_sortable_strings(self):
        # YAML permits bare integer mapping keys, so a job id can be an int.
        # Every uninspected entry must carry a str job id so that main()'s
        # sorted(unsupported) does not raise TypeError on mixed int/str keys.
        source = ('jobs:\n  123:\n    steps:\n'
                  '      - run: |\n          cat <<EOF\n          hi\n          EOF\n'
                  '      - run: python $DYN.py\n')
        _, unsupported = check.references('w.yml', source)
        self.assertTrue(all(isinstance(row[1], str) for row in unsupported))
        sorted(unsupported)  # must not raise

    def test_continuations_compose_with_environment_prefixes(self):
        source = 'jobs:\n  test:\n    steps:\n      - run: |\n          env FLAG=1 \\\n            python -B scripts/env.py\n          FLAG=1 python \\\n            scripts/assignment.py\n'
        refs, unsupported = check.references('test.yml', source)
        self.assertEqual({row[2] for row in refs}, {'scripts/env.py', 'scripts/assignment.py'})
        self.assertFalse(unsupported)


if __name__ == '__main__':
    unittest.main()
