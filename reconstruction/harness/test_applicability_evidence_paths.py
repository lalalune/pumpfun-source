"""Use real filesystem paths and the real inspector CLI to test evidence admission."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from attempt_applicability import FIELDS


ROOT = Path(__file__).resolve().parents[2]
TOOL = Path(__file__).resolve().with_name('attempt_applicability.py')


class EvidencePathTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir()
        self.outside = self.root / 'outside'
        self.outside.mkdir()
        self.captured = ROOT / 'evidence/original/pump_fees/deployed.so'
        self.payload = self.captured.read_bytes()
        self.digest = hashlib.sha256(self.payload).hexdigest()
        (self.outside / 'deployed.so').write_bytes(self.payload)
        # Matching synthetic identities isolate path admission from stale-context
        # classification; this is not an authenticity claim about those identities.
        self.context = {field: self.digest for field in FIELDS}
        (self.root / 'context.json').write_text(json.dumps(self.context), encoding='utf-8')

    def inspect_path(self, name):
        row = {'target': '0x10', 'approach': 'path-admission',
               'data': {'context': self.context,
                        'evidence': [{'path': name, 'sha256': self.digest}]}}
        ledger = self.root / 'ledger.jsonl'
        ledger.write_text(json.dumps(row) + '\n', encoding='utf-8')
        original_ledger = ledger.read_bytes()
        result = subprocess.run([sys.executable, '-B', str(TOOL),
            '--ledger', str(ledger), '--context', str(self.root / 'context.json'),
            '--evidence-root', str(self.evidence), '--target', '0x10',
            '--approach', 'path-admission'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(ledger.read_bytes(), original_ledger)
        self.assertEqual((self.outside / 'deployed.so').read_bytes(), self.payload)
        self.assertEqual(self.captured.read_bytes(), self.payload)
        return json.loads(result.stdout)['rows'][0]

    def test_regular_nested_evidence_remains_compatible(self):
        (self.evidence / 'nested').mkdir()
        shutil.copyfile(self.captured, self.evidence / 'nested/deployed.so')
        self.assertEqual(self.inspect_path('nested/deployed.so')['applicability'], 'compatible')

    @unittest.skipUnless(os.name == 'nt', 'Windows junction semantics')
    def test_junction_to_external_capture_is_unverifiable(self):
        import _winapi
        junction = self.evidence / 'linked'
        _winapi.CreateJunction(str(self.outside), str(junction))
        self.addCleanup(junction.rmdir)
        self.assertFalse(junction.is_symlink())
        self.assertEqual((junction / 'deployed.so').resolve(), self.outside / 'deployed.so')
        result = self.inspect_path('linked/deployed.so')
        self.assertEqual(result['applicability'], 'unverifiable')
        self.assertIn('linked evidence', result['reasons'][0])

    def test_symlinked_external_capture_is_unverifiable(self):
        link = self.evidence / 'linked.so'
        try:
            link.symlink_to(self.outside / 'deployed.so')
        except OSError as error:
            self.skipTest(f'file symlink creation unavailable: {error}')
        result = self.inspect_path('linked.so')
        self.assertEqual(result['applicability'], 'unverifiable')
        self.assertIn('linked evidence', result['reasons'][0])


if __name__ == '__main__':
    unittest.main()
