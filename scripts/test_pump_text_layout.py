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

    def test_call_graph_ordering_file_is_not_an_unbound_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            order = Path(temporary) / "call-graph-order.txt"
            order.write_text("caller\ncallee\n", encoding="utf-8")
            arguments = (
                ["--call-graph-ordering-file", str(order)],
                [f"--call-graph-ordering-file={order}"],
            )

            for argv in arguments:
                with self.subTest(argv=argv), self.assertRaisesRegex(
                    AssertionError, "call-graph ordering file is not admitted"
                ):
                    pump_text_layout.declared_inputs(argv)


if __name__ == "__main__":
    unittest.main()
