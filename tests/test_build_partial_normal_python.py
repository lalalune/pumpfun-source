"""Optimized Python must not remove partial-build input stability checks."""

import ast
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_partial_candidate.py"


class BuildPartialNormalPythonTests(unittest.TestCase):
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

    def test_optimized_modes_exit_before_build_imports(self):
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
                with tempfile.TemporaryDirectory() as temporary:
                    output = Path(temporary) / "output-must-not-be-created"
                    result = subprocess.run(
                        [sys.executable, *flags, str(SCRIPT),
                         "--manifest", str(Path(temporary) / "absent" / "Cargo.toml"),
                         "--program", "pump", "--artifact-name", "pump.so",
                         "--output", str(output)],
                        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30,
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("Normal Python is required", result.stderr)
                    self.assertNotIn("ModuleNotFoundError", result.stderr)
                    self.assertFalse(output.exists(), "optimized invocation must not begin a build")

    def test_normal_python_reaches_argument_parser(self):
        environment = dict(os.environ)
        environment.pop("PYTHONOPTIMIZE", None)
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--help"],
                                cwd=ROOT, env=environment, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
