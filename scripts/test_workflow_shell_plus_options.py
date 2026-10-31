import unittest
import check_workflow_inputs as check


def refs(command):
    return check.references('w.yml', 'jobs:\n  j:\n    steps:\n      - run: ' + command + '\n')


class ShellPlusOptionTests(unittest.TestCase):
    def test_plus_options_precede_the_script(self):
        for command in ('bash +e scripts/x.sh', 'bash +o pipefail scripts/x.sh',
                        'sh +x scripts/x.sh', 'bash -e +O extglob scripts/x.sh'):
            with self.subTest(command):
                self.assertEqual(refs(command), ({('w.yml', 'j', 'scripts/x.sh')}, set()))

    def test_python_plus_token_is_still_a_script_name(self):
        found, unsupported = refs('python3 +x.py')
        self.assertEqual(found, set())
        self.assertEqual(unsupported, {('w.yml', 'j', 'outside checked roots: +x.py')})


if __name__ == '__main__':
    unittest.main()
