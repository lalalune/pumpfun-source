"""Run the saved-evidence CLI on real capture copies in every optimization mode."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODES = (((), None), (('-O',), None), (('-OO',), None), ((), '1'), ((), '2'))


class CaptureVerificationModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='capture-verification-modes-')
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name)
        (cls.root / 'scripts').mkdir()
        for name in ('verify_evidence.py', 'capture.py', 'analyze.py'):
            shutil.copyfile(ROOT / 'scripts' / name, cls.root / 'scripts' / name)
        shutil.copytree(ROOT / 'evidence', cls.root / 'evidence')

    def gate(self, flags, optimize):
        environment = dict(os.environ)
        environment.pop('PYTHONOPTIMIZE', None)
        if optimize is not None:
            environment['PYTHONOPTIMIZE'] = optimize
        return subprocess.run(
            [sys.executable, '-B', *flags, 'scripts/verify_evidence.py'],
            cwd=self.root, env=environment, capture_output=True, text=True, timeout=30)

    @contextmanager
    def changed_record(self, relative, mutate):
        path = self.root / relative
        original = path.read_bytes()
        record = json.loads(original)
        mutate(record)
        path.write_text(json.dumps(record), encoding='utf-8')
        try:
            yield
        finally:
            path.write_bytes(original)

    def assert_rejected(self, message=None):
        for flags, optimize in MODES:
            with self.subTest(flags=flags, environment_optimize=optimize):
                result = self.gate(flags, optimize)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertNotIn('9 captures verified', result.stdout)
                if message is not None:
                    self.assertIn(message, result.stderr)

    def test_real_corpus_passes_in_all_modes(self):
        for flags, optimize in MODES:
            with self.subTest(flags=flags, environment_optimize=optimize):
                result = self.gate(flags, optimize)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('9 captures verified', result.stdout)

    def test_nonfinalized_commitments_are_rejected(self):
        for folder in ('original/pump', 'dependencies/associated_token'):
            for value in ('processed', 'confirmed', None):
                with self.subTest(folder=folder, commitment=value):
                    def mutate(record):
                        if value is None:
                            record.pop('commitment')
                        else:
                            record['commitment'] = value
                    with self.changed_record(f'evidence/{folder}/capture.json', mutate):
                        self.assert_rejected(f'evidence/{folder}: commitment')

    def test_self_consistent_swapped_program_captures_are_rejected(self):
        original = self.root / 'evidence/original'
        (original / 'pump').rename(original / 'swap')
        (original / 'pump_amm').rename(original / 'pump')
        (original / 'swap').rename(original / 'pump_amm')
        try:
            self.assert_rejected('evidence/original/pump: capture program')
        finally:
            (original / 'pump').rename(original / 'swap')
            (original / 'pump_amm').rename(original / 'pump')
            (original / 'swap').rename(original / 'pump_amm')

    def test_legacy_program_identity_is_rejected(self):
        def mutate(record):
            record['program'] = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
        with self.changed_record('evidence/dependencies/associated_token/capture.json', mutate):
            self.assert_rejected('evidence/dependencies/associated_token: capture program')

    def test_removed_idl_and_listing_entry_are_rejected(self):
        path = self.root / 'evidence/upstream/pump_fees.json'
        original = path.read_bytes()
        with self.changed_record('evidence/upstream/provenance.json',
                                 lambda record: record['file_sha256'].pop('pump_fees.json')):
            path.unlink()
            try:
                self.assert_rejected('upstream IDL missing')
            finally:
                path.write_bytes(original)

    def test_unexpected_upstream_listing_entry_is_rejected(self):
        provenance = 'evidence/upstream/provenance.json'
        def mutate(record):
            record['file_sha256']['pump_extra.json'] = record['file_sha256']['pump.json']
        extra = self.root / 'evidence/upstream/pump_extra.json'
        shutil.copyfile(self.root / 'evidence/upstream/pump.json', extra)
        try:
            with self.changed_record(provenance, mutate):
                self.assert_rejected('unexpected upstream file')
        finally:
            extra.unlink()

    def test_payload_hash_checks_remain_active(self):
        path = self.root / 'evidence/original/pump/deployed.so'
        original = path.read_bytes()
        damaged = bytearray(original)
        damaged[0x1000] ^= 1
        path.write_bytes(damaged)
        try:
            self.assert_rejected()
        finally:
            path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
