"""Fastbuild disk-budget integration without a real compiler or disk filling."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fastbuild as F
import resource_budget as R


class AvailableSequence:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self, _path):
        value = next(self.values)
        if isinstance(value, Exception):
            raise value
        return value


class FastbuildResourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'; self.source.mkdir()
        (self.source / 'input').write_text('source\n')
        self.work = self.root / 'work'
        self.out = self.root / 'output'
        self.config = R.DiskBudgetConfig(100, check_interval=.01)

    def test_enough_space_preserves_default_build_result_and_adds_receipt(self):
        def completed(_src, _work, out, **_kwargs):
            out.mkdir(parents=True); (out / 'build.log').write_text('complete\n')
            return {'ok': True, 'marker': 'complete'}
        with patch.object(R, 'available_bytes', return_value=1000), \
             patch.object(F, '_build_locked', side_effect=completed):
            result = F.build(self.source, self.work, self.out, recipe='identity',
                             resource_budget=self.config)
        self.assertTrue(result['ok']); self.assertEqual(result['marker'], 'complete')
        self.assertTrue(result['candidate_published'])
        receipt = json.loads(Path(result['resource_receipt']).read_text())
        verified = R.verify_receipt(receipt)
        self.assertTrue(verified['accepted'])
        self.assertEqual(receipt['outcome'], 'success')
        self.assertEqual(receipt['retained_logs'], [str(self.out / 'build.log')])

    def test_insufficient_initial_space_rejects_before_lock_or_staging(self):
        self.out.mkdir(); sentinel = self.out / 'candidate.so'; sentinel.write_bytes(b'prior')
        with patch.object(R, 'available_bytes', return_value=99), \
             patch.object(F, '_build_locked') as build:
            result = F.build(self.source, self.work, self.out, recipe='identity',
                             resource_budget=self.config)
        build.assert_not_called()
        self.assertFalse(result['ok'])
        self.assertEqual(result['failure_classification'], 'resource_budget_exceeded')
        self.assertEqual(sentinel.read_bytes(), b'prior')
        receipt = json.loads(Path(result['resource_receipt']).read_text())
        self.assertTrue(R.verify_receipt(receipt)['guard_fired'])
        self.assertFalse(receipt['candidate_published'])

    def test_unavailable_measurement_is_structured_infrastructure_failure(self):
        with patch.object(R, 'available_bytes', side_effect=OSError('stat unavailable')), \
             patch.object(F, '_build_locked') as build:
            result = F.build(self.source, self.work, self.out, recipe='identity',
                             resource_budget=self.config)
        build.assert_not_called()
        self.assertEqual(result['failure_classification'], 'resource_measurement_unavailable')
        receipt = json.loads(Path(result['resource_receipt']).read_text())
        self.assertIn('measurement_error', receipt['observations'][0])
        self.assertTrue(R.verify_receipt(receipt)['accepted'])

    def fixture_build(self, available):
        crate = self.root / 'crate'; crate.mkdir(exist_ok=True)
        (crate / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n')
        recipe = {'triple': 'fixture-target', 'rustc': self.root / 'rustc',
                  'template': self.root / 'missing-template'}
        slot = io.StringIO()
        def compiler(_command, **options):
            reason = options['monitor']()
            result = subprocess.CompletedProcess([], -9, 'partial compiler diagnostics\n')
            result.monitor_result = reason
            return result, False
        patches = (
            patch.object(R, 'available_bytes', side_effect=AvailableSequence(available)),
            patch.object(F, 'RECIPES', {'fixture': recipe}),
            patch.object(F, 'stage', return_value=crate),
            patch.object(F, 'acquire_slot', return_value=slot),
            patch.object(F, 'run_compiler', side_effect=compiler),
        )
        return patches

    def test_floor_crossing_before_compilation_preserves_current_outputs(self):
        self.out.mkdir(); candidate = self.out / 'candidate.so'; candidate.write_bytes(b'prior')
        patches = self.fixture_build([1000, 1000, 99])
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            result = F.build(self.source, self.work, self.out, quiet=True, recipe='fixture',
                             resource_budget=self.config)
        self.assertFalse(result['ok'])
        self.assertEqual(candidate.read_bytes(), b'prior')
        self.assertFalse((self.out / 'previous').exists())

    def test_runtime_floor_crossing_stops_build_and_retains_log_and_archive(self):
        self.out.mkdir()
        (self.out / 'candidate.so').write_bytes(b'prior candidate')
        (self.out / 'unstripped.so').write_bytes(b'prior symbols')
        (self.out / 'build.log').write_text('prior log\n')
        patches = self.fixture_build([1000, 1000, 1000, 99])
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            result = F.build(self.source, self.work, self.out, quiet=True, recipe='fixture',
                             resource_budget=self.config)
        self.assertFalse(result['ok'])
        self.assertEqual(result['failure_classification'], 'resource_budget_exceeded')
        self.assertEqual((self.out / 'build.log').read_text(), 'partial compiler diagnostics\n')
        archive, = (self.out / 'previous').glob('build-*')
        self.assertEqual((archive / 'candidate.so').read_bytes(), b'prior candidate')
        self.assertEqual((archive / 'unstripped.so').read_bytes(), b'prior symbols')
        receipt = json.loads(Path(result['resource_receipt']).read_text())
        self.assertTrue(R.verify_receipt(receipt)['guard_fired'])
        self.assertEqual(receipt['retained_logs'], [str(self.out / 'build.log')])
        self.assertFalse(receipt['candidate_published'])

    def test_staging_failure_retains_diagnostic_receipt_and_propagates(self):
        with patch.object(R, 'available_bytes', return_value=1000), \
             patch.object(F, '_build_locked', side_effect=OSError('controlled staging failure')):
            with self.assertRaisesRegex(OSError, 'controlled staging failure'):
                F.build(self.source, self.work, self.out, recipe='identity',
                        resource_budget=self.config)
        receipt, = (self.work / 'resource-receipts').glob('attempt-*/resource-receipt.json')
        value = json.loads(receipt.read_text())
        self.assertEqual(value['failure_classification'], 'build_infrastructure_failure')
        self.assertTrue(R.verify_receipt(value)['accepted'])

    def test_default_mode_creates_no_resource_receipt(self):
        with patch.object(F, '_build_locked', return_value={'ok': True}):
            self.assertEqual(F.build(self.source, self.work, self.out), {'ok': True})
        self.assertFalse((self.work / 'resource-receipts').exists())


if __name__ == '__main__':
    unittest.main()
