"""Actual host processes exercise the public Relay replay supervisor."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(os.name == 'posix', 'the native replay requires POSIX process groups')
class ReplayProcessCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe = load(ROOT / 'research/relay-replay-interruption-20261101/probe.py', 'relay_cleanup_probe')
        cls.replay = load(ROOT / cls.probe.RELATIVE, 'relay_cleanup_replay')
        cls.rows = {row['scenario']: row for row in cls.probe.run(ROOT)['scenarios']}

    def assert_stopped(self, scenario, returncode):
        row = self.rows[scenario]
        self.assertEqual(row['supervisor_returncode'], returncode)
        self.assertFalse(row['leader_ran_after_return'])
        self.assertFalse(row['grandchild_ran_after_return'])
        self.assertTrue(row['original_exception_retained'])
        self.assertTrue(row['process_record_retained'])
        self.assertTrue(row['existing_record_preserved'])
        self.assertTrue(row['log_retained'])

    def test_keyboard_interrupt_stops_child_and_grandchild(self):
        self.assert_stopped('interrupt', -2)

    def test_keyboard_interrupt_kills_term_ignoring_group(self):
        self.assert_stopped('interrupt-ignoring-term', -2)
        self.assertLess(self.rows['interrupt-ignoring-term']['stop_seconds'], 8)

    def test_keyboard_interrupt_kills_descendant_after_leader_exits(self):
        self.assert_stopped('interrupt-descendant-ignoring-term', -2)

    def test_failed_process_record_stops_spawned_command(self):
        self.assert_stopped('record-error', 1)

    def test_success_keeps_existing_result_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.replay.monitored([sys.executable, '-c', 'print("finished")'],
                                           Path(tmp), 'success', 5, 0)
            self.assertEqual(result['returncode'], 0)
            self.assertIsNone(result['guardFired'])
            self.assertFalse(result['groupRemained'])
            self.assertEqual((Path(tmp) / 'success.log').read_text(), 'finished\n')


if __name__ == '__main__':
    unittest.main()
