"""Optimized Python must not remove Pump probe signature checks."""

import ast
import json
from pathlib import Path
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = tuple(
    ROOT / "scripts" / name
    for name in (
        "pump_holder_distribution_probe.py",
        "pump_migrate_probe.py",
        "pump_migrate_v2_probe.py",
        "pump_set_mayhem_params_synthetic_cpi.py",
    )
)


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


class PumpProbeNormalPythonTests(unittest.TestCase):
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
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("Normal Python is required", result.stderr)
                    self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_normal_imports_and_synthetic_cpi_argument_parser(self):
        environment = dict(os.environ)
        environment.pop("PYTHONOPTIMIZE", None)
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                result = subprocess.run(
                    [sys.executable, "-B", "-c",
                     "import importlib,sys;sys.path.insert(0,sys.argv[1]);importlib.import_module(sys.argv[2]);print('import-ok')",
                     str(script.parent), script.stem],
                    cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "import-ok")
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS[-1]), "--help"],
                                cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)

    def test_normal_probes_run_signed_vm_controls_and_detect_wrong_image(self):
        environment = dict(os.environ)
        environment.pop("PYTHONOPTIMIZE", None)
        driver = r"""
import base64, importlib, json, sys
from pathlib import Path
from solders.transaction import Transaction
sys.path.insert(0, sys.argv[1])
wrong = Path(sys.argv[1]).parent / 'evidence/original/pump_fees/deployed.so'
rows = []
for name in ('pump_holder_distribution_probe', 'pump_migrate_probe', 'pump_migrate_v2_probe'):
    module = importlib.import_module(name)
    original = module.run({})
    candidate = module.run({}, candidate=wrong)
    for result in (original, candidate):
        assert result['signature_verification'] is True
        tx = Transaction.from_bytes(base64.b64decode(result['transaction_base64']))
        assert tx.signatures and all(tx.verify_with_results())
    assert original['error'] != candidate['error'], name
    rows.append({'probe': name, 'signatures_verified': True, 'wrong_image_detected': True})
print(json.dumps(rows))
"""
        result = subprocess.run([sys.executable, "-B", "-c", driver, str(ROOT / "scripts")],
                                cwd=ROOT, env=environment, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        rows = json.loads(result.stdout)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row['signatures_verified'] and row['wrong_image_detected'] for row in rows))


if __name__ == "__main__":
    unittest.main()
