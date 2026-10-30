"""Regression controls for legacy/upgradeable capture metadata."""
from pathlib import Path
import contextlib
import gzip
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest

import proof

P = Path(__file__).resolve().parent
FOLDER = 'evidence/dependencies/associated_token'


class CaptureMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = proof.check(proof.REPO)
        cls.record = json.loads((proof.REPO / FOLDER / 'capture.json').read_text())

    def blocked(self, **changes):
        record = dict(self.record)
        record.update(changes)
        return proof.validate(record, FOLDER)

    def load(self, folder):
        return json.loads((proof.REPO / folder / 'capture.json').read_text())

    def test_baseline(self):
        self.assertEqual(self.report['legacy_captures'], 1)
        self.assertEqual(self.report['upgradeable_captures'], 8)
        self.assertEqual(proof.validate(self.record, FOLDER), [])

    def test_legacy_deploy_slot_is_rejected(self):
        self.assertIn('legacy deploy slot', ' '.join(self.blocked(last_deploy_slot=1)))

    def test_legacy_authority_is_rejected(self):
        self.assertIn('legacy upgrade authority', ' '.join(
            self.blocked(upgrade_authority='11111111111111111111111111111111')
        ))

    def test_legacy_programdata_key_is_rejected(self):
        failures = ' '.join(self.blocked(programdata='11111111111111111111111111111111'))
        self.assertIn('legacy programdata keys', failures)

    def test_upgradeable_authority_must_decode_to_32_bytes(self):
        folder = 'evidence/original/pump'
        record = self.load(folder)
        record['upgrade_authority'] = 'not-a-pubkey'
        self.assertIn('upgradeable authority', ' '.join(proof.validate(record, folder)))

    def test_unknown_loader_is_rejected(self):
        folder = 'evidence/original/pump'
        record = self.load(folder)
        record['loader'] = 'upgradeable-v2'
        self.assertIn('expected loader', ' '.join(proof.validate(record, folder)))

    def test_loader_is_bound_to_the_known_capture_folder(self):
        record = self.load('evidence/original/pump')
        self.assertIn('expected loader', ' '.join(proof.validate(record, FOLDER)))

    def test_archived_gate_accepts_the_legacy_mutation(self):
        sys.path.insert(0, str(proof.REPO / 'scripts'))
        import verify_evidence
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(proof.REPO / FOLDER, root / FOLDER)
            shutil.copytree(proof.REPO / 'evidence/upstream', root / 'evidence/upstream')
            path = root / FOLDER / 'capture.json'
            record = json.loads(path.read_text())
            record['last_deploy_slot'] = 1
            record['upgrade_authority'] = '11111111111111111111111111111111'
            path.write_text(json.dumps(record))
            old_root, old_expected = verify_evidence.ROOT, verify_evidence.EXPECTED_CAPTURES
            verify_evidence.ROOT = root
            verify_evidence.EXPECTED_CAPTURES = frozenset({FOLDER})
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    verify_evidence.main()
            finally:
                verify_evidence.ROOT, verify_evidence.EXPECTED_CAPTURES = old_root, old_expected
            self.assertIn('legacy deploy slot', ' '.join(proof.validate(record, FOLDER)))
            self.assertIn('legacy upgrade authority', ' '.join(proof.validate(record, FOLDER)))

    def test_saved_observations_match(self):
        saved = json.loads(gzip.decompress((P / 'observations.json.gz').read_bytes()))
        self.assertEqual(saved, self.report)

    def test_manifest_inventory(self):
        saved = json.loads((P / 'manifest.json').read_text())
        actual = {
            str(path.relative_to(P)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(P.rglob('*'))
            if path.is_file() and path.name != 'manifest.json'
            and '__pycache__' not in path.parts and path.suffix != '.pyc'
        }
        self.assertEqual(saved, actual)


if __name__ == '__main__':
    unittest.main(verbosity=2)
