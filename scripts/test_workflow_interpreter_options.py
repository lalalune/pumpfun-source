import unittest
import check_workflow_inputs as check


def references(command):
    return check.references('test.yml', 'jobs:\n  audit:\n    steps:\n      - run: ' + command + '\n')[0]


class InterpreterOptionsTests(unittest.TestCase):
    def test_environment_prefixes_do_not_hide_script(self):
        for command in ('FOO=bar python scripts/check.py',
                        'env FOO=bar python scripts/check.py',
                        'env -i FOO=bar bash scripts/check.sh'):
            with self.subTest(command=command):
                self.assertEqual({r[2] for r in references(command)},
                                 {'scripts/check.py' if command.endswith('.py') else 'scripts/check.sh'})

    def test_shell_option_arguments_do_not_hide_script(self):
        for command in ('bash -o pipefail scripts/check.sh',
                        'bash -euo pipefail scripts/check.sh',
                        'bash -O extglob scripts/check.sh',
                        'bash --rcfile config scripts/check.sh',
                        'sh -o errexit scripts/check.sh'):
            with self.subTest(command=command):
                self.assertEqual({r[2] for r in references(command)}, {'scripts/check.sh'})

    def test_inline_shell_commands_and_python_options(self):
        self.assertFalse(references('bash -ec "python scripts/not-an-entrypoint.py"'))
        self.assertEqual({r[2] for r in references('python --check-hash-based-pycs always scripts/check.py')},
                         {'scripts/check.py'})
        self.assertEqual({r[2] for r in references('python -X utf8 -W error -- scripts/check.py')},
                         {'scripts/check.py'})
        self.assertFalse(references('python -m unittest'))


if __name__ == '__main__': unittest.main()
