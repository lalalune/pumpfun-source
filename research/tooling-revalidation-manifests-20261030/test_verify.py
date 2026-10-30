"""Retained manifests, corruption controls and CLI discovery integration."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import revalidate_all as audit

PACKETS = tuple(
    f'amm-multi-hop-{hops}fee-table-split-{mode}-chains-20261029'
    for hops in ('', 'four-hop-', 'five-hop-')
    for mode in ('liquidity', 'liquidity-tf', 'mode', 'mode-tf')
)


class ManifestTests(unittest.TestCase):
    def test_all_retained_record_manifests(self):
        checked = 0
        for name in PACKETS:
            with self.subTest(packet=name):
                packet = ROOT / 'research' / name
                expected = json.loads((packet / 'MANIFEST.json').read_text(encoding='utf-8'))
                result = audit.check_manifest(packet)
                self.assertEqual(result['status'], 'pass', result)
                self.assertEqual(result['files_checked'], len(expected['files']))
                self.assertEqual(result['files_expected'], len(expected['files']))
                checked += result['files_checked']
        self.assertEqual(checked, 297)

    def test_retained_flat_manifest(self):
        for name in ('legacy-capture-metadata', 'roadmap-call-classification',
                     'source-manifest-symlinks', 'token-program-constant-detector'):
            with self.subTest(packet=name):
                packet = ROOT / f'research/tooling-{name}-20261029'
                result = audit.check_manifest(packet)
                self.assertEqual(result, {'status': 'pass', 'files_checked': 7,
                                         'files_expected': 7, 'errors': []})

    def test_real_packet_corruption_size_missing_and_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary) / 'packet'
            shutil.copytree(ROOT / 'research' / PACKETS[0], packet)
            manifest = packet / 'MANIFEST.json'
            saved_manifest = manifest.read_bytes()
            rows = json.loads(saved_manifest)['files']
            row = rows[0]
            target = packet / row['path']
            original = target.read_bytes()
            target.write_bytes(bytes([original[0] ^ 1]) + original[1:])
            self.assertIn('hash_mismatch: ' + row['path'], audit.check_manifest(packet)['errors'])
            target.write_bytes(original)
            row['bytes'] += 1
            manifest.write_text(json.dumps({'files': rows}), encoding='utf-8')
            self.assertEqual(audit.check_manifest(packet)['errors'], ['size_mismatch: ' + row['path']])
            manifest.write_bytes(saved_manifest)
            target.unlink()
            self.assertIn('missing: ' + row['path'], audit.check_manifest(packet)['errors'])
            target.mkdir()
            self.assertIn('not_a_file: ' + row['path'], audit.check_manifest(packet)['errors'])

    def test_invalid_records_do_not_pass(self):
        valid = {'path': 'payload', 'sha256': 'a' * 64}
        invalid = [[], {'files': [None]}, {'files': [{'path': 'payload'}]},
                   {'files': [valid, valid]}, {'files': [{**valid, 'sha256': 'not-a-digest'}]},
                   {'files': [{**valid, 'path': ''}]},
                   {'files': [{**valid, 'bytes': size} for size in (-1, True, '4')]},
                   {'files': [{**valid, 'unsupported': 1}]}, {'metadata': {'version': 1}}]
        for document in invalid:
            with self.subTest(document=document), self.assertRaises(ValueError):
                audit.manifest_records(document)
        for size in (-1, True, '4'):
            with self.subTest(size=size), self.assertRaises(ValueError):
                audit.manifest_records({'files': [{**valid, 'bytes': size}]})
        self.assertEqual(audit.manifest_records({'files': [valid]}), [valid])

    def test_exact_manifest_names_and_ambiguity(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary)
            (packet / 'Manifest.json').write_text('{}', encoding='utf-8')
            self.assertEqual(audit.manifest_paths(packet), [])
            self.assertEqual(audit.check_manifest(packet)['status'], 'no_manifest')
            # Both actual spellings can coexist on case-sensitive filesystems.
            # Supply that inventory explicitly so this control also runs on Windows.
            with patch.object(audit, 'manifest_paths', return_value=[
                    packet / 'manifest.json', packet / 'MANIFEST.json']):
                self.assertEqual(audit.check_manifest(packet)['status'], 'fail')

    def test_cli_discovers_uppercase_record_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet = root / 'research/retained'
            packet.mkdir(parents=True)
            data = b'retained payload'
            (packet / 'payload').write_bytes(data)
            (packet / 'MANIFEST.json').write_text(json.dumps({'files': [
                {'path': 'payload', 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
            ]}), encoding='utf-8')
            output = root / 'audit'
            with patch.object(audit, 'REPO', root), patch.object(sys, 'argv', [
                    'revalidate_all.py', '--output', str(output)]), contextlib.redirect_stdout(io.StringIO()):
                audit.main()
            summary = json.loads((output / 'summary.json').read_text())
            rows = json.loads((output / 'results.json').read_text())
            self.assertEqual(summary['packets_with_manifest'], 1)
            self.assertTrue(rows[0]['has_manifest'])
            self.assertEqual(rows[0]['manifest_check']['files_checked'], 1)
            self.assertEqual(rows[0]['overall'], 'pass')


if __name__ == '__main__':
    unittest.main(verbosity=2)
