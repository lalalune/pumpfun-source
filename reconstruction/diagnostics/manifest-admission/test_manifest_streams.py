import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from check import check_manifest


class ManifestStreamTests(unittest.TestCase):
    def test_stream_paths_fail_before_any_payload_is_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary)
            payload = b'ordinary packet evidence\n'
            digest = hashlib.sha256(payload).hexdigest()
            (packet / 'ordinary.txt').write_bytes(payload)
            for name in ('payload.txt:hidden', 'payload.txt:hidden:$DATA', 'payload.txt::$DATA'):
                with self.subTest(name=name):
                    # These are actual NTFS streams on Windows and ordinary
                    # colon-bearing names on POSIX. Neither is a portable
                    # manifest member name.
                    (packet / 'payload.txt').write_bytes(payload)
                    (packet / name).write_bytes(payload)
                    (packet / 'manifest.json').write_text(json.dumps({
                        'ordinary.txt': digest, name: digest,
                    }), encoding='utf-8')
                    result = check_manifest(packet)
                    self.assertEqual(result['status'], 'fail', result)
                    self.assertEqual(result['files_checked'], 0)
                    self.assertIn('file streams', ' '.join(result['errors']))
                    self.assertEqual((packet / 'ordinary.txt').read_bytes(), payload)

    def test_nested_ordinary_file_still_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary)
            (packet / 'sub').mkdir()
            payload = b'ordinary packet evidence\n'
            (packet / 'sub/payload.txt').write_bytes(payload)
            (packet / 'manifest.json').write_text(json.dumps({
                'sub/payload.txt': hashlib.sha256(payload).hexdigest(),
            }), encoding='utf-8')
            result = check_manifest(packet)
            self.assertEqual(result['status'], 'pass', result)
            self.assertEqual(result['files_checked'], 1)


if __name__ == '__main__':
    unittest.main()
