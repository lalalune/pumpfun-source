#!/usr/bin/env python3
"""Ensure Pump Surfpool differential runners reject optimized Python."""

import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
RUNNERS = (
    "pump_buy_v2_surfpool.py",
    "pump_cashback_surfpool.py",
    "pump_create_control_surfpool.py",
    "pump_create_nested_surfpool.py",
    "pump_create_quote_surfpool.py",
    "pump_create_surfpool.py",
    "pump_create_v2_surfpool.py",
    "pump_exact_quote_surfpool.py",
    "pump_global_init_surfpool.py",
    "pump_holder_distribution_surfpool.py",
    "pump_idl_authority_surfpool.py",
    "pump_legacy_buy_surfpool.py",
    "pump_migrate_surfpool.py",
    "pump_migrate_v2_surfpool.py",
    "pump_v3_configured_fee_surfpool.py",
    "pump_v3_token_extensions_surfpool.py",
)
ERROR = "Normal Python is required"

# The module docstring names each runner's instruction family. A stale
# copy-pasted docstring once mislabelled several runners (and, for the two
# that pass ``description=__doc__`` to argparse, their ``--help`` text); pin a
# keyword that must appear so that regression does not return unnoticed.
SUBJECT_KEYWORDS = {
    "pump_cashback_surfpool.py": "claim_cashback",
    "pump_exact_quote_surfpool.py": "exact-quote",
    "pump_holder_distribution_surfpool.py": "holder-distribution",
    "pump_legacy_buy_surfpool.py": "legacy buy",
    "pump_migrate_surfpool.py": "migrate",
    "pump_v3_configured_fee_surfpool.py": "configured creator-fee",
}


def run(script, *arguments, environment=None):
    return subprocess.run(
        [sys.executable, *arguments, str(SCRIPTS / script), "--help"],
        cwd=SCRIPTS.parent,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class PumpSurfpoolOptimizedModeTests(unittest.TestCase):
    def test_optimized_python_is_rejected(self):
        for script in RUNNERS:
            for flag in ("-O", "-OO"):
                with self.subTest(script=script, flag=flag):
                    completed = run(script, flag)
                    self.assertEqual(completed.returncode, 1)
                    self.assertIn(ERROR, completed.stderr)
                    self.assertNotIn("usage:", completed.stdout)

    def test_pythonoptimize_environment_is_rejected(self):
        environment = dict(os.environ, PYTHONOPTIMIZE="1")
        for script in RUNNERS:
            with self.subTest(script=script):
                completed = run(script, environment=environment)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(ERROR, completed.stderr)

    def test_normal_python_reaches_each_argument_parser(self):
        for script in RUNNERS:
            with self.subTest(script=script):
                completed = run(script)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("usage:", completed.stdout)

    def test_module_docstring_names_its_instruction_family(self):
        import ast

        for script, keyword in SUBJECT_KEYWORDS.items():
            with self.subTest(script=script):
                source = (SCRIPTS / script).read_text(encoding="utf-8")
                docstring = ast.get_docstring(ast.parse(source)) or ""
                self.assertIn(keyword, docstring)


if __name__ == "__main__":
    unittest.main()
