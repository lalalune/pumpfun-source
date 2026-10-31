#!/usr/bin/env python3
"""Layer 3 totals in the generated summary and README of a real capture."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import deep_section_analysis  # noqa: E402


class SectionDataReferenceTotalTests(unittest.TestCase):
    def test_summary_and_readme_total_both_data_sections(self):
        with tempfile.TemporaryDirectory(prefix="section-data-refs-") as temporary:
            packet = Path(temporary)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(deep_section_analysis.build_packet("mayhem", packet, packet), 0)
            layer = json.loads((packet / "layer3-cross-section.json").read_text(encoding="utf-8"))
            summary = json.loads((packet / "summary.json").read_text(encoding="utf-8"))
            readme = (packet / "README.md").read_text(encoding="utf-8")
        self.assertGreater(layer["total_rodata_refs"], 0)
        self.assertGreater(layer["total_data_refs"], 0)
        self.assertEqual(summary["layer3_cross_section"].get("total_data_rel_ro_refs"),
                         layer["total_data_refs"])
        total = layer["total_rodata_refs"] + layer["total_data_refs"]
        self.assertIn(f"- Total data references: {total}\n", readme)


if __name__ == "__main__":
    unittest.main()
