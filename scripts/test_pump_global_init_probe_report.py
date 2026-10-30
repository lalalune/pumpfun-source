#!/usr/bin/env python3
"""The global-init probe must publish its report on a fresh checkout.

work/ is ignored by git, so its recovery directory does not exist after a
clone. The sibling probes reach write_json_report, which creates it; this one
ran both signed cases and then failed writing the result.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
REPORT = Path("work/pump-global-init-recovery/prerequisite.json")


class GlobalInitProbeReportTests(unittest.TestCase):
    def test_report_is_published_without_an_existing_work_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary)
            (checkout / "scripts").mkdir()
            for name in ("pump_global_init_probe.py", "probe_report.py"):
                shutil.copy(SCRIPTS / name, checkout / "scripts" / name)
            os.symlink(ROOT / "evidence", checkout / "evidence")

            completed = subprocess.run(
                [sys.executable, "-B", str(checkout / "scripts/pump_global_init_probe.py")],
                cwd=checkout,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((checkout / REPORT).read_text(encoding="utf-8"))
            self.assertEqual([case["seed"] for case in report["cases"]], [201, 202])
            self.assertEqual(
                [path.name for path in (checkout / REPORT).parent.iterdir()],
                [REPORT.name],
            )


if __name__ == "__main__":
    unittest.main()
