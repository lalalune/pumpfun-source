"""Bounded compiler monitor tests using tiny processes."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_process import run_compiler


class CompilerMonitorTests(unittest.TestCase):
    def test_monitor_stops_owned_group_and_retains_output(self):
        calls = 0
        def monitor():
            nonlocal calls
            calls += 1
            return None if calls == 1 else {'classification': 'resource_budget_exceeded'}
        result, timed_out = run_compiler(
            [sys.executable, '-u', '-c', 'import time;print("started",flush=True);time.sleep(30)'],
            timeout=10, monitor=monitor, monitor_interval=.02,
        )
        self.assertFalse(timed_out)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'started\n')
        self.assertEqual(result.monitor_result['classification'], 'resource_budget_exceeded')

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX process groups')
    def test_monitor_never_signals_unrelated_process(self):
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'],
                                     start_new_session=True)
        self.addCleanup(unrelated.wait)
        self.addCleanup(lambda: unrelated.poll() is None and unrelated.kill())
        result, _ = run_compiler(
            [sys.executable, '-c', 'import time;time.sleep(30)'],
            monitor=lambda: 'stop-owned', monitor_interval=.01,
        )
        self.assertEqual(result.monitor_result, 'stop-owned')
        self.assertIsNone(unrelated.poll())

    def test_monitor_cadence_does_not_become_timeout(self):
        result, timed_out = run_compiler(
            [sys.executable, '-c', 'print("complete")'], timeout=5,
            monitor=lambda: None, monitor_interval=.001,
        )
        self.assertFalse(timed_out)
        self.assertEqual(result.returncode, 0)
        self.assertIsNone(result.monitor_result)

    def test_overall_timeout_remains_distinct(self):
        result, timed_out = run_compiler(
            [sys.executable, '-c', 'import time;time.sleep(30)'], timeout=.05,
            monitor=lambda: None, monitor_interval=.005,
        )
        self.assertTrue(timed_out)
        self.assertIsNone(result.monitor_result)

    def test_invalid_monitor_configuration_precedes_launch(self):
        for monitor, interval in ((1, 1), (lambda: None, 0), (lambda: None, float('inf'))):
            with self.subTest(monitor=monitor, interval=interval), self.assertRaises(ValueError):
                run_compiler([sys.executable, '-c', 'pass'], monitor=monitor,
                             monitor_interval=interval)


if __name__ == '__main__':
    unittest.main()
