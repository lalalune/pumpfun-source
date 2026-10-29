"""Qualify package identity using the retained npm archive, not a stand-in SDK."""
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1]


class SdkPackageIdentity(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='sdk-identity-')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for folder in ['scripts', 'evidence/sdk', 'evidence/web']:
            (self.root/folder).mkdir(parents=True)
        shutil.copyfile(APP/'scripts/verify-evidence.py', self.root/'scripts/verify-evidence.py')
        shutil.copytree(APP/'packages/sdk/src', self.root/'packages/sdk/src')
        shutil.copyfile(APP/'packages/sdk/package.json', self.root/'packages/sdk/package.json')
        self.archive = self.root/'evidence/sdk/pump-sdk-4.3.1.tgz'
        shutil.copyfile(APP/'evidence/sdk/pump-sdk-4.3.1.tgz', self.archive)
        self.assertEqual(hashlib.sha256(self.archive.read_bytes()).hexdigest(), 'c8ff4e850651c81e9f488bfc6dffb4513a041bb4bca0819879dc19d9a72a4641')
        self.registry = json.loads((APP/'evidence/sdk/registry.json').read_text(encoding='utf-8'))
        self.write_registry(self.registry)
        (self.root/'evidence/web/manifest.json').write_text('{"records":[]}', encoding='utf-8')
        for name in ['api-probes.json', 'source-map-probes.json']:
            (self.root/'evidence'/name).write_text('[]', encoding='utf-8')

    def write_registry(self, value):
        (self.root/'evidence/sdk/registry.json').write_text(json.dumps(value), encoding='utf-8')

    def verify(self, valid, message='SDK package identity'):
        for flags in [[], ['-O']]:
            with self.subTest(flags=flags):
                result = subprocess.run([sys.executable, *flags, str(self.root/'scripts/verify-evidence.py')], capture_output=True)
                if valid:
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn(message.encode(), result.stderr)

    def test_valid_retained_archive_and_local_sources(self):
        self.verify(True)

    def test_registry_identity_cannot_disagree_with_the_fixed_package(self):
        for field, wrong in [('name', '@other/wrong-sdk'), ('version', '0.0.0')]:
            for value in [wrong, None]:
                with self.subTest(field=field, value=value):
                    altered = dict(self.registry)
                    if value is None:
                        del altered[field]
                    else:
                        altered[field] = value
                    self.write_registry(altered)
                    self.verify(False)

    def test_archive_manifest_is_unique_and_matches_the_package_identity(self):
        for mode in ['wrong-name', 'wrong-version', 'missing', 'duplicate']:
            with self.subTest(mode=mode):
                with tarfile.open(APP/'evidence/sdk/pump-sdk-4.3.1.tgz') as source, tarfile.open(self.archive, 'w:gz') as target:
                    for member in source.getmembers():
                        data = source.extractfile(member).read() if member.isfile() else None
                        if member.name == 'package/package.json':
                            if mode == 'missing':
                                continue
                            meta = json.loads(data)
                            if mode == 'wrong-name': meta['name'] = '@other/wrong-sdk'
                            if mode == 'wrong-version': meta['version'] = '0.0.0'
                            data = json.dumps(meta).encode('utf-8')
                            member.size = len(data)
                            if mode == 'duplicate': target.addfile(member, io.BytesIO(data))
                        target.addfile(member, io.BytesIO(data) if data is not None else None)
                registry = dict(self.registry)
                registry['dist'] = {**registry['dist'], 'integrity': 'sha512-'+base64.b64encode(hashlib.sha512(self.archive.read_bytes()).digest()).decode()}
                self.write_registry(registry)
                self.verify(False)

    def test_local_package_identity_is_checked_without_requiring_manifest_byte_equality(self):
        path = self.root/'packages/sdk/package.json'
        meta = json.loads(path.read_text(encoding='utf-8'))
        meta['scripts'] = {'build': 'a reviewed local build adjustment'}
        path.write_text(json.dumps(meta), encoding='utf-8')
        self.verify(True)
        meta['version'] = '0.0.0'
        path.write_text(json.dumps(meta), encoding='utf-8')
        self.verify(False)


if __name__ == '__main__': unittest.main()
