"""Path-keyed manifest records are a retained format, not a parse failure."""
import hashlib
import json
from pathlib import Path
import tempfile
import shutil
import subprocess
import sys
import unittest

import revalidate_all as runner

REPO = Path(__file__).resolve().parents[1]
RETAINED_PACKET = REPO / 'research/window-attribution-resubmit-20261029'


class PathKeyedManifestTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.packet = Path(folder.name)
        self.payload = self.packet / 'payload.txt'
        self.payload.write_bytes(b'bound bytes\n')
        self.record = {'bytes': 12, 'sha256': hashlib.sha256(b'bound bytes\n').hexdigest()}

    def write_manifest(self, document):
        (self.packet / 'manifest.json').write_text(json.dumps(document), encoding='utf-8')

    def test_retained_packet_passes_its_manifest_check(self):
        result = runner.check_manifest(RETAINED_PACKET)
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['files_checked'], result['files_expected'])

    def test_path_keyed_records_are_checked(self):
        self.write_manifest({'payload.txt': self.record})
        self.assertEqual(runner.check_manifest(self.packet)['status'], 'pass')

    def test_path_keyed_records_keep_hash_and_size_checks(self):
        self.write_manifest({'payload.txt': {**self.record, 'bytes': 13}})
        self.assertEqual(runner.check_manifest(self.packet)['errors'], ['size_mismatch: payload.txt'])
        self.write_manifest({'payload.txt': {**self.record, 'sha256': 'a' * 64}})
        self.assertEqual(runner.check_manifest(self.packet)['errors'], ['hash_mismatch: payload.txt'])

    def test_a_record_cannot_name_a_different_path_than_its_key(self):
        self.write_manifest({'payload.txt': {**self.record, 'path': 'other.txt'}})
        self.assertEqual(runner.check_manifest(self.packet)['status'], 'manifest_parse_error')

    def test_other_nested_objects_remain_invalid(self):
        for document in ({'metadata': {'version': 1}}, {'payload.txt': {'bytes': 12}},
                         {'payload.txt': {**self.record, 'unsupported': 1}}):
            with self.subTest(document=document), self.assertRaises(ValueError):
                runner.manifest_records(document)

    def test_invalid_byte_counts_and_unsafe_paths_are_rejected(self):
        for value in (-1, True, 1.5, '12'):
            with self.subTest(bytes=value), self.assertRaises(ValueError):
                runner.manifest_records({'payload.txt': {**self.record, 'bytes': value}})
        self.write_manifest({'../outside.txt': self.record})
        result=runner.check_manifest(self.packet)
        self.assertEqual(result['status'],'fail')
        self.assertEqual(result['files_checked'],0)

    def test_actual_batch_keeps_pass_and_failure_verdicts(self):
        repo=self.packet/'repo';(repo/'scripts').mkdir(parents=True)
        shutil.copyfile(Path(runner.__file__),repo/'scripts/revalidate_all.py')
        packet=repo/'research/record-packet';packet.mkdir(parents=True)
        (packet/'payload.txt').write_bytes(b'bound bytes\n')
        (packet/'manifest.json').write_text(json.dumps({'payload.txt':self.record}))
        for changed in (False, True):
            with self.subTest(changed=changed):
                if changed:(packet/'payload.txt').write_bytes(b'changed')
                output=repo/('changed-audit' if changed else 'valid-audit')
                result=subprocess.run([sys.executable,'-B',str(repo/'scripts/revalidate_all.py'),
                    '--output',str(output)],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                rows=json.loads((output/'results.json').read_text())
                self.assertEqual(rows[0]['overall'],'fail' if changed else 'pass')
                self.assertEqual(rows[0]['manifest_check']['files_checked'],1)
                self.assertEqual((packet/'payload.txt').read_bytes(),b'changed' if changed else b'bound bytes\n')


if __name__ == '__main__':
    unittest.main()
