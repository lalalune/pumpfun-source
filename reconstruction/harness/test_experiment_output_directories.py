"""Retained output directory membership is part of a reusable trial result."""
from pathlib import Path
import sys
import tempfile
import unittest

from experiment_runner import run_trial


class OutputDirectoryIdentityTests(unittest.TestCase):
    def test_empty_directory_changes_invalidate_pass_and_fail_results(self):
        for code in (0, 1):
            for change in ('remove', 'rename', 'add'):
                with self.subTest(code=code, change=change), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    source = root / 'source'
                    source.mkdir()
                    command = [sys.executable, '-c',
                               'from pathlib import Path; import sys; '
                               'p=Path(sys.argv[1]); '
                               '(p/"cache"/"empty").mkdir(parents=True); '
                               '(p/"result").write_text("unchanged"); '
                               'sys.exit(int(sys.argv[2]))', '{out}', str(code)]
                    destination = root / 'trial'
                    first = run_trial(source, command, destination)
                    self.assertEqual(first['status'], 'pass' if code == 0 else 'fail')
                    self.assertTrue(run_trial(source, command, destination)['reused'])
                    output = destination / first['attempt'] / 'output'
                    empty = output / 'cache' / 'empty'
                    if change == 'remove':
                        empty.rmdir()
                    elif change == 'rename':
                        empty.rename(empty.with_name('renamed'))
                    else:
                        (output / 'extra').mkdir()
                    second = run_trial(source, command, destination)
                    self.assertFalse(second['reused'])
                    self.assertNotEqual(first['attempt'], second['attempt'])
                    self.assertTrue((destination / second['attempt'] / 'output/cache/empty').is_dir())
                    self.assertEqual((output / 'result').read_text(), 'unchanged')
                    self.assertTrue(run_trial(source, command, destination)['reused'])


if __name__ == '__main__':
    unittest.main()
