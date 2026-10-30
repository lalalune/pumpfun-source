"""Optimized Python must not remove Mayhem-create signature verification."""

import ast
from pathlib import Path
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pump_create_mayhem_differential.py"


class CreateMayhemNormalPythonTests(unittest.TestCase):
    def test_guard_precedes_imports(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"), filename=str(SCRIPT))
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
        for flags, env in invocations:
            with self.subTest(flags=flags, optimize=env.get("PYTHONOPTIMIZE")):
                result = subprocess.run(
                    [sys.executable, *flags, str(SCRIPT), "--help"],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Normal Python is required", result.stderr)
                self.assertNotIn("ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
