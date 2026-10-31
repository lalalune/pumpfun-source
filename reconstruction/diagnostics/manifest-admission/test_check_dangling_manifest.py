"""A dangling manifest link is a failed check, not a packet without a manifest.

The batch runner counts a packet as having a manifest from its directory entry,
so the checker's answer decides the packet: no_manifest makes it inconclusive
even though the declared manifest cannot be read, while the root revalidator
fails the same packet.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent


class DanglingManifestTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.packet = self.root / 'research/linked-manifest'
        self.packet.mkdir(parents=True)

    def test_dangling_manifest_fails_the_check(self):
        os.symlink('missing.json', self.packet / 'manifest.json')
        result = check.check_manifest(self.packet)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['files_checked'], 0)

    def test_absent_manifest_is_still_reported_as_absent(self):
        self.assertEqual(check.check_manifest(self.packet), {'status': 'no_manifest', 'errors': []})

    def test_batch_fails_the_packet(self):
        (self.root / 'scripts').mkdir()
        shutil.copyfile(ROOT / 'scripts/revalidate_all.py', self.root / 'scripts/revalidate_all.py')
        (self.packet / 'verify.py').write_bytes(b'print("fixture verification passed")\n')
        os.symlink('missing.json', self.packet / 'manifest.json')
        output = self.root / 'audit'
        result = subprocess.run([sys.executable, '-B', str(PACKAGE / 'run.py'), '--repo', str(self.root),
                                 '--output', str(output)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = json.loads((output / 'results.json').read_text(encoding='utf-8'))
        self.assertEqual([row['overall'] for row in rows], ['fail'])


if __name__ == '__main__':
    unittest.main()
