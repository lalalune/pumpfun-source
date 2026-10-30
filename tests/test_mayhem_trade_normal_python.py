"""Optimized Python must not remove Mayhem trade signature verification."""

import ast
from pathlib import Path
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = tuple(
    ROOT / "scripts" / f"mayhem_{name}_differential.py"
    for name in ("buy", "buy_v2", "sell", "sell_v2", "pump_swap")
)


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


class MayhemTradeNormalPythonTests(unittest.TestCase):
    def test_guards_precede_imports(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                tree = parse(script)
                guard = next(
                    node
                    for node in tree.body
                    if isinstance(node, ast.If)
                    and isinstance(node.test, ast.UnaryOp)
                    and isinstance(node.test.op, ast.Not)
                    and isinstance(node.test.operand, ast.Name)
                    and node.test.operand.id == "__debug__"
                )
                first_import = next(
                    node.lineno
                    for node in tree.body
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                )
                self.assertLess(guard.lineno, first_import)

    def test_optimized_modes_exit_before_program_imports(self):
        environment = dict(os.environ)
        environment.pop("PYTHONOPTIMIZE", None)
        optimized_environment = dict(environment)
        optimized_environment["PYTHONOPTIMIZE"] = "1"
        invocations = (
            (("-O",), environment),
            (("-OO",), environment),
            ((), optimized_environment),
        )
        for script in SCRIPTS:
            for flags, env in invocations:
                with self.subTest(
                    script=script.name,
                    flags=flags,
                    optimize=env.get("PYTHONOPTIMIZE"),
                ):
                    result = subprocess.run(
                        [sys.executable, *flags, str(script), "--help"],
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Normal Python is required", result.stderr)
                    self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_normal_python_still_reaches_argument_parsers(self):
        environment = dict(os.environ)
        environment.pop("PYTHONOPTIMIZE", None)
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                result = subprocess.run(
                    [sys.executable, "-B", str(script), "--help"],
                    cwd=ROOT, env=environment, capture_output=True,
                    text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
