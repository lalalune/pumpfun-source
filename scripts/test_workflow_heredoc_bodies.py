import unittest
import check_workflow_inputs as check


def inspect(command):
    source = 'jobs:\n  audit:\n    steps:\n      - run: |\n' + ''.join('          ' + line + '\n' for line in command.splitlines())
    return check.references('test.yml', source)


class HeredocBodyTests(unittest.TestCase):
    def test_embedded_source_is_not_a_workflow_script_invocation(self):
        for command in ("cat <<'EOF' > generated.sh\npython scripts/not-invoked.py\nEOF",
                        "python - <<'PY'\npython scripts/not-python-code.py\nPY"):
            with self.subTest(command=command):
                refs, unsupported = inspect(command)
                self.assertFalse(refs)
                self.assertTrue(any('heredoc' in reason for _, _, reason in unsupported))

    def test_ordinary_literal_commands_remain_checked(self):
        refs, unsupported = inspect('python scripts/real.py\nbash scripts/real.sh')
        self.assertEqual({row[2] for row in refs}, {'scripts/real.py', 'scripts/real.sh'})
        self.assertFalse(unsupported)


if __name__ == '__main__': unittest.main()
