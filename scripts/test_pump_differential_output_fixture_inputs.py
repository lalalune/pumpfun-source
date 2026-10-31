#!/usr/bin/env python3
"""A shared fixture's data files must stay protected from every report writer."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from pump_differential_output import PumpReport


class FixtureInputs(unittest.TestCase):
    def report(self, root, output, module):
        script = root / 'tool.py'
        script.write_text('')
        with mock.patch.dict(sys.modules, {'shared_fixture': module}):
            return PumpReport(output, root, None, script)

    def test_loaded_fixture_inputs_are_refused_without_extra_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / 'fixture.json'
            data.write_text('{"tracked": true}\n')
            module = types.SimpleNamespace(REPORT_INPUTS=(data,))
            try:
                self.report(root, data, module)
            except ValueError as error:
                self.assertIn('aliases an input', str(error))
            else:
                self.fail('a loaded fixture input was admitted as the report output')
            self.assertEqual(data.read_text(), '{"tracked": true}\n')

    def test_hard_link_to_fixture_input_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / 'capture.json'
            data.write_text('{}\n')
            alias = root / 'report.json'
            alias.hardlink_to(data)
            module = types.SimpleNamespace(REPORT_INPUTS=(data,))
            with self.assertRaises(ValueError):
                self.report(root, alias, module)

    def test_unrelated_output_stays_admitted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / 'fixture.json'
            data.write_text('{}\n')
            module = types.SimpleNamespace(REPORT_INPUTS=(data,))
            output = root / 'out' / 'report.json'
            report = self.report(root, output, module)
            report.write(b'{}\n')
            self.assertEqual(output.read_bytes(), b'{}\n')

    @unittest.skipIf(importlib.util.find_spec('solders') is None, 'solders is required')
    def test_constant_product_admission_refuses_the_real_trade_fixture(self):
        # The same constructor call as pump_validate_constant_product.py, which
        # names none of these files. Only admission runs, so no case executes.
        import pump_trade_fixture as fixture
        host = ROOT / 'scripts/pump_validate_constant_product.py'
        for path in fixture.REPORT_INPUTS:
            with self.subTest(path=path.name):
                before = path.read_bytes()
                try:
                    PumpReport(path, fixture.R, host, host, extra_inputs=(
                        fixture.R / 'programs/pump/recovered/constant_product.rs',))
                except ValueError as error:
                    self.assertIn('aliases an input', str(error))
                else:
                    self.fail('the trade fixture input was admitted as a report output')
                self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
