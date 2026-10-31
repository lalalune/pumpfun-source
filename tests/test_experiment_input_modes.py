"""Real helper executions must not reuse a result after execute permissions change."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

HARNESS = Path(__file__).resolve().parents[1] / 'reconstruction' / 'harness'
sys.path.insert(0, str(HARNESS))
if os.name == 'posix':
    import fcntl
    import experiment_runner as runner

INVOKE_HELPER = '''import subprocess, sys
try:
    result = subprocess.run([sys.argv[1]]).returncode
except OSError:
    result = 2
raise SystemExit(result)
'''


@unittest.skipUnless(os.name == 'posix', 'requires POSIX executable permissions')
class DeclaredInputModeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='experiment-input-mode-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'value').write_bytes(b'unchanged source\n')
        self.helper = self.root / 'helper.sh'
        self.helper.write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
        self.helper.chmod(0o755)
        self.command = [sys.executable, '-c', INVOKE_HELPER, str(self.helper)]
        self.out = self.root / 'trials'

    def trial(self):
        return runner.run_trial(self.source, self.command, self.out,
                                inputs=[self.helper], timeout=10)

    def matrix(self, output):
        matrix = self.root / 'matrix.json'
        matrix.write_text(json.dumps([{'name': 'helper', 'source': str(self.source),
                                      'command': self.command, 'inputs': [str(self.helper)],
                                      'timeout': 10}]), encoding='utf-8')
        process = subprocess.run([sys.executable, '-B', str(HARNESS / 'experiment_runner.py'),
                                  str(matrix), '--out', str(output)],
                                 capture_output=True, text=True, timeout=20)
        self.assertTrue(process.stdout, process.stderr)
        return process.returncode, json.loads(process.stdout)['helper']

    def test_matrix_retries_changed_execute_bits_and_preserves_previous_attempt(self):
        for predicate in (0, 1):
            for mode in (0o644, 0o655):
                with self.subTest(predicate=predicate, mode=oct(mode)):
                    if mode == 0o655 and os.geteuid() == 0:
                        self.skipTest('root can execute using remaining group/other bits')
                    self.helper.chmod(0o755)
                    self.helper.write_text(f'#!/bin/sh\nexit {predicate}\n', encoding='utf-8')
                    unchanged_bytes = self.helper.read_bytes()
                    output = self.root / f'trial-{predicate}-{mode}'
                    code, first = self.matrix(output)
                    self.assertEqual((code, first['status']), (0, 'pass' if predicate == 0 else 'fail'))
                    attempt = output / 'helper' / first['attempt']
                    retained = {str(p.relative_to(attempt)): p.read_bytes()
                                for p in attempt.rglob('*') if p.is_file()}
                    self.assertTrue(self.matrix(output)[1]['reused'])
                    self.helper.chmod(mode)
                    self.assertEqual(self.helper.read_bytes(), unchanged_bytes)
                    code, resumed = self.matrix(output)
                    fresh_code, fresh = self.matrix(self.root / f'fresh-{predicate}-{mode}')
                    self.assertEqual((fresh_code, fresh['status']), (2, 'error'))
                    self.assertEqual((code, resumed['status'], resumed['reused']), (2, 'error', False))
                    self.assertNotEqual(resumed['key'], first['key'])
                    self.assertNotEqual(resumed['attempt'], first['attempt'])
                    self.assertEqual(resumed['inputs']['input_execute_bits'][str(self.helper)], mode & 0o111)
                    self.assertEqual(resumed['inputs']['inputs'][str(self.helper)],
                                     hashlib.sha256(unchanged_bytes).hexdigest())
                    self.assertEqual({str(p.relative_to(attempt)): p.read_bytes()
                                      for p in attempt.rglob('*') if p.is_file()}, retained)

    def test_write_permission_change_keeps_valid_reuse(self):
        first = self.trial()
        self.helper.chmod(0o555)
        resumed = self.trial()
        self.assertEqual((resumed['status'], resumed['reused']), ('pass', True))
        self.assertEqual(resumed['attempt'], first['attempt'])
        self.assertEqual(resumed['key'], first['key'])

    def test_changed_mode_before_launch_is_rejected_without_running_command(self):
        real_copy = runner.shutil.copytree
        def change_after_copy(*args, **kwargs):
            copied = real_copy(*args, **kwargs)
            self.helper.chmod(0o644)
            return copied
        with patch.object(runner.shutil, 'copytree', change_after_copy):
            result = self.trial()
        self.assertEqual(result['status'], 'error')
        self.assertIsNone(result['returncode'], 'command launched after a declared input changed')
        self.assertIn(b'declared input changed before launch',
                      (self.out / result['attempt'] / 'stderr.log').read_bytes())

    def test_helper_mode_change_during_execution_rejects_success(self):
        self.helper.write_text('#!/bin/sh\nchmod 644 "$0"\nexit 0\n', encoding='utf-8')
        before = self.helper.read_bytes()
        result = self.trial()
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['reason'], 'source or declared input changed during execution')
        self.assertEqual(self.helper.read_bytes(), before)

    def test_mode_changes_while_waiting_refresh_the_admitted_input(self):
        first = self.trial()
        entered = threading.Event()
        answers, errors = [], []
        real_identity = runner.identity
        def identity(*args, **kwargs):
            admitted = real_identity(*args, **kwargs)
            entered.set()
            return admitted
        def run():
            try:
                answers.append(self.trial())
            except BaseException as error:
                errors.append(error)
        with (self.out / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            with patch.object(runner, 'identity', identity):
                thread = threading.Thread(target=run)
                thread.start()
                try:
                    self.assertTrue(entered.wait(5))
                    self.helper.chmod(0o644)
                finally:
                    fcntl.flock(lock, fcntl.LOCK_UN)
                    thread.join(15)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        result = answers[0]
        self.assertEqual((result['status'], result['returncode'], result['reused']), ('error', 2, False))
        self.assertIsNone(result['reason'], 'mode should refresh with bytes after the lock wait')
        self.assertNotEqual(result['key'], first['key'])
        self.assertEqual(result['inputs']['input_execute_bits'][str(self.helper)], 0)


if __name__ == '__main__':
    unittest.main()
