#!/usr/bin/env python3
"""Roadmap packets must not adopt files left in an existing output directory."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReconstructionRoadmapPublicationTests(unittest.TestCase):
    def test_nonempty_output_is_rejected_without_modifying_retained_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            output.mkdir()
            retained = output / "foreign-retained.txt"
            retained.write_text("retained non-roadmap evidence\n", encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/reconstruction_roadmap.py"),
                 "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("output directory is not empty", completed.stderr)
            self.assertEqual(retained.read_text(encoding="utf-8"),
                             "retained non-roadmap evidence\n")
            self.assertEqual([path.name for path in output.iterdir()],
                             ["foreign-retained.txt"])


if __name__ == "__main__":
    unittest.main()
