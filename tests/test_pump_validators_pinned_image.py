"""Direct Pump validator CLIs must use one candidate image per run."""

import ast
import atexit
import os
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = tuple(
    ROOT / "scripts" / f"pump_validate_{name}.py"
    for name in ("admin", "authority", "buy", "config_admin", "quote", "sell", "volume")
)


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


class PumpValidatorPinnedImageTests(unittest.TestCase):
    def test_every_validator_pins_before_its_first_case_loop(self):
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

                pin_lines = []
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Assign):
                        continue
                    if not any(
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "a"
                        and target.attr == "candidate"
                        for target in node.targets
                    ):
                        continue
                    if any(
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id == "pin_program"
                        for child in ast.walk(node.value)
                    ):
                        pin_lines.append(node.lineno)

                self.assertTrue(pin_lines, "candidate path is not pinned")
                pin_line = min(pin_lines)
                following_loops = [
                    node.lineno
                    for node in ast.walk(tree)
                    if isinstance(node, ast.For) and node.lineno > pin_line
                ]
                self.assertTrue(following_loops, "case loop after pinning was not found")
                self.assertLess(pin_line, min(following_loops))

    def test_pin_snapshot_keeps_the_first_bytes(self):
        helper = ROOT / "scripts" / "pump_amm_reusable_harness.py"
        tree = parse(helper)
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "pin_program"
        )
        namespace = {
            "_pinned": {},
            "atexit": atexit,
            "os": os,
            "Path": Path,
            "shutil": shutil,
            "tempfile": tempfile,
        }
        module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
        exec(compile(module, str(helper), "exec"), namespace)

        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate.so"
            candidate.write_bytes(b"admitted image")
            snapshot = namespace["pin_program"](candidate)
            candidate.write_bytes(b"replacement image")
            self.assertEqual(namespace["pin_program"](candidate), snapshot)
            self.assertEqual(snapshot.read_bytes(), b"admitted image")


if __name__ == "__main__":
    unittest.main()
