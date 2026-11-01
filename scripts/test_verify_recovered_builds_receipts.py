"""The generic receipt aggregation in verify_recovered_builds.py must not
certify more differential cases than the distinct receipts actually record.

Builds a fabricated retained-state tree (repro/ is gitignored local state)
with identical original/candidate bytes so every hash binding passes, then
runs the real CLI as a subprocess for each receipt shape.
"""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
from compare import compare  # noqa: E402


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class RecoveredBuildReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        scripts = self.root / 'scripts'
        scripts.mkdir(parents=True)
        for name in ('verify_recovered_builds.py', 'compare.py', 'analyze.py'):
            shutil.copyfile(REPO / 'scripts' / name, scripts / name)
        blob = bytes(4096)
        self.digest = sha256(blob)
        cand = self.root / 'cand'
        cand.mkdir()
        (cand / 'candidate.so').write_bytes(blob)
        original = self.root / 'evidence/original/pump'
        original.mkdir(parents=True)
        (original / 'deployed.so').write_bytes(blob)
        log = b'build log\n'
        (cand / 'build.log').write_bytes(log)
        (cand / 'report.json').write_text(json.dumps({
            'source_sha256': {},
            'comparison': compare(blob, blob),
            'build_log_sha256': sha256(log),
        }))

    def receipt(self, name, **fields):
        row = {'candidate_sha256': self.digest,
               'original_sha256': self.digest, 'mismatches': []}
        row.update(fields)
        (self.root / 'cand' / name).write_text(json.dumps(row))
        return 'cand/' + name

    def run_verifier(self, reports, validated_cases, sequence=()):
        status = {'pump': {
            'candidate_artifact': 'cand/candidate.so',
            'comparison_report': 'cand/report.json',
            'build_log': 'cand/build.log',
            'validated_cases': validated_cases,
            'validation_reports': reports,
            'signed_sequence_reports': list(sequence),
        }}
        repro = self.root / 'repro'
        repro.mkdir(exist_ok=True)
        (repro / 'status.json').write_text(json.dumps(status))
        run = subprocess.run(
            [sys.executable, '-B',
             str(self.root / 'scripts/verify_recovered_builds.py'),
             '--program', 'pump'],
            cwd=self.root, capture_output=True, text=True)
        return run.returncode

    def test_legitimate_single_receipt_verifies(self):
        good = self.receipt('good.json', case_count=5000)
        self.assertEqual(self.run_verifier([good], 5000), 0)

    def test_inflated_claim_with_single_receipt_fails(self):
        good = self.receipt('good.json', case_count=5000)
        self.assertNotEqual(self.run_verifier([good], 10000), 0)

    def test_duplicate_receipt_listing_is_rejected(self):
        good = self.receipt('good.json', case_count=5000)
        self.assertNotEqual(self.run_verifier([good, good], 10000), 0)

    def test_fractional_case_counts_are_rejected(self):
        a = self.receipt('a.json', case_count=9999.5)
        b = self.receipt('b.json', case_count=0.5)
        self.assertNotEqual(self.run_verifier([a, b], 10000), 0)

    def test_boolean_case_count_is_rejected(self):
        a = self.receipt('a.json', case_count=True)
        self.assertNotEqual(self.run_verifier([a, a], 2), 0)

    def test_a_signed_sequence_with_no_steps_is_rejected(self):
        # all() over an empty step list is true, so the receipt verified nothing.
        sequence = self.receipt('sequence.json', steps=[])
        self.assertNotEqual(self.run_verifier([], 0, sequence=[sequence]), 0)

    def test_a_signed_sequence_with_a_matching_step_verifies(self):
        step = {'match': True, 'original': {'signature_verification': True},
                'candidate': {'signature_verification': True}}
        sequence = self.receipt('sequence.json', steps=[step])
        self.assertEqual(self.run_verifier([], 0, sequence=[sequence]), 0)

    def test_a_signed_sequence_with_a_failed_step_is_rejected(self):
        step = {'match': False, 'original': {'signature_verification': True},
                'candidate': {'signature_verification': True}}
        sequence = self.receipt('sequence.json', steps=[step])
        self.assertNotEqual(self.run_verifier([], 0, sequence=[sequence]), 0)

    def test_failures_shadowed_by_empty_mismatches_are_rejected(self):
        a = self.receipt('a.json', case_count=10000,
                         failures=['case 7: candidate diverged'])
        self.assertNotEqual(self.run_verifier([a], 10000), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
