"""Preserve authenticated manifest checkpoints across actual CLI captures."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from capture_cli_fixture import CaptureCli


@unittest.skipUnless(shutil.which('openssl'), 'real loopback TLS fixture requires openssl')
class SnapshotHistory(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix='capture-history-cli-')
        self.addCleanup(temporary.cleanup)
        fixture = CaptureCli(Path(temporary.name))
        self.addCleanup(fixture.close)
        return fixture

    def captured(self, fixture, version, *args):
        result = fixture.run(version, *args)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        summary = json.loads(result.stdout)
        self.assertEqual(summary['records'], 14)
        self.assertEqual(summary['successful'], 14)
        return fixture.manifest()

    def verified(self, fixture):
        result = fixture.verify()
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_fresh_rerun_preserves_both_manifests_and_every_object(self):
        f = self.fixture()
        before = self.captured(f, 1)
        original_objects = f.objects(before)
        self.verified(f)
        after = self.captured(f, 2)
        self.assertNotEqual(before, after)
        self.assertEqual(len(f.server.events), 28)
        for relative, raw in original_objects.items():
            self.assertEqual((f.root / relative).read_bytes(), raw)
        self.assertTrue(f.archive(before).is_file(), 'old manifest was replaced without a retained checkpoint')
        self.assertEqual(f.archive(before).read_bytes(), before)
        self.assertEqual(f.archive(after).read_bytes(), after)
        self.verified(f)

        # Archival does not excuse tampered historical payloads or unrelated
        # objects, and every retained manifest's metadata remains checked.
        relative, raw = next(iter(original_objects.items()))
        (f.root / relative).write_bytes(b'changed historical bytes')
        self.assertIn(b'SHA-256 mismatch', f.verify().stderr)
        (f.root / relative).write_bytes(raw)
        f.archive(before).write_bytes(b'changed manifest')
        self.assertIn(b'manifest', f.verify().stderr.lower())
        f.archive(before).write_bytes(before)
        surplus = f.web / 'objects/unreferenced'
        surplus.write_bytes(b'unreferenced')
        self.assertIn(b'unreferenced', f.verify().stderr)
        surplus.unlink()
        altered = json.loads(before)
        altered['records'][0]['sha256'] = '0' * 64
        forged = json.dumps(altered).encode()
        f.archive(forged).write_bytes(forged)
        self.assertIn(b'SHA-256 mismatch', f.verify().stderr)
        f.archive(forged).unlink()
        self.verified(f)

    def test_resume_retains_full_prior_manifest_and_record_acquisition_times(self):
        f = self.fixture()
        before = self.captured(f, 1)
        after = self.captured(f, 2, '--resume')
        self.assertNotEqual(before, after)
        self.assertEqual(len(f.server.events), 14, 'resume must reuse authenticated bodies')
        self.assertEqual(json.loads(before)['records'], json.loads(after)['records'])
        self.assertTrue(f.archive(before).is_file(), 'resume discarded the prior batch checkpoint')
        self.assertEqual(f.archive(before).read_bytes(), before)
        self.assertEqual(f.archive(after).read_bytes(), after)
        self.verified(f)

    def test_modified_existing_archive_blocks_alias_replacement(self):
        f = self.fixture()
        before = self.captured(f, 1)
        archived = f.archive(before)
        archived.parent.mkdir(parents=True, exist_ok=True)
        archived.write_bytes(b'altered retained checkpoint')
        result = f.run(2)
        self.assertNotEqual(result.returncode, 0, 'a mismatched retained checkpoint must not be replaced')
        self.assertEqual(f.manifest(), before)
        self.assertEqual(archived.read_bytes(), b'altered retained checkpoint')

    def test_malformed_prior_manifest_is_preserved_but_not_verified_as_valid(self):
        f = self.fixture()
        f.web.mkdir(parents=True)
        incomplete = b'preserve this incomplete prior manifest exactly'
        (f.web / 'manifest.json').write_bytes(incomplete)
        current = self.captured(f, 1)
        self.assertNotEqual(current, incomplete)
        self.assertTrue(f.archive(incomplete).is_file(), 'incomplete prior metadata was discarded')
        self.assertEqual(f.archive(incomplete).read_bytes(), incomplete)
        result = f.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'JSONDecodeError', result.stderr)
        self.assertEqual(f.archive(incomplete).read_bytes(), incomplete)


if __name__ == '__main__':
    unittest.main()
