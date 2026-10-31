"""Removing a directory's last file must not remove a directory the part still has."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

import integrate


def crate(path):
    (path / 'src/shared/deep').mkdir(parents=True)
    (path / 'Cargo.toml').write_text('[package]\nname="synthetic"\nversion="0.0.0"\n')
    (path / 'Cargo.lock').write_text('version = 3\n')
    (path / 'src/lib.rs').write_text('pub fn f() {}\n')
    (path / 'src/shared/deep/text.rs').write_text('one\n')
    (path / 'src/shared/deep/empty.rs').write_text('')


class IntegrateKeptDirectoriesTests(unittest.TestCase):
    def compose(self, root, names):
        base, part = root / 'base', root / 'part'
        crate(base)
        shutil.copytree(base, part)
        for name in names:
            (part / name).unlink()
        sc = root / 'reconstruction'
        argv = ['integrate.py', '--name', 'trial', '--base-src', str(base),
                '--part', f'lane={part}', '--no-build']
        with patch.object(integrate, 'SC', sc), patch.object(sys, 'argv', argv), \
                contextlib.redirect_stdout(io.StringIO()):
            status = integrate.main()
        out = sc / 'integ/trial'
        report = json.loads((out / 'report.json').read_text())
        self.assertEqual(status, 0, report)
        self.assertEqual({row['status'] for row in report['parts']}, {'applied'}, report)
        return out / 'src'

    def test_directories_survive_for_both_patch_formats(self):
        files = ['src/shared/deep/text.rs', 'src/shared/deep/empty.rs']
        for names in (files, files[:1], files[1:]):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as temporary:
                src = self.compose(Path(temporary), names)
                self.assertTrue((src / 'src/shared/deep').is_dir())
                for name in names:
                    self.assertFalse((src / name).exists())

    def test_a_directory_removed_by_an_earlier_part_stays_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = root / 'base'
            crate(base)
            first, second = root / 'first', root / 'second'
            shutil.copytree(base, first)
            shutil.copytree(base, second)
            shutil.rmtree(first / 'src/shared')
            (second / 'src/lib.rs').write_text('pub fn g() {}\n')
            sc = root / 'reconstruction'
            argv = ['integrate.py', '--name', 'trial', '--base-src', str(base),
                    '--part', f'first={first}', '--part', f'second={second}', '--no-build']
            with patch.object(integrate, 'SC', sc), patch.object(sys, 'argv', argv), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(integrate.main(), 0)
            self.assertFalse((sc / 'integ/trial/src/src/shared').exists())


if __name__ == '__main__':
    unittest.main()
