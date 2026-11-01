"""Bounded process-level checks for the experiment trial supervisor."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch


H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

from process_supervisor import (SupervisedProcess, SupervisionError,
                                _signal_owned_group, _terminate_owned_group)


@unittest.skipUnless(os.name == 'posix', 'requires POSIX process groups')
class ProcessSupervisorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def start(self, script, *arguments):
        stdout = (self.root / 'stdout.log').open('ab')
        stderr = (self.root / 'stderr.log').open('ab')
        self.addCleanup(stdout.close)
        self.addCleanup(stderr.close)
        process = SupervisedProcess.start(
            [sys.executable, '-c', script, *map(str, arguments)],
            executable=sys.executable, cwd=self.root, stdout=stdout, stderr=stderr,
            env=os.environ,
        )
        self.addCleanup(process.terminate)
        return process

    def process_exists(self, pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def wait_for_dead(self, pid, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not self.process_exists(pid):
                return True
            time.sleep(.02)
        return not self.process_exists(pid)

    def test_preserves_child_exit_codes_and_output(self):
        for code in (0, 1, 7):
            with self.subTest(code=code):
                process = self.start('import sys; print("trial-output"); raise SystemExit(int(sys.argv[1]))',
                                     code)
                self.assertEqual(process.wait(timeout=5), code)
                process.terminate()
        self.assertEqual((self.root / 'stdout.log').read_text().splitlines(),
                         ['trial-output'] * 3)

    def test_process_start_failure_is_bounded(self):
        stdout = (self.root / 'start-stdout.log').open('wb')
        stderr = (self.root / 'start-stderr.log').open('wb')
        self.addCleanup(stdout.close); self.addCleanup(stderr.close)
        started = time.monotonic()
        with self.assertRaises(OSError):
            SupervisedProcess.start(
                ['/definitely/missing/experiment-command'],
                executable='/definitely/missing/experiment-command', cwd=self.root,
                stdout=stdout, stderr=stderr, env=os.environ,
            )
        self.assertLess(time.monotonic() - started, 5)

    def test_timeout_stops_trial_and_same_group_grandchild(self):
        marker = self.root / 'pids'
        script = r'''
import os
from pathlib import Path
import subprocess
import sys
import time
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
Path(sys.argv[1]).write_text(f'{os.getpid()} {child.pid}', encoding='ascii')
time.sleep(30)
'''
        process = self.start(script, marker)
        deadline = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(marker.exists(), 'trial did not create its child marker')
        trial, grandchild = map(int, marker.read_text(encoding='ascii').split())
        with self.assertRaises(subprocess.TimeoutExpired):
            process.wait(timeout=.05)
        process.terminate()
        self.assertTrue(self.wait_for_dead(trial), 'trial survived timeout cleanup')
        self.assertTrue(self.wait_for_dead(grandchild), 'grandchild survived timeout cleanup')

    def test_normal_exit_stops_ordinary_grandchildren(self):
        for code in (0, 1, 7):
            with self.subTest(code=code):
                marker = self.root / f'grandchild-{code}'
                child = ('import os,time; from pathlib import Path; '
                         f'Path({str(marker)!r}).write_text(str(os.getpid())); time.sleep(20)')
                leader = ('import subprocess,sys,time; from pathlib import Path; '
                          f'subprocess.Popen([sys.executable,"-c",{child!r}]); '
                          f'p=Path({str(marker)!r}); deadline=time.monotonic()+5\n'
                          'while not p.exists() and time.monotonic()<deadline: time.sleep(.01)\n'
                          f'raise SystemExit({code})')
                process = self.start(leader)
                self.assertEqual(process.wait(timeout=6), code)
                grandchild = int(marker.read_text())
                process.terminate()
                self.assertTrue(self.wait_for_dead(grandchild), 'ordinary grandchild survived normal completion')

    def test_stopped_guardian_fallback_kills_term_ignoring_group(self):
        marker = self.root / 'stopped-guardian-pids'
        script = r'''
import os,signal,subprocess,sys,time
from pathlib import Path
signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([sys.executable, '-c', 'import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(20)'])
Path(sys.argv[1]).write_text(f'{os.getpid()} {child.pid}')
time.sleep(20)
'''
        process = self.start(script, marker)
        deadline = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertTrue(marker.exists())
        trial, grandchild = map(int, marker.read_text().split())
        self.assertEqual(os.getpgid(process.guardian.pid), process.guardian.pid)
        os.kill(process.guardian.pid, signal.SIGSTOP)
        started = time.monotonic()
        process.terminate()
        self.assertLess(time.monotonic() - started, 3)
        self.assertTrue(self.wait_for_dead(trial))
        self.assertTrue(self.wait_for_dead(grandchild))

    def test_ownership_mismatch_does_not_signal_unrelated_group(self):
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
                                     start_new_session=True)
        self.addCleanup(unrelated.wait)
        self.addCleanup(unrelated.kill)
        with self.assertRaisesRegex(SupervisionError, 'without ownership'):
            _terminate_owned_group(unrelated, unrelated.pid + 100000, None)
        self.assertIsNone(unrelated.poll())

    def test_signal_helper_never_uses_dead_owner_to_signal_another_group(self):
        dead_owner = subprocess.Popen([sys.executable, '-c', 'pass'], start_new_session=True)
        dead_owner.wait(timeout=5)
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(20)'],
                                     start_new_session=True)
        self.addCleanup(unrelated.wait)
        self.addCleanup(unrelated.kill)
        with self.assertRaisesRegex(SupervisionError, 'without ownership'):
            _signal_owned_group(dead_owner, unrelated.pid, unrelated.pid, signal.SIGKILL)
        self.assertIsNone(unrelated.poll())

    def test_post_exit_permission_error_is_not_a_false_cleanup_failure(self):
        guardian = Mock(pid=1234)
        guardian.poll.return_value = 0
        with patch('process_supervisor.os.killpg', side_effect=PermissionError(1, 'denied')):
            with patch('process_supervisor.os.getpgid', side_effect=ProcessLookupError):
                self.assertFalse(_signal_owned_group(guardian, 1234, 1235, signal.SIGKILL))

    def test_permission_error_with_live_owner_fails_closed(self):
        guardian = Mock(pid=1234)
        guardian.poll.return_value = None
        with patch('process_supervisor.os.killpg', side_effect=PermissionError(1, 'denied')):
            with patch('process_supervisor.os.getpgid', return_value=1234):
                with self.assertRaisesRegex(SupervisionError, 'permission denied'):
                    _signal_owned_group(guardian, 1234, 1235, signal.SIGKILL)


if __name__ == '__main__':
    unittest.main()
