"""An inherited POSIXLY_CORRECT must not turn a part's new file into a conflict."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).with_name('integrate.py')


@unittest.skipUnless(shutil.which('git') and shutil.which('diff') and shutil.which('patch'),
                     'requires the real composition tools')
class PosixPatchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='compose-posix-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tool = self.root / 'reconstruction/harness/integrate.py'
        self.tool.parent.mkdir(parents=True)
        for name in ('integrate.py', 'treediff.py', 'source_inputs.py'):
            shutil.copyfile(TOOL.with_name(name), self.tool.with_name(name))

    def crate(self, name, *extra):
        root = self.root / name
        for filename in ('Cargo.toml', 'Cargo.lock', 'src/lib.rs', *extra):
            path = root / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'// ' + filename.encode() + b'\n')
        return root

    def test_new_file_is_applied_under_posixly_correct(self):
        base = self.crate('base')
        part = self.crate('part', 'src/added.rs')
        result = subprocess.run(
            [sys.executable, '-B', str(self.tool), '--name', 'test', '--base-src', str(base),
             '--part', f'part={part}', '--no-build'],
            cwd=self.root, capture_output=True, text=True, timeout=30,
            env=dict(os.environ, POSIXLY_CORRECT='1'))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.root / 'reconstruction/integ/test'
        status = json.loads((output / 'report.json').read_bytes())['parts'][0]['status']
        self.assertEqual(status, 'applied')
        self.assertEqual((output / 'src/src/added.rs').read_bytes(), b'// src/added.rs\n')


if __name__ == '__main__':
    unittest.main()
