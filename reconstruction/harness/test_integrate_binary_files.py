"""Composition must carry binary changes instead of reporting them as applied."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


TOOL = Path(__file__).with_name('integrate.py')
OLD, NEW = b'\x00\x01old\xff', b'\x00\x02new\xff'
TEXT = b'pub fn value() -> u64 { 2 }\n'


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


@unittest.skipUnless(shutil.which('git') and shutil.which('diff') and shutil.which('patch'),
                     'requires the real composition tools')
class BinaryCompositionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='compose-binary-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tool = self.root / 'reconstruction/harness/integrate.py'
        self.tool.parent.mkdir(parents=True)
        shutil.copyfile(TOOL, self.tool)
        # integrate.py imports its sibling treediff module.
        shutil.copyfile(TOOL.with_name('treediff.py'), self.tool.with_name('treediff.py'))
        shutil.copyfile(TOOL.with_name('source_inputs.py'), self.tool.with_name('source_inputs.py'))

    def crate(self, name, files):
        root = self.root / name
        contents = {'Cargo.toml': b'[package]\nname="fixture"\nversion="0.1.0"\n',
                    'Cargo.lock': b'version = 3\n',
                    'src/lib.rs': b'pub fn value() -> u64 { 1 }\n', **files}
        for filename, data in contents.items():
            path = root / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return root

    def assert_composed(self, base_files, part_files, changed):
        base, part = self.crate('base', base_files), self.crate('part', part_files)
        result = subprocess.run(
            [sys.executable, '-B', str(self.tool), '--name', 'test', '--base-src', str(base),
             '--part', f'part={part}', '--no-build'],
            cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.root / 'reconstruction/integ/test'
        report = json.loads((output / 'report.json').read_bytes())
        self.assertEqual(report['parts'][0]['status'], 'applied')
        self.assertEqual(report['parts'][0]['files'], changed)
        self.assertEqual(snapshot(output / 'src'), snapshot(part))

    def test_changed_binary_beside_a_text_change(self):
        self.assert_composed({'data.bin': OLD}, {'data.bin': NEW, 'src/lib.rs': TEXT},
                             ['data.bin', 'src/lib.rs'])

    def test_added_binary_beside_a_text_change(self):
        self.assert_composed({}, {'data.bin': NEW, 'src/lib.rs': TEXT},
                             ['data.bin', 'src/lib.rs'])

    def test_binary_change_alone(self):
        self.assert_composed({'data.bin': OLD}, {'data.bin': NEW}, ['data.bin'])

    def test_removed_binary_beside_a_text_change(self):
        self.assert_composed({'data.bin': OLD}, {'src/lib.rs': TEXT}, ['data.bin', 'src/lib.rs'])

    @unittest.skipIf(sys.platform == 'win32', 'executable shell fixture requires POSIX')
    def test_binary_detection_does_not_inherit_a_translated_locale(self):
        shim = self.root/'bin'; shim.mkdir()
        wrapper = shim/'diff'
        real_diff = shutil.which('diff')
        wrapper.write_text('#!/bin/sh\nif [ "$LC_ALL" = C ]; then exec "'+real_diff+'" "$@"; fi\n'
                           "printf 'Fichiers binaires differents\\n'\nexit 1\n")
        wrapper.chmod(0o755)
        with mock.patch.dict(os.environ, PATH=str(shim)+os.pathsep+os.environ['PATH'], LC_ALL='translated-fixture'):
            self.assert_composed({'data.bin': OLD}, {'data.bin': NEW, 'src/lib.rs': TEXT},
                                 ['data.bin', 'src/lib.rs'])


if __name__ == '__main__':
    unittest.main()
