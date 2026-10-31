import unittest
import check_workflow_inputs as check


def refs(run):
    source = "jobs:\n  audit:\n    steps:\n      - run: |\n" + ''.join(f"          {line}\n" for line in run)
    return check.references('w.yml', source)


class MidwordHashTests(unittest.TestCase):
    def test_hash_inside_a_word_keeps_the_script_path(self):
        found, unsupported = refs(['python3 scripts/issue#12.py --tag=v#1'])
        self.assertEqual(found, {('w.yml', 'audit', 'scripts/issue#12.py')})
        self.assertEqual(unsupported, set())

    def test_word_start_hash_is_still_a_comment(self):
        found, _ = refs(['python3 scripts/a.py # scripts/b.py', 'python3 scripts/c.py #x', '# python3 scripts/d.py'])
        self.assertEqual({r[2] for r in found}, {'scripts/a.py', 'scripts/c.py'})

    def test_quoted_and_escaped_hash_are_literal(self):
        found, _ = refs(['python3 "scripts/q #1.py"', "python3 scripts/e\\#2.py"])
        self.assertEqual({r[2] for r in found}, {'scripts/q #1.py', 'scripts/e#2.py'})


if __name__ == '__main__':
    unittest.main()
