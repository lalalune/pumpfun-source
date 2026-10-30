#!/usr/bin/env python3
"""The burn-sequence receipt must not report success for zero cases or a mismatch."""
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import mayhem_burn_sequence as target  # noqa: E402

FAMILY = {'accounts': {'mint': 'Mint1111111111111111111111111111111111111111'}}


def receipt(side):
    """Smallest receipt row main() inspects; no VM is executed."""
    second = {'error': None, 'logs_without_compute_numbers': [],
              'transaction_base64': 'AQ==', 'metadata': {'inner_instructions': []},
              'before': {}, 'after': {}}
    return {'error': None, 'parsed_after': None, 'events': [],
            'inner_instructions': [], 'return_data': [],
            'logs_without_compute_numbers': [],
            'transaction_base64': 'AQ==', 'logs': [], 'before': {}, 'after': {},
            'sequential_second': second, 'side': side}


class BurnSequenceStatusTests(unittest.TestCase):
    def fixture(self, root, families):
        fixtures = root / 'fixtures'
        fixtures.mkdir()
        (fixtures / 'fixture-manifest.json').write_text(json.dumps({
            'snapshots': {'eligible': {'accounts': {}}},
            'eligible_families': families,
        }))

    def invoke(self, root, fixtures):
        output = root / 'receipts'
        argv = ['mayhem_burn_sequence.py',
                '--candidate', str(ROOT / 'evidence/original/mayhem/deployed.so'),
                '--fixtures', str(fixtures), '--output', str(output)]
        with mock.patch.object(sys, 'argv', argv):
            target.main()
        return output

    def test_manifest_without_families_is_refused_before_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root, [])
            env = dict(os.environ)
            env.pop('PYTHONOPTIMIZE', None)
            # This is the actual entrypoint: no run(), VM, or argument mocks.
            completed = subprocess.run([
                sys.executable, '-B', str(ROOT / 'scripts/mayhem_burn_sequence.py'),
                '--candidate', str(root / 'missing-candidate.so'),
                '--fixtures', str(root / 'fixtures'), '--output', str(root / 'receipts'),
            ], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn('no eligible families', completed.stderr)
            self.assertNotIn('FileNotFoundError', completed.stderr)
            self.assertFalse((root / 'receipts').exists())

    def test_matching_receipts_exit_zero(self):
        with tempfile.TemporaryDirectory() as temporary, \
                mock.patch.object(target, 'run', side_effect=lambda *a: receipt(a[4])):
            root = Path(temporary)
            self.fixture(root, [FAMILY])
            with self.assertRaises(SystemExit) as raised:
                self.invoke(root, root / 'fixtures')
            self.assertFalse(raised.exception.code)
            self.assertEqual(json.loads((root / 'receipts/comparison.json').read_text())['mismatches'], [])

    def test_differing_receipts_exit_nonzero(self):
        def run(binary, family, manifest, index, side, outdir):
            row = receipt(side)
            if side == 'candidate':
                row['error'] = 'evidence differs'
            return row

        with tempfile.TemporaryDirectory() as temporary, \
                mock.patch.object(target, 'run', side_effect=run):
            root = Path(temporary)
            self.fixture(root, [FAMILY])
            with self.assertRaises(SystemExit) as raised:
                self.invoke(root, root / 'fixtures')
            self.assertTrue(raised.exception.code)
            self.assertEqual(json.loads((root / 'receipts/comparison.json').read_text())['mismatches'], [0])


if __name__ == '__main__':
    unittest.main()
