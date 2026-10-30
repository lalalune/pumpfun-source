"""Real subprocess controls for the shared serial-suite timeout adapter."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import serial_suite_process as runner


class SerialSuiteProcessTests(unittest.TestCase):
    def test_normal_output_and_failure_exit_are_retained_on_both_backends(self):
        for groups in (False, True) if os.name == 'posix' else (False,):
            with self.subTest(groups=groups), mock.patch.object(runner, 'USE_PROCESS_GROUPS', groups):
                result, expired = runner.run_suite_process([sys.executable, '-c',
                    'import sys;print("retained output");sys.exit(7)'], timeout=10)
                self.assertFalse(expired)
                self.assertEqual(result.returncode, 7)
                if groups:self.assertEqual(result.stdout.strip(), 'retained output')
                else:self.assertIsNone(result.stdout)

    def test_single_process_fallback_timeout_returns_promptly(self):
        started = time.monotonic()
        with mock.patch.object(runner, 'USE_PROCESS_GROUPS', False):
            result, expired = runner.run_suite_process([sys.executable, '-u', '-c',
                'import time;print("started",flush=True);time.sleep(30)'], timeout=0.3)
        self.assertTrue(expired)
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual(result.stdout, '')

    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group guarantee')
    def test_timeout_kills_the_actual_child_process_group(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / 'survivor'
            code = ('import subprocess,sys,time;print("started",flush=True);'
                    'subprocess.Popen([sys.executable,"-c",'
                    f'"import time,pathlib;time.sleep(0.8);pathlib.Path({str(marker)!r}).write_text(\'survived\')"]);'
                    'time.sleep(30)')
            result, expired = runner.run_suite_process([sys.executable, '-u', '-c', code], timeout=0.3)
            self.assertTrue(expired);self.assertIn('started', result.stdout)
            time.sleep(1)
            self.assertFalse(marker.exists())


if __name__ == '__main__':unittest.main()
