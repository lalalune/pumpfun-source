"""Composition inputs must not acquire bytes through filesystem links."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate


class IntegrationSourceLinkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.scope = patch.object(integrate, 'SC', self.root / 'reconstruction')
        self.scope.start()
        self.addCleanup(self.scope.stop)
        self.outside = self.root / 'outside'
        self.outside.mkdir()
        (self.outside / 'sentinel.rs').write_bytes(
            b'pub const EXTERNAL_SENTINEL: &str = "outside";\n')

    def crate(self, name):
        source = self.root / name
        (source / 'src/nested').mkdir(parents=True)
        (source / 'Cargo.toml').write_bytes(
            b'[package]\nname = "fixture"\nversion = "0.0.0"\n')
        (source / 'Cargo.lock').write_bytes(b'version = 3\n')
        (source / 'src/lib.rs').write_bytes(b'pub fn fixture() {}\n')
        return source

    def file_link(self, target, link):
        try:
            link.symlink_to(target)
        except OSError as error:
            if sys.platform == 'win32' and error.winerror == 1314:
                self.skipTest('Windows file-symlink privilege unavailable')
            raise

    def directory_link(self, target, link):
        if sys.platform == 'win32':
            import _winapi
            _winapi.CreateJunction(str(target), str(link))
            self.addCleanup(link.rmdir)
        else:
            link.symlink_to(target, target_is_directory=True)

    def assert_preflight_rejects(self, base, parts=(), bases=()):
        with self.assertRaisesRegex(ValueError, 'source tree link'):
            integrate.preflight('trial', base, list(parts), list(bases))
        self.assertFalse((integrate.SC / 'integ').exists())

    def test_nested_file_links_are_rejected_in_every_input_role(self):
        for role in ('base-src', 'part', 'base-of'):
            with self.subTest(role=role):
                base = self.crate('base-' + role)
                part = self.crate('part-' + role)
                derived = self.crate('derived-' + role)
                selected = {'base-src': base, 'part': part, 'base-of': derived}[role]
                self.file_link(
                    self.outside / 'sentinel.rs',
                    selected / 'src/nested/external.rs')
                parts = [f'change={part}'] if role != 'base-src' else []
                bases = [f'change={derived}'] if role == 'base-of' else []
                self.assert_preflight_rejects(base, parts, bases)

    def test_symlinked_required_file_is_rejected(self):
        base = self.crate('base-required')
        outside_lock = self.outside / 'Cargo.lock'
        outside_lock.write_bytes(b'version = 3\n# external\n')
        (base / 'Cargo.lock').unlink()
        self.file_link(outside_lock, base / 'Cargo.lock')
        self.assert_preflight_rejects(base)

    def test_nested_directory_link_or_windows_junction_is_rejected(self):
        base = self.crate('base-directory')
        part = self.crate('part-directory')
        external_directory = self.outside / 'directory'
        external_directory.mkdir()
        (external_directory / 'external.rs').write_bytes(b'pub const OUTSIDE: u8 = 7;\n')
        self.directory_link(external_directory, part / 'src/linked')
        self.assert_preflight_rejects(base, [f'change={part}'])

    def test_source_root_link_or_windows_junction_is_rejected(self):
        target = self.crate('root-target')
        linked_root = self.root / 'root-link'
        self.directory_link(target, linked_root)
        self.assert_preflight_rejects(linked_root)

    def test_main_rejects_before_creating_output(self):
        base = self.crate('base-main')
        self.file_link(self.outside / 'sentinel.rs', base / 'src/nested/external.rs')
        argv = [
            'integrate.py', '--name', 'fresh-output', '--base-src', str(base),
            '--no-build',
        ]
        with patch.object(sys, 'argv', argv), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                integrate.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse((integrate.SC / 'integ').exists())

    def test_regular_nested_unicode_and_crlf_bytes_are_preserved(self):
        base = self.crate('ordinary')
        expected = b'pub const TEXT: &str = "ordinary";\r\n'
        (base / 'src/nested/na\u00efve.rs').write_bytes(expected)
        argv = [
            'integrate.py', '--name', 'ordinary', '--base-src', str(base),
            '--no-build',
        ]
        with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
            integrate.main()
        self.assertEqual(
            (integrate.SC / 'integ/ordinary/src/src/nested/na\u00efve.rs').read_bytes(),
            expected,
        )


if __name__ == '__main__':
    unittest.main()
