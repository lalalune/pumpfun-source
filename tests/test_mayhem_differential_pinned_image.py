"""Mayhem differentials must execute one candidate image per run."""

import ast
import base64
import contextlib
import hashlib
import importlib.util
import io
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
SCRIPTS = tuple(
    ROOT / "scripts" / f"mayhem_{name}_differential.py"
    for name in ("buy", "buy_v2", "sell", "sell_v2", "pump_swap", "initialize_state")
)


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def pin_assignment_lines(main):
    lines = []
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
            lines.append(node.lineno)
    return lines


class MayhemTradePinnedImageTests(unittest.TestCase):
    def test_every_trade_cli_pins_before_cases_run(self):
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

                main = next(
                    node
                    for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main"
                )
                pin_lines = pin_assignment_lines(main)
                case_loops = []
                for node in ast.walk(main):
                    if not isinstance(node, ast.For):
                        continue
                    if any(
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id == "cases"
                        for child in ast.walk(node.iter)
                    ):
                        case_loops.append(node.lineno)
                self.assertTrue(pin_lines, "candidate path is not pinned")
                self.assertTrue(case_loops, "cases loop was not found")
                self.assertLess(min(pin_lines), min(case_loops))

    def test_candidate_replacement_cannot_change_later_cases(self):
        work = ROOT / "work"
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as temporary:
            root = Path(temporary)
            original = root / "evidence/original/mayhem/deployed.so"
            candidate = root / "candidate.so"
            replacement = root / "replacement.so"
            output = root / "report.json"
            cases = root / "cases.json"
            script = root / "scripts/mayhem_buy_differential.py"
            original.parent.mkdir(parents=True)
            original.write_bytes(b"original image")
            script.parent.mkdir(parents=True)
            shutil.copyfile(SCRIPTS[0], script)
            candidate.write_bytes(b"admitted image")
            replacement.write_bytes(b"replacement image")
            cases.write_text(json.dumps({"cases": [{"name": "first"}, {"name": "second"}]}))
            for relative in (
                "scripts/mayhem_buy_fixture.py",
                "scripts/pump_trade_fixture.py",
                "research/imported-lab/analysis/pump_fun/"
                "curve-fresh-trades-v3-signed-surfpool.json",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n")

            pinned = {}

            def pin(path):
                key = os.path.abspath(os.fspath(path))
                if key not in pinned:
                    snapshot = root / f"pinned-{len(pinned)}.so"
                    shutil.copyfile(key, snapshot)
                    pinned[key] = snapshot
                return pinned[key]

            candidate_images = []

            class FakeTransaction:
                @classmethod
                def from_bytes(cls, data):
                    return cls()

                signatures = ["signed"]

                def verify_with_results(self):
                    return [True]

            fixture = types.ModuleType("mayhem_buy_fixture")
            fixture.ROOT = root
            fixture.MAY = "mayhem"
            fixture.sha = lambda data: hashlib.sha256(data).hexdigest()
            fixture.f = types.SimpleNamespace(REPORT_INPUTS=(
                root / "scripts/pump_trade_fixture.py",
                root / "research/imported-lab/analysis/pump_fun/"
                "curve-fresh-trades-v3-signed-surfpool.json",
            ))

            def run(case, binary=None):
                data = Path(binary or original).read_bytes()
                if binary is not None:
                    candidate_images.append(data)
                    if len(candidate_images) == 1:
                        candidate.write_bytes(replacement.read_bytes())
                return {
                    "transaction_base64": base64.b64encode(b"tx").decode(),
                    "before": {},
                    "after": {},
                    "error": None,
                    "metadata": {
                        "inner_instructions": [],
                        "return_data": None,
                        "logs": [],
                    },
                }

            fixture.run = run
            solders = types.ModuleType("solders")
            solders.__path__ = []
            transaction = types.ModuleType("solders.transaction")
            transaction.Transaction = FakeTransaction
            solders.transaction = transaction
            helper = types.ModuleType("pump_amm_reusable_harness")
            helper.pin_program = pin

            # The script's real report publisher and input-binding helpers.
            helpers = {}
            for name in ("pump_differential_output", "pump_diagnostic_audit"):
                helper_spec = importlib.util.spec_from_file_location(
                    name, ROOT / "scripts" / f"{name}.py"
                )
                helpers[name] = importlib.util.module_from_spec(helper_spec)
                helper_spec.loader.exec_module(helpers[name])

            modules = {
                **helpers,
                "mayhem_buy_fixture": fixture,
                "pump_amm_reusable_harness": helper,
                "solders": solders,
                "solders.transaction": transaction,
            }
            with patch.dict(sys.modules, modules):
                spec = importlib.util.spec_from_file_location(
                    "mayhem_buy_differential", script
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            argv = [
                str(script),
                "--candidate",
                str(candidate),
                "--output",
                str(output),
                "--cases",
                str(cases),
            ]
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    module.main()
            self.assertFalse(raised.exception.code)

            report = json.loads(output.read_text())
            admitted = hashlib.sha256(b"admitted image").hexdigest()
            self.assertEqual(report["candidate_sha256"], admitted)
            self.assertEqual(candidate_images, [b"admitted image", b"admitted image"])
            self.assertEqual(candidate.read_bytes(), b"replacement image")

            # fb6ab38a also made the CLI treat a transaction as signed only
            # when it really carries a signature: an unsigned one must abort
            # the run before any report is published.
            class UnsignedTransaction(FakeTransaction):
                signatures = []

            unsigned_output = root / "unsigned-report.json"
            argv[argv.index("--output") + 1] = str(unsigned_output)
            with patch.object(module, "Transaction", UnsignedTransaction):
                with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(AssertionError):
                        module.main()
            self.assertFalse(unsigned_output.exists())


if __name__ == "__main__":
    unittest.main()
