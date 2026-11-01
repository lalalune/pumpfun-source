"""Deterministic resource-budget foundation tests; no disk is filled."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resource_budget as R


class SequenceMeasure:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self, _path):
        return next(self.values)


class ResourceBudgetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def monitor(self, values, floor=100):
        return R.DiskBudget(floor, [self.root], .01, measure=SequenceMeasure(values))

    def test_real_available_bytes_uses_selected_filesystem(self):
        before = os.statvfs(self.root)
        measured = R.available_bytes(self.root)
        after = os.statvfs(self.root)
        low = min(before.f_bavail * before.f_frsize, after.f_bavail * after.f_frsize)
        high = max(before.f_bavail * before.f_frsize, after.f_bavail * after.f_frsize)
        self.assertGreaterEqual(measured, low)
        self.assertLessEqual(measured, high)

    def test_nonexistent_target_uses_existing_ancestor(self):
        target = self.root / 'not-created' / 'output'
        identity = R.filesystem_identity([target])
        self.assertEqual(identity[0]['probe_path'], str(self.root))
        self.assertEqual(identity[0]['monitored_paths'], [str(target)])
        self.assertFalse(target.exists())

    def test_enough_space_records_measurement(self):
        monitor = self.monitor([1000])
        observation = monitor.sample('admission')
        self.assertFalse(observation['filesystems'][0]['below_floor'])
        self.assertIsNone(monitor.guard_fired)

    def test_insufficient_admission_is_explicit(self):
        monitor = self.monitor([99])
        with self.assertRaises(R.DiskBudgetExceeded):
            monitor.sample('admission')
        self.assertEqual(monitor.guard_fired['classification'], 'resource_budget_exceeded')

    def test_runtime_floor_crossing_returns_monitor_reason(self):
        monitor = self.monitor([1000, 99])
        self.assertIsNone(monitor.monitor())
        reason = monitor.monitor()
        self.assertEqual(reason['classification'], 'resource_budget_exceeded')
        self.assertEqual(reason['observation_sequence'], 1)

    def test_multiple_filesystems_are_measured_independently(self):
        rows = [
            {'device': 10, 'probe_path': str(self.root / 'a'),
             'monitored_paths': [str(self.root / 'a')]},
            {'device': 20, 'probe_path': str(self.root / 'b'),
             'monitored_paths': [str(self.root / 'b')]},
        ]
        (self.root / 'a').mkdir(); (self.root / 'b').mkdir()
        devices = {str(self.root / 'a'): 10, str(self.root / 'b'): 20}
        real_stat = Path.stat
        def fake_stat(path):
            result = real_stat(path)
            if str(path) not in devices:
                return result
            class Stat:
                st_dev = devices[str(path)]
            return Stat()
        with patch.object(R, 'filesystem_identity', return_value=rows), \
             patch.object(Path, 'stat', fake_stat):
            monitor = R.DiskBudget(100, [self.root / 'a', self.root / 'b'], .1,
                                   measure=SequenceMeasure([500, 90]))
            with self.assertRaises(R.DiskBudgetExceeded) as caught:
                monitor.sample('admission')
        self.assertEqual([row['available_bytes'] for row in caught.exception.observation['filesystems']],
                         [500, 90])

    def test_invalid_numeric_configuration_is_rejected(self):
        for floor in (0, -1, True, 1.5, '100'):
            with self.subTest(floor=floor), self.assertRaises(ValueError):
                R.DiskBudgetConfig(floor)
        for interval in (0, -1, True, float('inf'), float('nan'), 3601, '1'):
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                R.DiskBudgetConfig(100, check_interval=interval)

    def test_invalid_or_unavailable_measurement_fails_closed(self):
        for value in (-1, True, 1.5):
            with self.subTest(value=value):
                monitor = R.DiskBudget(100, [self.root], .1, measure=lambda _: value)
                with self.assertRaises(R.DiskMeasurementError):
                    monitor.sample('admission')
        monitor = R.DiskBudget(100, [self.root], .1,
                               measure=lambda _: (_ for _ in ()).throw(OSError('unavailable')))
        with self.assertRaisesRegex(R.DiskMeasurementError, 'unavailable'):
            monitor.sample('admission')

    def valid_receipt(self):
        monitor = self.monitor([1000, 800])
        monitor.sample('admission'); monitor.sample('build_end', enforce=False)
        return monitor, monitor.receipt(operation='fixture', outcome='success',
                                        build_identity={'source_sha256': 'a' * 64},
                                        retained_logs=['build.log'])

    def test_receipt_verifier_recomputes_minimum(self):
        monitor, receipt = self.valid_receipt()
        result = R.verify_receipt(receipt, expected_budget=monitor.identity)
        self.assertTrue(result['accepted'])
        self.assertEqual(next(iter(result['minimum_observed_free_bytes'].values())), 800)

    def test_receipt_negative_controls(self):
        monitor, receipt = self.valid_receipt()
        mutations = []
        changed = copy.deepcopy(receipt); changed['minimum_observed_free_bytes'] = {}; mutations.append(changed)
        changed = copy.deepcopy(receipt); changed['observations'][0]['filesystems'][0]['below_floor'] = True; mutations.append(changed)
        changed = copy.deepcopy(receipt); changed['observations'][0]['sequence'] = 9; mutations.append(changed)
        changed = copy.deepcopy(receipt); changed['budget']['implementation_sha256'] = '0' * 64; mutations.append(changed)
        for changed in mutations:
            with self.subTest(mutation=mutations.index(changed)), self.assertRaises(ValueError):
                R.verify_receipt(changed, expected_budget=monitor.identity)

    def test_stale_budget_identity_is_rejected(self):
        _, receipt = self.valid_receipt()
        other = self.monitor([1000], floor=101)
        with self.assertRaisesRegex(ValueError, 'stale'):
            R.verify_receipt(receipt, expected_budget=other.identity)

    def test_atomic_receipt_publication_replaces_complete_json(self):
        monitor, receipt = self.valid_receipt()
        path = self.root / 'receipts' / 'resource.json'
        path.parent.mkdir()
        path.write_text('{old')
        R.atomic_write_receipt(path, receipt)
        self.assertEqual(json.loads(path.read_text()), receipt)
        self.assertEqual(list(path.parent.iterdir()), [path])


if __name__ == '__main__':
    unittest.main()
