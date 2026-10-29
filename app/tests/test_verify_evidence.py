"""Evidence integrity checks must remain active under Python optimization."""
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


class EvidenceVerificationTests(unittest.TestCase):
    def test_utf8_metadata_paths_work_without_python_utf8_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('scripts', 'evidence/web/objects', 'evidence/sdk', 'packages/sdk/src'):
                (root / name).mkdir(parents=True)
            script = root / 'scripts/verify-evidence.py'
            shutil.copyfile(Path(__file__).resolve().parents[1] / 'scripts/verify-evidence.py', script)
            records = []
            for name in ('capture-\u4e2d\u6587.txt', 'probe-\u20ac.txt', 'map-\U0001f4c4.txt'):
                captured = root / 'evidence/web/objects' / name
                captured.write_bytes(b'captured')
                records.append({'path': captured.relative_to(root).as_posix(), 'sha256': hashlib.sha256(b'captured').hexdigest()})
            metadata = [
                ('web/manifest.json', {'records': records[:1]}),
                ('api-probes.json', records[1:2]),
                ('source-map-probes.json', records[2:]),
            ]
            for path, value in metadata:
                (root / 'evidence' / path).write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
            source = root / 'packages/sdk/src/index.ts'
            source.write_bytes(b'export {};')
            archive = root / 'evidence/sdk/pump-sdk-4.3.1.tgz'
            with tarfile.open(archive, 'w:gz') as tar:
                package_meta = json.dumps({'name':'@pump-fun/pump-sdk','version':'4.3.1'}).encode('utf-8')
                (root/'packages/sdk/package.json').write_bytes(package_meta)
                identity = tarfile.TarInfo('package/package.json'); identity.size = len(package_meta)
                tar.addfile(identity, io.BytesIO(package_meta))
                member = tarfile.TarInfo('package/src/index.ts')
                member.size = len(source.read_bytes())
                tar.addfile(member, io.BytesIO(source.read_bytes()))
            integrity = 'sha512-' + base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
            (root / 'evidence/sdk/registry.json').write_text(json.dumps({'name':'@pump-fun/pump-sdk','version':'4.3.1','dist': {'integrity': integrity}, 'description': '\u4e2d\u6587'}, ensure_ascii=False), encoding='utf-8')
            captured = root / records[0]['path']
            for flags in ((), ('-O',)):
                command = [sys.executable, '-X', 'utf8=0', *flags, str(script)]
                valid = subprocess.run(command, capture_output=True)
                self.assertEqual(valid.returncode, 0, valid.stderr)
                self.assertIn(b'Verified 3 captured objects', valid.stdout)
                captured.write_bytes(b'changed')
                try:
                    invalid = subprocess.run(command, capture_output=True)
                    self.assertNotEqual(invalid.returncode, 0)
                    self.assertIn(b'Captured object SHA-256 mismatch', invalid.stderr)
                finally:
                    captured.write_bytes(b'captured')
    def test_optimized_python_rejects_each_integrity_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('scripts', 'evidence/web', 'evidence/sdk', 'packages/sdk/src'):
                (root / name).mkdir(parents=True)
            script = root / 'scripts/verify-evidence.py'
            shutil.copyfile(Path(__file__).resolve().parents[1] / 'scripts/verify-evidence.py', script)
            captured = root / 'evidence/web/capture.txt'
            captured.write_bytes(b'captured')
            (root / 'evidence/web/manifest.json').write_text(json.dumps({'records': [
                {'path': 'evidence/web/capture.txt', 'sha256': hashlib.sha256(b'captured').hexdigest()}]}))
            for name in ('api-probes.json', 'source-map-probes.json'):
                (root / 'evidence' / name).write_text('[]')
            archive = root / 'evidence/sdk/pump-sdk-4.3.1.tgz'
            source = root / 'packages/sdk/src/index.ts'
            source.write_bytes(b'export {};')
            with tarfile.open(archive, 'w:gz') as tar:
                package_meta = json.dumps({'name':'@pump-fun/pump-sdk','version':'4.3.1'}).encode('utf-8')
                (root/'packages/sdk/package.json').write_bytes(package_meta)
                identity = tarfile.TarInfo('package/package.json'); identity.size = len(package_meta)
                tar.addfile(identity, io.BytesIO(package_meta))
                member = tarfile.TarInfo('package/src/index.ts')
                member.size = len(source.read_bytes())
                tar.addfile(member, io.BytesIO(source.read_bytes()))
            integrity = 'sha512-' + base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
            (root / 'evidence/sdk/registry.json').write_text(json.dumps({'name':'@pump-fun/pump-sdk','version':'4.3.1','dist': {'integrity': integrity}}))
            def run(*flags):
                return subprocess.run([sys.executable, *flags, str(script)], capture_output=True, text=True)
            for flags in ((), ('-O',)):
                valid = run(*flags)
                self.assertEqual(valid.returncode, 0, valid.stderr)
            for target in (captured, source, archive):
                original = target.read_bytes()
                target.write_bytes(original + b'mutated')
                invalid = run('-O')
                self.assertNotEqual(invalid.returncode, 0, f'Accepted corrupt {target.name}')
                target.write_bytes(original)
            for name in ('extra.ts', 'nested/extra.json', '.extra.ts'):
                extra = source.parent / name
                extra.parent.mkdir(parents=True, exist_ok=True)
                extra.write_bytes(b'{}')
                for flags in ((), ('-O',)):
                    with self.subTest(extra=name, flags=flags):
                        invalid = run(*flags)
                        self.assertNotEqual(invalid.returncode, 0, f'Accepted extra SDK source {name}')
                extra.unlink()
            stray = root / 'evidence/web/objects/stray.bin'
            stray.parent.mkdir(parents=True, exist_ok=True)
            stray.write_bytes(b'stray')
            for flags in ((), ('-O',)):
                with self.subTest(stray=stray.name, flags=flags):
                    invalid = run(*flags)
                    self.assertNotEqual(invalid.returncode, 0, 'Accepted unreferenced captured object')
            stray.unlink()


if __name__ == '__main__':
    unittest.main()
