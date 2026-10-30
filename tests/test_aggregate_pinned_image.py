"""Long aggregate runners must pass one stable candidate image to every suite."""

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    ROOT / "scripts/pump_validate_all.py",
    ROOT / "scripts/pump_validate_parallel.py",
    ROOT / "scripts/fees_validate_all.py",
)


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def pin_lines(tree):
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == "pin_program"
            for child in ast.walk(node.value)
        ):
            lines.append(node.lineno)
    return lines


def subprocess_lines(tree):
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]


class AggregatePinnedImageTests(unittest.TestCase):
    def test_every_aggregate_pins_before_launching_suites(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                tree = parse(script)
                imported = any(
                    isinstance(node, ast.ImportFrom)
                    and node.module == "pump_amm_reusable_harness"
                    and any(alias.name == "pin_program" for alias in node.names)
                    for node in tree.body
                )
                self.assertTrue(imported, "pin_program is not imported")

                pins = pin_lines(tree)
                launches = subprocess_lines(tree)
                self.assertTrue(pins, "candidate is not pinned")
                self.assertTrue(launches, "subprocess suite launch was not found")
                self.assertLess(min(pins), min(launches))

    def test_suite_commands_do_not_reuse_the_live_cli_argument(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                tree = parse(script)
                violations = []
                for node in ast.walk(tree):
                    if not (
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "subprocess"
                        and node.func.attr == "run"
                    ):
                        continue
                    for child in ast.walk(node):
                        if (
                            isinstance(child, ast.Attribute)
                            and child.attr == "candidate"
                            and isinstance(child.value, ast.Name)
                            and child.value.id in {"a", "args"}
                        ):
                            violations.append(child.lineno)
                self.assertEqual(
                    violations,
                    [],
                    "a suite launch reads the live candidate argument",
                )


if __name__ == "__main__":
    unittest.main()
