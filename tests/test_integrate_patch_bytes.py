"""Exercise composition patches with real diff/patch and exact source bytes."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
import integrate


class PatchedFilesTests(unittest.TestCase):
    @staticmethod
    def diff_text(new_name):
        old_name = new_name.replace('b/pump/', 'a/pump/', 1)
        return (f'diff -ruN {old_name} {new_name}\n'
                f'--- {old_name}\tstamp\n'
                f'+++ {new_name}\tstamp\n'
                '@@ -1 +1 @@\n-old\n+new\n')

    def test_quoted_utf8_paths(self):
        names = (
            r'"b/pump/src/caf\303\251.rs"',
            '"b/pump/src/café.rs"',
        )
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(integrate.patched_files(self.diff_text(name)),
                                 ['src/café.rs'])

    def test_c_quoted_path_characters(self):
        name = r'"b/pump/src/space \"quote\"\\backslash\tname.rs"'
        self.assertEqual(integrate.patched_files(self.diff_text(name)),
                         ['src/space "quote"\\backslash\tname.rs'])

    def test_unquoted_unicode_line_separator_in_path(self):
        filename = 'src/one\u2028two.rs'
        self.assertEqual(integrate.patched_files(self.diff_text(f'b/pump/{filename}')),
                         [filename])

    def test_quoted_added_content_is_not_a_path(self):
        text = (self.diff_text('b/pump/src/lib.rs')
                + '@@ -10 +10,4 @@\n'
                  ' context\n'
                  '+++ "ordinary" + "text"\n'
                  '+++ "b/pump/ordinary" + "text"\n'
                  '+++ b/pump/not-a-file.rs\tstamp\n')
        self.assertEqual(integrate.patched_files(text), ['src/lib.rs'])

    def test_reads_headers_after_previous_file_hunks(self):
        text = (self.diff_text('b/pump/src/z.rs')
                + self.diff_text(r'"b/pump/src/caf\303\251.rs"'))
        self.assertEqual(integrate.patched_files(text), ['src/café.rs', 'src/z.rs'])


@unittest.skipUnless(shutil.which('diff') and shutil.which('patch'), 'requires diff and patch')
class IntegrationPatchBytesTests(unittest.TestCase):
    def assert_round_trip(self, before, after):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base, part, target = (root / name for name in ('base', 'part', 'target'))
            base.mkdir()
            part.mkdir()
            (base / 'lib.rs').write_bytes(before)
            (part / 'lib.rs').write_bytes(after)
            shutil.copytree(base, target)
            output, staging = root / 'change.patch', root / 'staging'
            report_text = integrate.make_patch(base, part, output, staging)
            # Compare with the actual diff process over the same staged paths;
            # timestamps and header formatting are supplied by the installed tool.
            raw = subprocess.run(['diff', '-ruN', 'a/pump', 'b/pump'], cwd=staging,
                                 capture_output=True)
            self.assertEqual(raw.returncode, 1)
            self.assertEqual(output.read_bytes(), raw.stdout)
            self.assertIsInstance(report_text, str)
            self.assertIn('+++ b/pump/lib.rs\t', report_text)
            command = ['patch', '-p2', '--forward', '-E', '-d', str(target), '-i', str(output)]
            dry = subprocess.run(command + ['--dry-run'], capture_output=True)
            self.assertEqual(dry.returncode, 0, (dry.stdout, dry.stderr))
            applied = subprocess.run(command, capture_output=True)
            self.assertEqual(applied.returncode, 0, (applied.stdout, applied.stderr))
            self.assertEqual((target / 'lib.rs').read_bytes(), after)
            self.assertEqual((base / 'lib.rs').read_bytes(), before)
            self.assertEqual((part / 'lib.rs').read_bytes(), after)

    def test_lf(self):
        self.assert_round_trip(b'// context\npub fn value() -> u8 { 1 }\n',
                               b'// context\npub fn value() -> u8 { 2 }\n')

    def test_crlf(self):
        self.assert_round_trip(b'// context\r\npub fn value() -> u8 { 1 }\r\n',
                               b'// context\r\npub fn value() -> u8 { 2 }\r\n')

    def test_mixed_line_endings(self):
        self.assert_round_trip(b'// context\r\npub fn value() -> u8 { 1 }\n// tail\r\n',
                               b'// context\r\npub fn value() -> u8 { 2 }\n// tail\r\n')

    def test_line_ending_change(self):
        self.assert_round_trip(b'// context\npub fn value() -> u8 { 1 }\n',
                               b'// context\r\npub fn value() -> u8 { 1 }\r\n')

    def test_unicode_and_line_separator(self):
        before = '// évidence\nconst TEXT: &str = "one\u2028two";\npub fn value() -> u8 { 1 }\n'
        self.assert_round_trip(before.encode(), before.replace('{ 1 }', '{ 2 }').encode())

    def test_missing_final_newline(self):
        self.assert_round_trip(b'// context\r\npub fn value() -> u8 { 1 }',
                               b'// context\r\npub fn value() -> u8 { 2 }')

    def test_no_build_composition_preserves_bytes_and_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base, part = root / 'base', root / 'part'
            for source in (base, part):
                (source / 'src').mkdir(parents=True)
                (source / 'Cargo.toml').write_bytes(b'[package]\nname = "fixture"\n')
                (source / 'Cargo.lock').write_bytes(b'version = 3\n')
            filename = 'src/café.rs'
            before = b'// context\r\npub fn value() -> u8 { 1 }\r\n'
            after = before.replace(b'{ 1 }', b'{ 2 }')
            (base / filename).write_bytes(before)
            (part / filename).write_bytes(after)
            argv = ['integrate.py', '--name', 'byte-test', '--base-src', str(base),
                    '--part', f'change={part}', '--no-build']
            with patch.object(integrate, 'SC', root / 'reconstruction'), \
                    patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                integrate.main()
            output = root / 'reconstruction/integ/byte-test'
            self.assertEqual((output / 'src' / filename).read_bytes(), after)
            report = json.loads((output / 'report.json').read_text())
            self.assertEqual(report['parts'], [{'label': 'change', 'status': 'applied',
                                                'files': [filename]}])
            self.assertNotIn('build', report)

    def test_identical_snapshots_have_empty_patch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base, part = root / 'base', root / 'part'
            for source in (base, part):
                source.mkdir()
                (source / 'lib.rs').write_bytes(b'// unchanged\r\n')
            output = root / 'change.patch'
            self.assertEqual(integrate.make_patch(base, part, output, root / 'staging'), '')
            self.assertEqual(output.read_bytes(), b'')


if __name__ == '__main__':
    unittest.main()
