"""Shell stdin operands are not workflow script dependencies."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import check_workflow_inputs as check


def workflow(command):
    return 'jobs:\n  audit:\n    steps:\n      - run: ' + command + '\n'


class ShellStdinTests(unittest.TestCase):
    def test_stdin_mode_ignores_positional_parameters(self):
        for shell in ('bash', 'sh', '/bin/bash', '/bin/sh'):
            for flags in ('-s', '-es', '-se', '-s -c ":"', '-s -o errexit'):
                command = f'{shell} {flags} -- scripts/not-a-file.sh < /dev/null'
                with self.subTest(command=command):
                    self.assertEqual(check.references('test.yml', workflow(command)), (set(), set()))

    def test_option_arguments_are_not_stdin_or_command_flags(self):
        for options in ('-o posix', '-o noclobber', '-O extglob',
                        '--rcfile config', '--init-file config'):
            with self.subTest(options=options):
                found, skipped = check.references('test.yml', workflow(f'bash {options} scripts/real.sh'))
                self.assertEqual({row[2] for row in found}, {'scripts/real.sh'})
                self.assertEqual(skipped, set())

    def test_cli_does_not_report_stdin_positional_parameter_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            path = root / '.github/workflows/test.yml'
            path.parent.mkdir(parents=True)
            path.write_text(workflow('bash -es -- scripts/not-a-file.sh < /dev/null'), encoding='utf-8')
            result = subprocess.run([sys.executable, str(Path(check.__file__)), '--repo', str(root), '--all'],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['checked_references'], 0)
            self.assertEqual(report['new_missing'], [])

    @unittest.skipUnless(shutil.which('bash') and shutil.which('sh') and sys.platform != 'win32',
                         'requires native POSIX shells')
    def test_native_shells_use_stdin_without_opening_positional_parameter(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for shell in ('bash', 'sh'):
                for flag in ('-s', '-es', '-se'):
                    with self.subTest(shell=shell, flag=flag):
                        result = subprocess.run([shell, flag, '--', 'scripts/not-a-file.sh'],
                                                input=':', text=True, capture_output=True, cwd=root)
                        self.assertEqual(result.returncode, 0, result.stderr)
            script = root / 'scripts/real.sh'
            script.parent.mkdir()
            script.write_text(':\n', encoding='utf-8')
            for flags in (('-o', 'posix'), ('-o', 'noclobber'), ('-O', 'extglob')):
                result = subprocess.run(['bash', *flags, 'scripts/real.sh'],
                                        text=True, capture_output=True, cwd=root)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
