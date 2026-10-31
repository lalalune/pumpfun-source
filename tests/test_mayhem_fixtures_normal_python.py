"""Optimized Python must not strip Mayhem trade fixture signature verification."""

import ast
import json
from pathlib import Path
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = tuple(
    ROOT / "scripts" / f"mayhem_{name}_fixture.py"
    for name in ("buy", "buy_v2", "sell", "sell_v2", "pump_swap")
)

try:
    import solders  # noqa: F401
except ModuleNotFoundError:
    solders = None


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


class MayhemFixturesNormalPythonTests(unittest.TestCase):
    def test_guards_precede_imports_and_no_bare_asserts_remain(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                tree = parse(script)
                self.assertIsNotNone(ast.get_docstring(tree))
                guard = next(
                    (
                        node
                        for node in tree.body
                        if isinstance(node, ast.If)
                        and isinstance(node.test, ast.UnaryOp)
                        and isinstance(node.test.op, ast.Not)
                        and isinstance(node.test.operand, ast.Name)
                        and node.test.operand.id == "__debug__"
                    ),
                    None,
                )
                self.assertIsNotNone(guard, f"{script.name} lacks top-level __debug__ guard")
                first_import = next(
                    node.lineno
                    for node in tree.body
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                )
                self.assertLess(guard.lineno, first_import)
                bare_asserts = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
                self.assertEqual(bare_asserts, [], f"{script.name} still contains bare asserts at lines {bare_asserts}")

    def test_optimized_modes_reject_direct_execution_and_import_before_dependencies(self):
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
                    mode="direct",
                    flags=flags,
                    optimize=env.get("PYTHONOPTIMIZE"),
                ):
                    result = subprocess.run(
                        [sys.executable, *flags, str(script)],
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Normal Python is required", result.stderr)
                    self.assertNotIn("ModuleNotFoundError", result.stderr)
                with self.subTest(
                    script=script.name,
                    mode="import",
                    flags=flags,
                    optimize=env.get("PYTHONOPTIMIZE"),
                ):
                    result = subprocess.run(
                        [
                            sys.executable,
                            *flags,
                            "-c",
                            "import importlib,sys;sys.path.insert(0,sys.argv[1]);importlib.import_module(sys.argv[2])",
                            str(script.parent),
                            script.stem,
                        ],
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Normal Python is required", result.stderr)
                    self.assertNotIn("ModuleNotFoundError", result.stderr)

    @unittest.skipIf(solders is None, "solders/LiteSVM required for live fixture transaction tests")
    def test_normal_import_and_runtime_signature_verification_fail_closed(self):
        environment = dict(os.environ)
        environment.pop("PYTHONOPTIMIZE", None)
        driver = r"""
import importlib, json, sys
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
rows = []
for name in ('mayhem_buy_fixture', 'mayhem_buy_v2_fixture', 'mayhem_sell_fixture', 'mayhem_sell_v2_fixture', 'mayhem_pump_swap_fixture'):
    module = importlib.import_module(name)
    report = module.run({})
    assert report['signature_verified'] is True
    real_tx_cls = module.Transaction if hasattr(module, 'Transaction') else module.f.Transaction

    class UnverifiedTx:
        def __init__(self, real_tx):
            self._real = real_tx
        def verify_with_results(self):
            return [False]
        def __getattr__(self, attr):
            return getattr(self._real, attr)

    class TxFactoryProxy:
        @staticmethod
        def new_signed_with_payer(*args, **kwargs):
            return UnverifiedTx(real_tx_cls.new_signed_with_payer(*args, **kwargs))
        def __getattr__(self, attr):
            return getattr(real_tx_cls, attr)

    if hasattr(module, 'Transaction'):
        ctx = patch.object(module, 'Transaction', TxFactoryProxy())
    else:
        real_f = module.f
        class FixtureNamespaceProxy:
            Transaction = TxFactoryProxy()
            def __getattr__(self, attr):
                return getattr(real_f, attr)
        ctx = patch.object(module, 'f', FixtureNamespaceProxy())

    raised_runtime_error = False
    with ctx:
        try:
            module.run({})
        except RuntimeError:
            raised_runtime_error = True
    assert raised_runtime_error, name
    rows.append({'fixture': name, 'verified': True, 'rejected_unverified': True})
print(json.dumps(rows))
"""
        result = subprocess.run(
            [sys.executable, "-B", "-c", driver, str(ROOT / "scripts")],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=90,
        )
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        rows = json.loads(result.stdout)
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["verified"] and row["rejected_unverified"] for row in rows))


if __name__ == "__main__":
    unittest.main()
