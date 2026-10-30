"""Real trial execution: source directory membership affects a predicate."""
from pathlib import Path
import sys
import tempfile
import unittest

from experiment_runner import run_trial


class DirectoryIdentityTests(unittest.TestCase):
    def test_add_remove_and_rename_directory_invalidate_reuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            (source / 'value').write_text('unchanged')
            command = [sys.executable, '-c',
                       'from pathlib import Path; import sys; '
                       'sys.exit(0 if Path(sys.argv[1], "generated").is_dir() else 1)', '{source}']
            first = run_trial(source, command, root / 'trial')
            self.assertEqual(first['status'], 'fail')
            (source / 'generated').mkdir()
            second = run_trial(source, command, root / 'trial')
            self.assertFalse(second['reused'])
            self.assertEqual(second['status'], 'pass')
            self.assertTrue(run_trial(source, command, root / 'trial')['reused'])
            (source / 'generated').rename(source / 'other')
            third = run_trial(source, command, root / 'trial')
            self.assertFalse(third['reused'])
            self.assertEqual(third['status'], 'fail')
            (source / 'other').rmdir()
            self.assertFalse(run_trial(source, command, root / 'trial')['reused'])

    def test_trial_directory_mutation_is_an_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            command = [sys.executable, '-c',
                       'from pathlib import Path; import sys; '
                       'Path(sys.argv[1], "generated").mkdir()', '{source}']
            result = run_trial(source, command, root / 'trial')
            self.assertEqual(result['status'], 'error')

    def test_ignored_root_target_directory_does_not_change_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            command = [sys.executable, '-c', 'pass']
            run_trial(source, command, root / 'trial')
            (source / 'target').mkdir()
            self.assertTrue(run_trial(source, command, root / 'trial')['reused'])


    def test_nested_directory_survives_ignored_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            cache = source / 'nested' / '__pycache__'
            cache.mkdir(parents=True)
            noise = cache / 'ignored'
            noise.write_text('first')
            command = [sys.executable, '-c',
                       'from pathlib import Path; import sys; '
                       'p=Path(sys.argv[1], "nested"); '
                       'sys.exit(0 if p.is_dir() and not list(p.iterdir()) else 1)', '{source}']
            first = run_trial(source, command, root / 'trial')
            self.assertEqual(first['status'], 'pass')
            noise.write_text('changed ignored bytes')
            self.assertTrue(run_trial(source, command, root / 'trial')['reused'])
            noise.unlink()
            cache.rmdir()
            self.assertTrue(run_trial(source, command, root / 'trial')['reused'])
            (source / 'nested').rmdir()
            final = run_trial(source, command, root / 'trial')
            self.assertFalse(final['reused'])
            self.assertEqual(final['status'], 'fail')


if __name__ == '__main__':
    unittest.main()
