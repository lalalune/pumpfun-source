"""A manifest that repeats a key must not revalidate against only its last entry.

json.loads() keeps the last of several entries for one key, so a manifest that
lists a file with conflicting digests was checked against whichever entry
happened to come last and reviewed as a pass. The tracked packet
research/tooling-legacy-capture-metadata-20261029 declared inputs.json three
times with three different digests, two of them matching nothing on disk.

scripts/revalidate_all.py is the admission path that reads these manifests, so
it now rejects repeated keys before any digest is compared: a repeated flat key
or a repeated field inside a files record is a manifest_parse_error naming the
key, and the packet's overall status is fail.
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


class RevalidateDuplicateManifestKeyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'scripts').mkdir()
        shutil.copyfile(REPO / 'scripts/revalidate_all.py',
                        self.root / 'scripts/revalidate_all.py')
        payload = b'recorded notes\n'
        accurate = hashlib.sha256(payload).hexdigest()
        stale = hashlib.sha256(b'an earlier draft\n').hexdigest()

        for name, declaration in (
            # The stale digest comes first so json.loads() keeps the accurate
            # one and the packet passed, though its manifest also declares a
            # digest that matches nothing.
            ('duplicate-flat',
             '{\n  "notes.txt": "%s",\n  "notes.txt": "%s"\n}\n'
             % (stale, accurate)),
            ('duplicate-record',
             '{"files": [{"path": "notes.txt", "sha256": "%s", '
             '"sha256": "%s"}]}\n' % (stale, accurate)),
        ):
            packet = self.root / 'research' / name
            packet.mkdir(parents=True)
            (packet / 'notes.txt').write_bytes(payload)
            (packet / 'manifest.json').write_text(declaration, encoding='utf-8')

        control = self.root / 'research' / 'valid'
        control.mkdir(parents=True)
        (control / 'notes.txt').write_bytes(payload)
        (control / 'manifest.json').write_text(json.dumps({
            'notes.txt': accurate,
        }), encoding='utf-8')

    def test_repeated_manifest_key_fails_instead_of_using_the_last_entry(self):
        output = self.root / 'audit'
        result = subprocess.run(
            [sys.executable, '-B', str(self.root / 'scripts/revalidate_all.py'),
             '--output', str(output)],
            cwd=self.root, capture_output=True, encoding='utf-8',
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = {row['packet']: row for row in json.loads(
            (output / 'results.json').read_text(encoding='utf-8'))}
        for name, key in (('duplicate-flat', 'notes.txt'),
                          ('duplicate-record', 'sha256')):
            with self.subTest(name=name):
                check = rows[name]['manifest_check']
                self.assertEqual(check['status'], 'manifest_parse_error')
                self.assertEqual(check['errors'],
                                 ['duplicate manifest key: ' + key])
                self.assertEqual(rows[name]['overall'], 'fail')
        self.assertEqual(rows['valid']['overall'], 'pass')
        summary = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
        self.assertEqual((summary['pass'], summary['fail'],
                          summary['skip_or_inconclusive']), (1, 2, 0))


if __name__ == '__main__':
    unittest.main()
