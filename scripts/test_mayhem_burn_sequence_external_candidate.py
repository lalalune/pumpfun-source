#!/usr/bin/env python3
"""A candidate built outside the checkout must reach the burn-sequence receipt."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import mayhem_burn_sequence as target  # noqa: E402

CAPTURE = ROOT / 'evidence/original/mayhem/deployed.so'
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


class ExternalCandidateTests(unittest.TestCase):
    def test_external_candidate_is_bound_by_its_resolved_path(self):
        with tempfile.TemporaryDirectory() as temporary, \
                mock.patch.object(target, 'run', side_effect=lambda *a: receipt(a[4])):
            root = Path(temporary).resolve()
            fixtures = root / 'fixtures'
            fixtures.mkdir()
            (fixtures / 'fixture-manifest.json').write_text(json.dumps({
                'snapshots': {'eligible': {'accounts': {}}},
                'eligible_families': [FAMILY],
            }))
            candidate = root / 'candidate.so'
            shutil.copyfile(CAPTURE, candidate)
            output = root / 'receipts'
            argv = ['mayhem_burn_sequence.py', '--candidate', str(candidate),
                    '--fixtures', str(fixtures), '--output', str(output)]
            with mock.patch.object(sys, 'argv', argv):
                try:
                    with self.assertRaises(SystemExit) as raised:
                        target.main()
                except ValueError as error:
                    self.fail(f'external candidate stopped the run: {error}; '
                              f'output left behind: {os.listdir(output)}')
            self.assertFalse(raised.exception.code)
            report = json.loads((output / 'comparison.json').read_text())
            self.assertIn(candidate.as_posix(), report['input_sha256'])
            self.assertIn('evidence/original/mayhem/deployed.so', report['input_sha256'])


if __name__ == '__main__':
    unittest.main()
