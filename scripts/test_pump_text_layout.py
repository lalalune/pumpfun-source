#!/usr/bin/env python3
"""Regression tests for text-layout evidence publication."""

from pathlib import Path
import tempfile
import unittest

import pump_text_layout


class ConfigureTests(unittest.TestCase):
    def test_failed_sdk_admission_does_not_publish_layout(self):
        default = (Path(__file__).resolve().parent / "pump_text_layout_default.ld").read_text()
        ordered = default.replace(
            "  .text : { *(.text*) } :text",
            '  .text : {\n    *fixture.o(".text.fixture")\n    *(.text*)\n  } :text',
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            order = root / "order.ld"
            order.write_text(ordered)
            output = root / "output"
            output.mkdir()
            with self.assertRaises(FileNotFoundError):
                pump_text_layout.configure(
                    order, output, root / "missing-sdk", "fixture", Path("/bin/true")
                )
            self.assertEqual(list(output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
