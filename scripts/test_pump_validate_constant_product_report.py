#!/usr/bin/env python3
"""Regression checks for report-publication input protection in the
constant-product validator.

Sibling of merged #2951 (admin, buy, sell, quote, authority validators):
scripts/pump_validate_constant_product.py was the one remaining validate
script that published its report with a bare ``write_text`` instead of the
maintained ``PumpReport`` publisher, so a ``--output`` that aliased an input
--- the host binary, the recovered ``constant_product.rs`` source, or a
captured original/dependency image --- truncated that input with the report
bytes (reproduced: ``--output`` equal to the host path replaced the host
executable with JSON, and the run then failed on the mismatches assert).
The fix admits the output through ``PumpReport`` before any case runs, so
an alias is rejected with ``report output aliases an input`` and every
input keeps its bytes; a fresh output still publishes the same report
bytes. The stub host answers 0 to every case line, so the fresh-output
run records mismatches (as on base) without ever touching the host.
"""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_validate_constant_product.py"
HOST_STUB = "#!/bin/sh\nwhile IFS= read -r line; do echo 0; done\n"


def make_host(directory):
    host = Path(directory) / "host.sh"
    host.write_text(HOST_STUB)
    host.chmod(0o755)
    return host


def invoke(host, output):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / SCRIPT), "--host", str(host), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


@unittest.skipUnless(importlib.util.find_spec("solders"), "requires the documented solders runtime")
class PumpValidateConstantProductReportTests(unittest.TestCase):
    def test_host_aliases_are_rejected_before_writes(self):
        for kind in ["direct", "symlink", "hardlink"]:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                host = make_host(root)
                before = host.read_bytes()
                output = host
                if kind == "symlink":
                    output = root / "report.json"
                    output.symlink_to(host)
                if kind == "hardlink":
                    output = root / "report.json"
                    os.link(host, output)
                result = invoke(host, output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("aliases", result.stderr)
                self.assertEqual(host.read_bytes(), before)

    def test_original_and_source_input_aliases_are_rejected(self):
        for relative in ["evidence/original/pump/deployed.so",
                         "programs/pump/recovered/constant_product.rs"]:
            # The alias must hardlink the protected repo file itself, so
            # the staging directory has to share its filesystem.
            with self.subTest(input=relative), tempfile.TemporaryDirectory(dir=ROOT) as temp:
                root = Path(temp)
                host = make_host(root)
                protected = ROOT / relative
                before = protected.read_bytes()
                output = root / "report.json"
                os.link(protected, output)
                result = invoke(host, output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("aliases", result.stderr)
                self.assertEqual(protected.read_bytes(), before)

    def test_fresh_output_still_publishes_and_preserves_the_host(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            host = make_host(root)
            before = host.read_bytes()
            output = root / "nested" / "report.json"
            result = invoke(host, output)
            # The stub host answers 0 to every case, so mismatches are
            # recorded and the final assert fails, exactly as on base ---
            # but only after the report is published through PumpReport.
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("aliases", result.stderr)
            self.assertEqual(host.read_bytes(), before)
            report = json.loads(output.read_text())
            self.assertGreater(report["case_count"], 0)
            self.assertNotEqual(report["mismatches"], [])


if __name__ == "__main__":
    unittest.main()
