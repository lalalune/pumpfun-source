"""Apply generated source patches and require exact candidate bytes."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from treediff import tree_diff


class SourcePatchLineBoundaries(unittest.TestCase):
    def assert_round_trip(self, before, after):
        with tempfile.TemporaryDirectory(prefix='pump-treediff-lines-') as temp:
            root = Path(temp)
            working = root / 'working'
            base = working / 'programs/pump'
            candidate = root / 'candidate'
            base.mkdir(parents=True)
            candidate.mkdir()
            # A crate-root file isolates line handling from nested-path portability.
            (base / 'lib.rs').write_bytes(before)
            (candidate / 'lib.rs').write_bytes(after)
            patch = tree_diff(base, candidate).encode('utf-8')
            for arguments in (['--check'], []):
                result = subprocess.run(
                    ['git', '-c', 'core.autocrlf=false', 'apply', *arguments, '-'], cwd=working,
                    input=patch, capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            self.assertEqual((base / 'lib.rs').read_bytes(), after)

    def test_unicode_separators_in_unchanged_context(self):
        for separator in ('\u0085', '\u2028', '\u2029'):
            with self.subTest(separator=ascii(separator)):
                context = f'pub const LABEL: &str = "A{separator}B";\n'.encode('utf-8')
                self.assert_round_trip(
                    context + b'pub const N: u8 = 1;\n',
                    context + b'pub const N: u8 = 2;\n',
                )

    def test_unicode_separators_in_changed_lines(self):
        for separator in ('\u0085', '\u2028', '\u2029'):
            with self.subTest(separator=ascii(separator)):
                self.assert_round_trip(
                    f'pub const LABEL: &str = "A{separator}B";\n'.encode('utf-8'),
                    f'pub const LABEL: &str = "C{separator}D";\n'.encode('utf-8'),
                )

    def test_lf_crlf_and_missing_final_lf(self):
        for ending in (b'\n', b'\r\n', b''):
            with self.subTest(ending=ending):
                self.assert_round_trip(b'const N: u8 = 1;' + ending,
                                       b'const N: u8 = 2;' + ending)

    def test_undecodable_files_report_as_binary_without_losing_the_diff(self):
        with tempfile.TemporaryDirectory(prefix='pump-treediff-binary-') as temp:
            root = Path(temp)
            base = root / 'base'
            candidate = root / 'candidate'
            base.mkdir()
            candidate.mkdir()
            (base / 'lib.rs').write_bytes(b'pub const N: u8 = 1;\n')
            (candidate / 'lib.rs').write_bytes(b'pub const N: u8 = 2;\n')
            (base / 'fixture.bin').write_bytes(b'abc\x00\xfe\xff')
            (candidate / 'fixture.bin').write_bytes(b'abc\x00\xfd\xfe')
            (base / 'latin.cfg').write_bytes(b'caf\xe9\n')
            (candidate / 'latin.cfg').write_bytes(b'caf\xe8\n')
            (base / 'became-binary.bin').write_bytes(b'plain text\n')
            (candidate / 'became-binary.bin').write_bytes(b'\xff\xfe')
            (base / 'unchanged.bin').write_bytes(b'\x00\x01same')
            (candidate / 'unchanged.bin').write_bytes(b'\x00\x01same')
            patch = tree_diff(base, candidate)
            self.assertIn('Binary files "a/programs/pump/fixture.bin" and "b/programs/pump/fixture.bin" differ', patch)
            self.assertIn('Binary files "a/programs/pump/latin.cfg" and "b/programs/pump/latin.cfg" differ', patch)
            self.assertIn('Binary files \"a/programs/pump/became-binary.bin\" and \"b/programs/pump/became-binary.bin\" differ', patch)
            self.assertNotIn('unchanged.bin', patch)
            self.assertIn('-pub const N: u8 = 1;', patch)
            self.assertIn('+pub const N: u8 = 2;', patch)


if __name__ == '__main__':
    unittest.main()
