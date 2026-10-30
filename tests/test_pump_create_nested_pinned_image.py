"""The nested-create differential must use one program image per run.

The CLI runs the original and candidate once per case. A live candidate path
would be read again for every case, while the receipt records only the bytes
present at the end of the run. The source imports solders and cannot be run in
the lightweight tooling environment, so this test checks the pinning
data-flow directly.
"""

import ast
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
DIFFERENTIAL = ROOT / "scripts" / "pump_create_nested_differential.py"
FIXTURE = ROOT / "scripts" / "pump_create_nested_fixture.py"


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def imported_pin_program(tree):
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "pump_amm_reusable_harness"
        and any(alias.name == "pin_program" for alias in node.names)
        for node in tree.body
    )


class PumpCreateNestedPinnedImageTests(unittest.TestCase):
    def test_candidate_is_pinned_before_cases_run(self):
        tree = parse(DIFFERENTIAL)
        self.assertTrue(imported_pin_program(tree), "pin_program is not imported")

        main = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        pin_lines = []
        for node in ast.walk(main):
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

        case_loops = [
            node.lineno
            for node in ast.walk(main)
            if isinstance(node, ast.For)
            and isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "cases"
        ]
        self.assertTrue(pin_lines, "the candidate path is not pinned")
        self.assertTrue(case_loops, "the cases loop was not found")
        self.assertLess(
            min(pin_lines),
            min(case_loops),
            "the candidate path is pinned after cases start running",
        )

    def test_fixture_pins_the_program_before_loading_it(self):
        tree = parse(FIXTURE)
        self.assertTrue(imported_pin_program(tree), "fixture does not import pin_program")

        pinned_binary_load = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_program_from_file"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Call)
            and isinstance(node.args[1].func, ast.Name)
            and node.args[1].func.id == "pin_program"
            and len(node.args[1].args) == 1
            and isinstance(node.args[1].args[0], ast.Name)
            and node.args[1].args[0].id == "binary"
            for node in ast.walk(tree)
        )
        self.assertTrue(
            pinned_binary_load,
            "the selected program is loaded from the live binary path",
        )

    def test_candidate_swap_cannot_mix_program_images(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "original.so"
            candidate = root / "candidate.so"
            replacement = root / "replacement.so"
            output = root / "report.json.gz"
            original.write_bytes(b"admitted image")
            candidate.write_bytes(b"admitted image")
            replacement.write_bytes(b"replacement image")

            snapshots = {}

            def pin(path):
                key = os.path.abspath(os.fspath(path))
                if key not in snapshots:
                    snapshot = root / f"pinned-{len(snapshots)}.so"
                    shutil.copyfile(key, snapshot)
                    snapshots[key] = snapshot
                return snapshots[key]

            helper = types.ModuleType("pump_amm_reusable_harness")
            helper.pin_program = pin
            # The differential imports its scripts/ siblings by plain name.
            with patch.dict(sys.modules, {"pump_amm_reusable_harness": helper}), \
                    patch.object(sys, "path", [str(DIFFERENTIAL.parent), *sys.path]):
                spec = importlib.util.spec_from_file_location(
                    "pump_create_nested_differential", DIFFERENTIAL
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            candidate_images = []

            class Harness:
                ORIGINAL = original

                def run(self, case, binary=original):
                    data = Path(pin(binary)).read_bytes()
                    if Path(binary) != original:
                        candidate_images.append(data)
                        if len(candidate_images) == 1:
                            candidate.write_bytes(replacement.read_bytes())
                    return {
                        "before": {},
                        "after": {},
                        "error": None,
                        "events": [],
                        "inner": [],
                        "return": None,
                    }

            module.load = lambda: Harness()
            module.prepare = lambda case: ({}, {"case": case})
            module.cases = lambda: [{"name": "first"}, {"name": "second"}]
            with patch.object(
                sys,
                "argv",
                [
                    str(DIFFERENTIAL),
                    "--candidate",
                    str(candidate),
                    "--output",
                    str(output),
                ],
            ):
                module.main()

            report = json.loads(gzip.decompress(output.read_bytes()))
            admitted = hashlib.sha256(b"admitted image").hexdigest()
            self.assertEqual(report["candidate_sha256"], admitted)
            self.assertEqual(
                candidate_images,
                [b"admitted image", b"admitted image"],
            )
            self.assertEqual(candidate.read_bytes(), b"replacement image")


if __name__ == "__main__":
    unittest.main()
