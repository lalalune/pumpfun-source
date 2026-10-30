#!/usr/bin/env python3
"""Regression tests for text-layout evidence publication."""

from pathlib import Path
import tempfile
import unittest

import pump_text_layout


class MaintainedOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.default = (root / "scripts/pump_text_layout_default.ld").read_text()
        cls.ordered = (root / "programs/pump/link/ordered.ld").read_text()
        cls.first_selector = next(line for line in cls.ordered.splitlines()
                                  if line.startswith("    *"))

    def test_actual_maintained_order_is_admitted(self):
        # Includes object digest globs, the root-object .text* catch-all,
        # and the bare-* allocation-error selector in the maintained recipe.
        self.assertEqual(pump_text_layout.check_script(self.default, self.ordered), 555)

    def test_only_text_input_selectors_are_admitted(self):
        for statement in ('    *(.data*)', '    *(.rodata*)',
                          '    *(.text.other*)', '    INCLUDE other.ld',
                          '    symbol = 1;', '    *evil.o(".text;BYTE(0)")'):
            with self.subTest(statement=statement), self.assertRaisesRegex(
                    AssertionError, "unexpected linker statement"):
                pump_text_layout.check_script(
                    self.default, self.ordered.replace(self.first_selector, statement, 1))

    def test_default_scaffold_and_selector_uniqueness_are_preserved(self):
        for changed in (self.ordered.replace("SIZEOF_HEADERS", "SIZEOF_HEADERS + 8", 1),
                        self.ordered.replace("    *(.text*)\n  } :text", "  } :text", 1)):
            with self.subTest(changed=changed[:60]), self.assertRaisesRegex(
                    AssertionError, "wrap the default .text rule"):
                pump_text_layout.check_script(self.default, changed)
        duplicate = self.ordered.replace(self.first_selector,
                                         self.first_selector + "\n" + self.first_selector, 1)
        with self.assertRaisesRegex(AssertionError, "duplicate selector"):
            pump_text_layout.check_script(self.default, duplicate)


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
