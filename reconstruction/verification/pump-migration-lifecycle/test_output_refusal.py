#!/usr/bin/env python3
"""Actual lifecycle CLI admission and fresh-output controls.

The captured Pump image is a diagnostic candidate for the positive control;
this test does not certify a reconstructed image or late-writer atomicity.
"""

import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
SCRIPT = PACKAGE / "lifecycle.py"


class OutputRefusalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="lifecycle-output-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.missing_candidate = self.directory / "missing-candidate.so"

    def invoke(self, output, *, candidate=None, optimize=()):
        env = dict(os.environ)
        env.pop("PYTHONOPTIMIZE", None)
        return subprocess.run(
            [sys.executable, *optimize, "-B", str(SCRIPT), "--candidate",
             str(candidate or self.missing_candidate), "--output", str(output)],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=120,
        )

    def assert_refused(self, output, *, optimize=()):
        result = self.invoke(output, optimize=optimize)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("refusing to overwrite existing report", result.stderr)
        self.assertNotIn("FileNotFoundError", result.stderr)

    def test_existing_file_directory_and_links_are_refused_before_candidate_access(self):
        retained = self.directory / "retained.json.gz"
        retained.write_bytes(b"retained report\n")
        directory = self.directory / "existing-directory"
        directory.mkdir()
        symlink = self.directory / "linked-report"
        symlink.symlink_to(retained)
        hardlink = self.directory / "hardlinked-report"
        os.link(retained, hardlink)
        target = self.directory / "missing-target"
        dangling = self.directory / "dangling-report"
        dangling.symlink_to(target)
        for output in (retained, directory, symlink, hardlink, dangling):
            with self.subTest(output=output.name):
                self.assert_refused(output)
                self.assertEqual(retained.read_bytes(), b"retained report\n")
                self.assertFalse(target.exists())
        self.assertTrue(directory.is_dir())
        self.assertTrue(symlink.is_symlink())
        self.assertTrue(dangling.is_symlink())

    def test_existing_report_is_refused_under_optimized_python(self):
        output = self.directory / "retained.json"
        output.write_bytes(b"retained report\n")
        for optimize in (("-O",), ("-OO",)):
            with self.subTest(optimize=optimize):
                self.assert_refused(output, optimize=optimize)
                self.assertEqual(output.read_bytes(), b"retained report\n")

    def test_fresh_output_reaches_real_candidate_loading(self):
        output = self.directory / "nested" / "report.json.gz"
        result = self.invoke(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FileNotFoundError", result.stderr)
        self.assertIn("missing-candidate.so", result.stderr)
        self.assertNotIn("refusing to overwrite", result.stderr)
        self.assertFalse(output.exists())
        self.assertFalse(output.parent.exists())

    def test_fresh_output_runs_complete_real_lifecycle(self):
        output = self.directory / "nested" / "report.json.gz"
        result = self.invoke(output, candidate=ROOT / "evidence/original/pump/deployed.so")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(gzip.decompress(output.read_bytes()))
        self.assertEqual(report["case_count"], 27)
        self.assertEqual(len(report["cases"]), 27)
        self.assertEqual(report["transaction_count_per_image"], 41)
        for field in ("mismatch_cases", "oracle_mismatch_cases", "invariant_failure_cases",
                      "rollback_failure_cases", "infrastructure_failure_cases"):
            self.assertEqual(report[field], [], field)
        self.assertEqual(report["negative_controls"], {"after": True, "error": True})


if __name__ == "__main__":
    unittest.main()
