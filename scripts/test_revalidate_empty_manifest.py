"""A manifest that declares no files must not revalidate as a pass.

Sibling of merged #2494, which closed the same gap in
reconstruction/tooling/revalidation-qualification/audit.py: an empty flat
manifest ({}) or an empty files manifest ({"files": []}) verified nothing,
yet scripts/revalidate_all.py reported the packet overall "pass". This
checker is a separate admission path that #2494 could not reach.
"""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class RevalidateEmptyManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'scripts').mkdir()
        shutil.copyfile(REPO / 'scripts/revalidate_all.py',
                        self.root / 'scripts/revalidate_all.py')
        for name, declaration in (('empty-flat', {}),
                                  ('empty-files', {'files': []})):
            packet = self.root / 'research' / name
            packet.mkdir(parents=True)
            (packet / 'manifest.json').write_text(
                json.dumps(declaration), encoding='utf-8')
        control = self.root / 'research' / 'valid'
        control.mkdir(parents=True)
        payload = b'recorded notes\n'
        (control / 'notes.txt').write_bytes(payload)
        (control / 'manifest.json').write_text(json.dumps({
            'notes.txt': hashlib.sha256(payload).hexdigest(),
        }), encoding='utf-8')

    def run_audit(self, output):
        return subprocess.run(
            [sys.executable, '-B', str(self.root / 'scripts/revalidate_all.py'),
             '--output', str(output)],
            cwd=self.root, capture_output=True, encoding='utf-8',
        )

    def test_manifest_declaring_no_files_is_not_a_pass(self):
        output = self.root / 'audit'
        result = self.run_audit(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = {row['packet']: row for row in json.loads(
            (output / 'results.json').read_text(encoding='utf-8'))}
        for name in ('empty-flat', 'empty-files'):
            with self.subTest(name=name):
                self.assertEqual(rows[name]['manifest_check']['status'], 'fail')
                self.assertEqual(rows[name]['manifest_check']['files_checked'], 0)
                self.assertEqual(rows[name]['manifest_check']['files_expected'], 0)
                self.assertEqual(rows[name]['manifest_check']['errors'],
                                 ['manifest declares no files'])
                self.assertEqual(rows[name]['overall'], 'fail')
        self.assertEqual(rows['valid']['overall'], 'pass')
        summary = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
        self.assertEqual((summary['pass'], summary['fail'],
                          summary['skip_or_inconclusive']), (1, 2, 0))


if __name__ == '__main__':
    unittest.main()
