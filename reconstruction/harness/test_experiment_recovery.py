"""Durable recovery checks for interrupted and unpublished experiments."""
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


H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

import experiment_runner as E


RUNNER = r"""
import json
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
from experiment_runner import run_trial
run_trial(Path(sys.argv[2]), json.loads(sys.argv[4]), Path(sys.argv[3]), timeout=60)
"""

INTERRUPTIBLE = r'''
import os
from pathlib import Path
import sys
import time
marker, output = Path(sys.argv[1]), Path(sys.argv[2])
if marker.exists():
    (output / 'complete').write_text('resumed\n', encoding='ascii')
    print('resumed', flush=True)
else:
    marker.write_text(str(os.getpid()), encoding='ascii')
    (output / 'partial').write_text('retained\n', encoding='ascii')
    print('partial-log', flush=True)
    time.sleep(30)
'''


class ExperimentRecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'value').write_text('source\n', encoding='ascii')
        self.destination = self.root / 'results'
        self.pass_command = [sys.executable, '-c',
                             'from pathlib import Path; import sys; '
                             'Path(sys.argv[1], "result").write_text("pass\\n")', '{out}']

    def attempt_metadata(self, attempt):
        return json.loads((attempt / 'attempt.json').read_text(encoding='utf-8'))

    def make_stale_attempt(self, command=None, *, corrupt=False):
        command = command or self.pass_command
        admission = E.identity(self.source, command, [], 300, environment=os.environ)
        key = E.digest(json.dumps(admission, sort_keys=True).encode())
        self.destination.mkdir(parents=True, exist_ok=True)
        attempt = self.destination / 'attempt-stale'
        attempt.mkdir()
        (attempt / 'output').mkdir()
        (attempt / 'output/partial').write_text('partial\n', encoding='ascii')
        (attempt / 'stdout.log').write_text('started\n', encoding='ascii')
        (attempt / 'stderr.log').write_bytes(b'')
        metadata = {'schema': E.ATTEMPT_SCHEMA, 'attempt': attempt.name,
                    'state': 'staging', 'created_ns': time.time_ns(),
                    'key': key, 'inputs': admission}
        (attempt / 'attempt.json').write_text(
            '{not-json' if corrupt else json.dumps(metadata), encoding='utf-8')
        return attempt

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX signals')
    @patch.dict(os.environ, {'XPC_SERVICE_NAME': '0'})
    def test_sigkill_recovery_retains_partial_attempt_and_retries(self):
        # macOS normalizes this launcher variable on Python startup. Keep the
        # private first-run and resumed fixtures on the same environment identity.
        marker = self.root / 'first.pid'
        command = [sys.executable, '-c', INTERRUPTIBLE, str(marker), '{out}']
        runner = subprocess.Popen(
            [sys.executable, '-I', '-B', '-c', RUNNER, str(H), str(self.source),
             str(self.destination), json.dumps(command)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        self.addCleanup(runner.kill)
        self.addCleanup(runner.stderr.close)
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(marker.exists(), 'first trial did not start')
        os.kill(runner.pid, signal.SIGKILL)
        runner.wait(timeout=5)

        old_attempt, = self.destination.glob('attempt-*')
        partial_hash = hashlib.sha256((old_attempt / 'output/partial').read_bytes()).hexdigest()
        result = E.run_trial(self.source, command, self.destination, timeout=60)
        self.assertEqual(result['status'], 'pass')
        self.assertNotEqual(result['attempt'], old_attempt.name)
        self.assertEqual(result['recovered_attempts'], [
            {'attempt': old_attempt.name, 'state': 'interrupted',
             'retry_identity_matches': True},
        ])
        old = self.attempt_metadata(old_attempt)
        self.assertEqual(old['state'], 'interrupted')
        self.assertEqual(old['partial_artifacts']['output/partial']['sha256'], partial_hash)
        self.assertEqual((old_attempt / 'stdout.log').read_text(encoding='ascii'), 'partial-log\n')
        self.assertEqual((self.destination / result['attempt'] / 'output/complete').read_text(),
                         'resumed\n')

    def test_completed_attempt_is_republished_without_rerun(self):
        first = E.run_trial(self.source, self.pass_command, self.destination)
        attempt_path = self.destination / first['attempt'] / 'attempt.json'
        metadata = json.loads(attempt_path.read_text())
        metadata['state'] = 'completed'
        metadata.pop('published_ns')
        E.atomic_json(attempt_path, metadata)
        (self.destination / 'latest.json').unlink()
        second = E.run_trial(self.source, self.pass_command, self.destination)
        self.assertTrue(second['reused'])
        self.assertTrue(second['recovered'])
        self.assertEqual(second['attempt'], first['attempt'])
        self.assertEqual(len(list(self.destination.glob('attempt-*'))), 1)
        self.assertEqual(json.loads((self.destination / 'latest.json').read_text())['attempt'],
                         first['attempt'])

    def test_published_latest_closes_a_stranded_completed_state(self):
        first = E.run_trial(self.source, self.pass_command, self.destination)
        attempt_path = self.destination / first['attempt'] / 'attempt.json'
        metadata = json.loads(attempt_path.read_text())
        metadata['state'] = 'completed'
        metadata.pop('published_ns')
        E.atomic_json(attempt_path, metadata)
        second = E.run_trial(self.source, self.pass_command, self.destination)
        self.assertTrue(second['reused'])
        self.assertNotIn('recovered', second)
        self.assertEqual(json.loads(attempt_path.read_text())['state'], 'published')

    def test_corrupt_receipts_are_preserved_but_never_accepted(self):
        stale = self.make_stale_attempt(corrupt=True)
        self.destination.joinpath('latest.json').write_bytes(b'{invalid-latest')
        result = E.run_trial(self.source, self.pass_command, self.destination)
        self.assertEqual(result['status'], 'pass')
        self.assertFalse(result['reused'])
        self.assertEqual(result['recovered_attempts'][0]['state'], 'invalid')
        self.assertEqual((stale / 'attempt.json').read_text(encoding='utf-8'), '{not-json')
        history = self.destination / 'receipt-history' / result['receipt_history'][0]
        self.assertEqual(history.read_bytes(), b'{invalid-latest')

    def test_concurrent_callers_recover_stale_attempt_once(self):
        stale = self.make_stale_attempt()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                lambda _: E.run_trial(self.source, self.pass_command, self.destination), range(2)))
        fresh = {value['attempt'] for value in results}
        self.assertEqual(len(fresh), 1)
        self.assertNotIn(stale.name, fresh)
        self.assertEqual(sum(not value['reused'] for value in results), 1)
        self.assertEqual(self.attempt_metadata(stale)['state'], 'interrupted')
        self.assertEqual(len(list(self.destination.glob('attempt-*'))), 2)

    def test_stale_identity_mismatch_is_explicit_and_history_is_retained(self):
        stale = self.make_stale_attempt()
        (self.source / 'value').write_text('changed\n', encoding='ascii')
        result = E.run_trial(self.source, self.pass_command, self.destination)
        self.assertFalse(result['reused'])
        self.assertEqual(result['recovered_attempts'], [
            {'attempt': stale.name, 'state': 'interrupted',
             'retry_identity_matches': False},
        ])
        self.assertEqual((stale / 'output/partial').read_text(), 'partial\n')

    def test_previous_published_attempt_remains_byte_identical(self):
        first = E.run_trial(self.source, self.pass_command, self.destination)
        old = self.destination / first['attempt']
        before = {path.relative_to(old).as_posix(): path.read_bytes()
                  for path in old.rglob('*') if path.is_file()}
        (self.source / 'value').write_text('different source\n', encoding='ascii')
        second = E.run_trial(self.source, self.pass_command, self.destination)
        self.assertNotEqual(second['attempt'], first['attempt'])
        after = {path.relative_to(old).as_posix(): path.read_bytes()
                 for path in old.rglob('*') if path.is_file()}
        self.assertEqual(after, before)

    def test_running_receipt_failure_still_cleans_started_process(self):
        real_atomic = E.atomic_json
        real_start = E.SupervisedProcess.start
        processes = []
        def remember_start(*args, **kwargs):
            process = real_start(*args, **kwargs)
            processes.append(process)
            return process
        def fail_running(path, value):
            if value.get('state') == 'running':
                raise OSError('controlled running receipt failure')
            return real_atomic(path, value)
        with patch.object(E.SupervisedProcess, 'start', side_effect=remember_start), \
             patch.object(E, 'atomic_json', side_effect=fail_running):
            with self.assertRaisesRegex(OSError, 'controlled running receipt failure'):
                E.run_trial(self.source, [sys.executable, '-c', 'import time;time.sleep(20)'],
                            self.destination)
        self.assertEqual(len(processes), 1)
        process = processes[0]
        self.addCleanup(process.terminate)
        self.assertIsNotNone(process.guardian.poll())
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                os.kill(process.trial_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(.01)
        else:
            self.fail('trial survived a running receipt persistence failure')
        attempt, = self.destination.glob('attempt-*')
        self.assertEqual(self.attempt_metadata(attempt)['state'], 'interrupted')
        self.assertFalse((self.destination / 'latest.json').exists())

    def test_recovery_does_not_signal_a_group_named_by_stale_metadata(self):
        stale = self.make_stale_attempt()
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(20)'],
                                     start_new_session=True)
        self.addCleanup(unrelated.wait)
        self.addCleanup(unrelated.kill)
        metadata = self.attempt_metadata(stale)
        metadata.update(state='running', guardian_pid=unrelated.pid,
                        process_group=unrelated.pid, trial_pid=unrelated.pid)
        E.atomic_json(stale / 'attempt.json', metadata)
        before = (stale / 'attempt.json').read_bytes()
        with patch.object(E, 'RECOVERY_PROCESS_WAIT', .1), \
             patch.object(E.SupervisedProcess, 'start') as start:
            with self.assertRaisesRegex(ValueError, 'still active'):
                E.run_trial(self.source, self.pass_command, self.destination)
        start.assert_not_called()
        self.assertIsNone(unrelated.poll())
        self.assertEqual((stale / 'attempt.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
