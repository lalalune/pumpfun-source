"""Exercise progress reporting with the retained npm archive and SDK source bytes."""
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('progress_sdk_auth', APP/'scripts/progress.py')
progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress)


class SdkAuthentication(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='progress-sdk-auth-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        values = {
            'contracts/feature-progress.json': {'asOf': '2026-10-29', 'frontend': [], 'backend': [], 'gates': {}, 'exclusions': [], 'deferred': []},
            'contracts/internal-operations.json': {'operations': []},
            'contracts/developer.openapi.json': {'paths': {}},
            'recovered/modules.json': {'modules': []},
            'evidence/web/manifest.json': {'records': []},
        }
        for name, value in values.items():
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value), encoding='utf-8')
        shutil.copytree(APP/'evidence/sdk', self.root/'evidence/sdk')
        shutil.copytree(APP/'packages/sdk/src', self.root/'packages/sdk/src')
        self.archive = self.root/'evidence/sdk/pump-sdk-4.3.1.tgz'

    def render(self):
        with patch.object(progress, 'ROOT', self.root):
            return progress.render()

    def test_retained_npm_archive_and_sources_keep_existing_credit(self):
        self.assertIn('| Published SDK source | 31 / 31 files | 100% |', self.render())

    def test_changed_gzip_metadata_cannot_keep_the_exact_npm_claim(self):
        body = bytearray(self.archive.read_bytes())
        body[4] ^= 1  # mtime changes archive identity without changing any source byte.
        self.archive.write_bytes(body)
        with self.assertRaisesRegex(ValueError, 'SDK archive npm integrity'):
            self.render()

    def test_repeated_source_member_cannot_inflate_the_file_count(self):
        with tarfile.open(self.archive) as source:
            members = [(m, source.extractfile(m).read() if m.isfile() else None) for m in source]
        duplicate = next((m, body) for m, body in members if m.isfile() and m.name.startswith('package/src/'))
        with tarfile.open(self.archive, 'w:gz') as output:
            for member, body in [*members, duplicate]:
                output.addfile(member, io.BytesIO(body) if body is not None else None)
        metadata = json.loads((self.root/'evidence/sdk/registry.json').read_text(encoding='utf-8'))
        metadata['dist']['integrity'] = 'sha512-' + base64.b64encode(hashlib.sha512(self.archive.read_bytes()).digest()).decode()
        (self.root/'evidence/sdk/registry.json').write_text(json.dumps(metadata), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate SDK source archive member'):
            self.render()
