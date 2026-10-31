"""A retained output tree that cannot be enumerated is not authenticated."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

from experiment_runner import run_trial


@unittest.skipUnless(os.name == 'posix' and os.geteuid() != 0,
                     'requires POSIX directory permissions and an unprivileged user')
class OutputWalkErrorTests(unittest.TestCase):
    def test_unreadable_generated_output_is_an_error_with_retained_logs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            command = [sys.executable, '-c',
                       'from pathlib import Path; import sys; '
                       'p=Path(sys.argv[1])/"closed"; p.mkdir(); '
                       '(p/"result").write_text("not authenticated"); '
                       'p.chmod(0); print("child completed")', '{out}']
            result = run_trial(source, command, root / 'trial')
            attempt = root / 'trial' / result['attempt']
            closed = attempt / 'output/closed'
            try:
                self.assertEqual(result['status'], 'error')
                self.assertIn('post-run validation failed', result['reason'])
                self.assertIn('child completed', (attempt / 'stdout.log').read_text())
                self.assertTrue((root / 'trial/latest.json').is_file())
            finally:
                closed.chmod(0o700)

    def test_unreadable_retained_directory_cannot_be_silently_skipped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            command = [sys.executable, '-c',
                       'from pathlib import Path; import sys; '
                       '(Path(sys.argv[1])/"empty").mkdir()', '{out}']
            first = run_trial(source, command, root / 'trial')
            self.assertEqual(first['status'], 'pass')
            self.assertTrue(run_trial(source, command, root / 'trial')['reused'])
            closed = root / 'trial' / first['attempt'] / 'output/empty'
            closed.chmod(0)
            try:
                second = run_trial(source, command, root / 'trial')
                self.assertFalse(second['reused'])
                self.assertEqual(second['status'], 'pass')
                self.assertNotEqual(first['attempt'], second['attempt'])
            finally:
                closed.chmod(0o700)


if __name__ == '__main__':
    unittest.main()
