"""Reject coordinate reports that alias the candidate ELF."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parents[1]
ORIGINAL = REPO / "evidence/original/pump/deployed.so"


class CoordsReportDestinationTests(unittest.TestCase):
    def run_alias(self, alias_kind):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.so"
            shutil.copyfile(ORIGINAL, candidate)
            before = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if alias_kind == "same":
                output = candidate
            elif alias_kind == "symlink":
                output = root / "report.json"
                try:
                    os.symlink(candidate, output)
                except (OSError, NotImplementedError, AttributeError) as error:
                    self.skipTest(f"creating links is not permitted: {error}")
            else:
                output = root / "report.json"
                os.link(candidate, output)
            result = subprocess.run(
                [sys.executable, "-B", str(HARNESS / "coords.py"),
                 "unmatched", "--cand", str(candidate), "--json", str(output)],
                cwd=REPO, capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("report destination aliases an input", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(), before)

    def test_report_destination_cannot_alias_candidate(self):
        for alias_kind in ("same", "symlink", "hardlink"):
            with self.subTest(alias_kind=alias_kind):
                self.run_alias(alias_kind)


if __name__ == "__main__":
    unittest.main()
