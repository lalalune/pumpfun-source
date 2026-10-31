"""A manifest that declares one path twice must not pass admission.

json.loads keeps the last occurrence of a key, so the earlier declaration was
never compared with the payload. The qualification audit (audit.py) rejects a
repeated JSON field before it delegates, and the root revalidator rejects a
repeated path in its record lists; this checker, which run.py substitutes for
the root one, did neither.
"""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402


PAYLOAD = b'payload bytes\n'
ACTUAL = hashlib.sha256(PAYLOAD).hexdigest()
STALE = hashlib.sha256(b'other bytes\n').hexdigest()


def write_packet(packet, manifest_text):
    packet.mkdir(parents=True)
    (packet / 'data.txt').write_bytes(PAYLOAD)
    (packet / 'manifest.json').write_text(manifest_text, encoding='utf-8')


class ManifestAdmissionDuplicatePathTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_unique_paths_still_pass(self):
        packet = self.root / 'packet'
        write_packet(packet, json.dumps({'data.txt': ACTUAL}))
        self.assertEqual(check.check_manifest(packet)['status'], 'pass')

    def test_repeated_path_with_a_stale_first_digest_fails(self):
        packet = self.root / 'packet'
        write_packet(packet, f'{{"data.txt": "{STALE}", "data.txt": "{ACTUAL}"}}')
        result = check.check_manifest(packet)
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(any('duplicate' in error for error in result['errors']), result)

    def test_actual_batch_records_the_repeated_path_as_a_failure(self):
        repository = self.root / 'repo'
        (repository / 'scripts').mkdir(parents=True)
        source_root = Path(__file__).resolve().parents[3]
        shutil.copyfile(source_root / 'scripts/revalidate_all.py',
                        repository / 'scripts/revalidate_all.py')
        write_packet(repository / 'research/repeated',
                     f'{{"data.txt": "{STALE}", "data.txt": "{ACTUAL}"}}')
        output = repository / 'audit'
        run = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('run.py')),
                              '--repo', str(repository), '--output', str(output)],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        row = json.loads((output / 'results.json').read_bytes())[0]
        self.assertEqual(row['manifest_check']['status'], 'fail', row)
        self.assertEqual(row['overall'], 'fail', row)


if __name__ == '__main__':
    unittest.main()
