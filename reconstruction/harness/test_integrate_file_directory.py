"""Run the complete no-build integration CLI with real git/diff/patch."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent


class FileDirectoryIntegrationTests(unittest.TestCase):
    def test_file_directory_transitions_and_text_control(self):
        for change in ('file-to-directory', 'directory-to-file', 'text'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                harness = root / 'harness'
                harness.mkdir()
                for name in ('integrate.py', 'treediff.py', 'source_inputs.py'):
                    shutil.copy2(H / name, harness / name)
                base, part = root / 'base', root / 'part'
                for tree in (base, part):
                    (tree / 'src').mkdir(parents=True)
                    (tree / 'Cargo.toml').write_text('[package]\nname="fixture"\n')
                    (tree / 'Cargo.lock').write_text('version = 3\n')
                    (tree / 'src/lib.rs').write_text('pub fn same() {}\n')
                directory_side = part if change == 'file-to-directory' else base
                if change != 'text':
                    (directory_side / 'assets').mkdir()
                    (directory_side / 'assets/table.txt').write_text('directory data\n')
                    file_side = base if directory_side == part else part
                    (file_side / 'assets').write_text('file data\n')
                else:
                    (base / 'assets').write_text('before\n')
                    (part / 'assets').write_text('after\n')
                def inventory(tree):
                    return {p.relative_to(tree).as_posix(): p.read_bytes()
                            for p in tree.rglob('*') if p.is_file()}
                originals = inventory(base), inventory(part)
                run = subprocess.run(
                    [sys.executable, str(harness / 'integrate.py'), '--name', 'trial',
                     '--base-src', str(base), '--part', 'change=' + str(part), '--no-build'],
                    capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                report = json.loads((root / 'integ/trial/report.json').read_text())
                self.assertEqual(report['parts'][0]['status'], 'applied', run.stdout)
                self.assertEqual(inventory(root / 'integ/trial/src'), inventory(part))
                self.assertEqual(originals, (inventory(base), inventory(part)))


if __name__ == '__main__':
    unittest.main()
