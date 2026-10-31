"""The legacy cashback report must refuse the shared trade fixture's inputs.

pump_legacy_buy_differential.run() executes the shared trade fixture, but this
wrapper admitted only PumpReport's default inputs, so the fixture JSON and the
capture.json metadata could be replaced by the report.
"""

import importlib
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class ReachedCases(Exception):
    """Admission passed; stop before any case or report write."""


class LegacyCashbackReportInputsTests(unittest.TestCase):
    def test_fixture_inputs_are_refused_before_cases_run(self):
        tool = importlib.import_module("pump_legacy_cashback_differential")
        candidate = ROOT / "evidence/original/pump/deployed.so"
        for path in tool.h.REPORT_INPUTS:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                argv = ["tool", "--candidate", str(candidate), "--output", str(path)]
                with mock.patch.object(sys, "argv", argv), \
                        mock.patch.object(tool, "cases", side_effect=ReachedCases):
                    try:
                        tool.main()
                    except ValueError as error:
                        self.assertIn("aliases an input", str(error))
                    except ReachedCases:
                        self.fail("report destination admitted a fixture input")


if __name__ == "__main__":
    unittest.main()
