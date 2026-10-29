from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
import match_oracle as oracle


class MatchOracleTests(unittest.TestCase):
    def test_build_errors_are_not_matching_failures(self):
        for built, expected in [({'ok': False}, 2), ({'ok': True, 'stack_warnings': ['overflow']}, 2), ({'ok': True}, 0)]:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory); out = root / 'out'; out.mkdir()
                for name in ['original.so', 'functions.tsv']: (root / name).write_bytes(b'fixture')
                with patch.object(oracle.score, 'BASE', root), patch.object(oracle.score, 'original_windows', return_value=[{'start': 8}]), patch.object(oracle.fastbuild, 'build', return_value=built), patch.object(oracle.score, 'score', return_value={8: {'normalized': True}}) as scoring:
                    self.assertEqual(oracle.evaluate(root, root / 'work', out, 8, 'normalized', 'identity'), expected)
                    self.assertEqual(scoring.call_count, int(expected == 0))
                    self.assertEqual(oracle.score.BASE, root)

    def test_cli_input_exception_is_error_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(Path(oracle.__file__)), '--source', directory,
                '--work', directory + '/work', '--out', directory + '/out', '--sdk', directory,
                '--recipe', 'mac', '--window', '0x123456789'], capture_output=True)
            self.assertEqual(result.returncode, 2)

    def test_valid_nonmatch_is_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'out'; out.mkdir()
            for name in ['original.so', 'functions.tsv']: (root / name).write_bytes(b'fixture')
            with patch.object(oracle.score, 'BASE', root), patch.object(oracle.score, 'original_windows', return_value=[{'start': 8}]), patch.object(oracle.fastbuild, 'build', return_value={'ok': True}), patch.object(oracle.score, 'score', return_value={8: {'raw': False}}):
                self.assertEqual(oracle.evaluate(root, root / 'work', out, 8, 'raw', 'identity'), 1)


if __name__ == '__main__': unittest.main()
