"""A new run must not replace a retained stateful report."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location('relay_stateful_output', HERE / 'producer.py')
relay = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = relay
SPEC.loader.exec_module(relay)

CANDIDATE = ROOT / 'evidence/dependencies/donation_relay/deployed.so'


class OutputRefusalTests(unittest.TestCase):
    def run_over(self, output):
        with mock.patch.object(relay, 'run_case', side_effect=RuntimeError('cases started')):
            try:
                with self.assertRaisesRegex(SystemExit, 'refusing to overwrite'):
                    relay.execute(ROOT, CANDIDATE, output)
            except RuntimeError as error:
                self.fail(f'{error}: an occupied output was accepted')

    def test_existing_report_is_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'report.json'
            output.write_bytes(b'retained report\n')
            self.run_over(output)
            self.assertEqual(output.read_bytes(), b'retained report\n')

    def test_dangling_output_link_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'report.json'
            target = Path(temporary) / 'elsewhere.json'
            os.symlink(target, output)
            self.run_over(output)
            self.assertFalse(target.exists())

    def test_absent_output_starts_the_cases(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(relay, 'run_case', side_effect=RuntimeError('cases started')):
                with self.assertRaisesRegex(RuntimeError, 'cases started'):
                    relay.execute(ROOT, CANDIDATE, Path(temporary) / 'report.json')


if __name__ == '__main__':
    unittest.main()
