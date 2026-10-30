#!/usr/bin/env python3
"""The exact-body report must hash the window bytes it analyzed.

window_inventory_sha256 came from a second read at report time, so an inventory
replaced during the window walk bound the report to bytes it never parsed.
"""
import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import pump_exact_body_inventory as inventory  # noqa: E402


class ExactBodyInventorySnapshotTests(unittest.TestCase):
    def test_report_binds_the_parsed_inventory_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            windows = directory / "functions.tsv"
            shutil.copy(ROOT / inventory.CHECKED_IN_WINDOWS, windows)
            parsed = windows.read_bytes()
            output = directory / "report.json"
            real_body = inventory.function_body

            def body_then_replace_inventory(*args):
                windows.write_bytes(b"replaced during the walk\n")
                return real_body(*args)

            argv = ["pump_exact_body_inventory.py", "--candidate", str(inventory.ORIGINAL),
                    "--output", str(output), "--objdump", sys.executable]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(inventory, "window_inventory", return_value=windows), \
                    mock.patch.object(inventory, "candidate_functions", return_value=[]), \
                    mock.patch.object(inventory, "function_body", body_then_replace_inventory), \
                    contextlib.redirect_stdout(io.StringIO()):
                inventory.main()

            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["window_inventory_sha256"],
                             hashlib.sha256(parsed).hexdigest())
            self.assertEqual(report["original_windows"], 1035)


if __name__ == "__main__":
    unittest.main()
