"""Resource-aware experiment regressions using mocked storage measurements."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment_runner as E


class SequenceMeasure:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self, _path):
        value = next(self.values)
        if isinstance(value, Exception):
            raise value
        return value


class ExperimentResourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'; self.source.mkdir()
        (self.source / 'input').write_text('fixture\n')
        self.destination = self.root / 'results'
        self.command = [sys.executable, '-c',
                        'from pathlib import Path;import sys;Path(sys.argv[1],"done").write_text("ok")',
                        '{out}']
        self.config = E.DiskBudgetConfig(100, check_interval=.01)

    def run_trial(self, command=None):
        return E.run_trial(self.source, command or self.command, self.destination,
                           timeout=5, resource_budget=self.config)

    def receipt(self, result):
        path = self.destination / result['attempt'] / 'resource-receipt.json'
        return json.loads(path.read_text())

    def test_insufficient_admission_is_infrastructure_error_and_never_launches(self):
        marker = self.root / 'launched'
        command = [sys.executable, '-c',
                   'from pathlib import Path;import sys;Path(sys.argv[1]).touch()', str(marker)]
        with patch.object(E.RESOURCE, 'available_bytes', return_value=99):
            result = self.run_trial(command)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['reason'], 'resource_budget_exceeded')
        self.assertIsNone(result['returncode'])
        self.assertFalse(marker.exists())
        receipt = self.receipt(result)
        self.assertTrue(E.verify_resource_receipt(receipt)['guard_fired'])
        self.assertEqual(receipt['failure_classification'], 'resource_budget_exceeded')

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX process groups')
    def test_runtime_crossing_stops_owned_trial_but_not_unrelated_process(self):
        pid_file = self.root / 'trial.pid'
        command = [sys.executable, '-c',
                   'import os,time;from pathlib import Path;import sys;'
                   'Path(sys.argv[1]).write_text(str(os.getpid()));time.sleep(30)', str(pid_file)]
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'],
                                     start_new_session=True)
        self.addCleanup(unrelated.wait)
        self.addCleanup(lambda: unrelated.poll() is None and unrelated.kill())
        def available(_path):
            return 99 if pid_file.exists() else 1000
        with patch.object(E.RESOURCE, 'available_bytes', side_effect=available):
            result = self.run_trial(command)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['reason'], 'resource_budget_exceeded')
        self.assertIsNone(unrelated.poll())
        self.assertTrue(pid_file.exists())
        trial_pid = int(pid_file.read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(trial_pid, 0)
        receipt = self.receipt(result)
        self.assertTrue(E.verify_resource_receipt(receipt)['guard_fired'])

    def test_successful_attempt_is_reused_with_same_budget_identity(self):
        with patch.object(E.RESOURCE, 'available_bytes', return_value=1000):
            first = self.run_trial()
            second = self.run_trial()
        self.assertEqual(first['status'], 'pass')
        self.assertTrue(second['reused'])
        self.assertEqual(second['attempt'], first['attempt'])
        receipt = self.receipt(first)
        self.assertEqual(receipt['build_identity'], {'experiment_key': first['key']})
        self.assertTrue(E.verify_resource_receipt(
            receipt, expected_budget=first['inputs']['resource_budget'])['accepted'])

    def test_storage_failure_retries_and_preserves_failed_attempt(self):
        with patch.object(E.RESOURCE, 'available_bytes', return_value=99):
            failed = self.run_trial()
        failed_path = self.destination / failed['attempt']
        before = {path.relative_to(failed_path).as_posix(): path.read_bytes()
                  for path in failed_path.rglob('*') if path.is_file()}
        with patch.object(E.RESOURCE, 'available_bytes', return_value=1000):
            recovered = self.run_trial()
        self.assertEqual(recovered['status'], 'pass')
        self.assertNotEqual(recovered['attempt'], failed['attempt'])
        after = {path.relative_to(failed_path).as_posix(): path.read_bytes()
                 for path in failed_path.rglob('*') if path.is_file()}
        self.assertEqual(after, before)

    def test_semantically_stale_resource_receipt_is_not_reused(self):
        with patch.object(E.RESOURCE, 'available_bytes', return_value=1000):
            first = self.run_trial()
        attempt = self.destination / first['attempt']
        path = attempt / 'resource-receipt.json'
        value = json.loads(path.read_text())
        value['budget']['floor_bytes'] += 1
        path.write_text(json.dumps(value))
        latest_path = self.destination / 'latest.json'
        latest = json.loads(latest_path.read_text())
        latest['artifacts']['resource-receipt.json']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        E.atomic_json(latest_path, latest)
        with patch.object(E.RESOURCE, 'available_bytes', return_value=1000):
            second = self.run_trial()
        self.assertFalse(second['reused'])
        self.assertNotEqual(second['attempt'], first['attempt'])

    def test_concurrent_same_budget_attempt_executes_once(self):
        with patch.object(E.RESOURCE, 'available_bytes', return_value=1000):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: self.run_trial(), range(2)))
        self.assertEqual(len({row['attempt'] for row in results}), 1)
        self.assertEqual(sum(not row['reused'] for row in results), 1)

    def test_measurement_failure_is_not_a_valid_negative_experiment(self):
        with patch.object(E.RESOURCE, 'available_bytes', side_effect=OSError('no statvfs')):
            result = self.run_trial()
        self.assertEqual(result['status'], 'error')
        self.assertNotEqual(result['status'], 'fail')
        self.assertEqual(result['reason'], 'resource_measurement_unavailable')
        self.assertIn('measurement_error', self.receipt(result)['observations'][0])

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX parent-death handling')
    @patch.dict(os.environ, {'XPC_SERVICE_NAME': '0'})
    def test_parent_termination_retains_resource_evidence_and_recovers(self):
        marker = self.root / 'started'
        child = (
            'from pathlib import Path;import os,sys,time;'
            'marker=Path(sys.argv[1]);out=Path(sys.argv[2]);'
            'already=marker.exists();marker.write_text(str(os.getpid()));'
            '(out/("complete" if already else "partial")).write_text("evidence");'
            'time.sleep(0 if already else 30)'
        )
        command = [sys.executable, '-c', child, str(marker), '{out}']
        launcher = (
            'from pathlib import Path;import sys;'
            f'sys.path.insert(0,{str(Path(E.__file__).resolve().parent)!r});'
            'import experiment_runner as E;'
            'E.run_trial(Path(sys.argv[1]),'
            + repr(command) + ',Path(sys.argv[2]),timeout=60,'
            'resource_budget=E.DiskBudgetConfig(1,check_interval=.05))'
        )
        parent = subprocess.Popen([sys.executable, '-I', '-B', '-c', launcher,
                                   str(self.source), str(self.destination)])
        self.addCleanup(lambda: parent.poll() is None and parent.kill())
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(marker.exists(), 'resource-aware child did not start')
        os.kill(parent.pid, signal.SIGKILL); parent.wait(timeout=5)
        old, = self.destination.glob('attempt-*')
        self.assertTrue((old / 'resource-receipt.json').is_file())
        recovered = self.run_trial(command)
        self.assertEqual(recovered['status'], 'pass')
        self.assertNotEqual(recovered['attempt'], old.name)
        metadata = json.loads((old / 'attempt.json').read_text())
        self.assertEqual(metadata['state'], 'interrupted')
        self.assertIn('resource-receipt.json', metadata['partial_artifacts'])


if __name__ == '__main__':
    unittest.main()
