#!/usr/bin/env python3
"""Regression check for locale-independent IDL loading in the admin token
incentives verifier.

Sibling of merged #2654 and the surfpool UTF-8 fixes, which pin UTF-8 for
the upstream Pump IDL reads in the offline differentials: the differential
itself loads this same IDL with ``encoding='utf-8'``
(pump_admin_token_incentives_differential.py), but its verifier re-read the
same file through a bare ``diff.IDL.read_text()``. evidence/upstream/pump.json
contains non-ASCII bytes (the U+2192 arrow in a doc string), so on a
POSIX-locale host without UTF-8 mode the verifier's load raised
UnicodeDecodeError before it could check any event discriminator, while
UTF-8 hosts ran fine. Pinning ``encoding='utf-8'`` makes the verifier's
load host-independent, matching the differential.

The verifier cannot be executed on a host without solders (it imports the
differential module), so this test checks the load call statically and
demonstrates the locale failure on the real IDL file directly.
"""

import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
VERIFY_SCRIPT = "pump_admin_token_incentives_verify.py"
IDL = SCRIPTS.parent / "evidence" / "upstream" / "pump.json"


def idl_load_calls():
    tree = ast.parse((SCRIPTS / VERIFY_SCRIPT).read_text(encoding="utf-8"))
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "read_text":
            continue
        target = func.value
        if (
            isinstance(target, ast.Attribute)
            and target.attr == "IDL"
            and isinstance(target.value, ast.Name)
            and target.value.id == "diff"
        ):
            calls.append(node)
    return calls


def run_hostile_locale(snippet):
    environment = dict(os.environ)
    environment.update({
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONUTF8": "0",
        "PYTHONCOERCECLOCALE": "0",
    })
    return subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=SCRIPTS.parent,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class AdminTokenIncentivesVerifyEncodingTests(unittest.TestCase):
    def test_idl_load_pins_utf8(self):
        calls = idl_load_calls()
        self.assertEqual(len(calls), 1, "expected exactly one diff.IDL read_text call")
        encodings = [
            keyword.value.value
            for keyword in calls[0].keywords
            if keyword.arg == "encoding"
            and isinstance(keyword.value, ast.Constant)
        ]
        self.assertEqual(encodings, ["utf-8"])

    def test_bare_load_fails_and_pinned_load_succeeds_under_posix_locale(self):
        bare = run_hostile_locale(
            "import pathlib; pathlib.Path('evidence/upstream/pump.json').read_text()"
        )
        self.assertNotEqual(bare.returncode, 0)
        self.assertIn("UnicodeDecodeError", bare.stderr)
        pinned = run_hostile_locale(
            "import pathlib, json; "
            "json.loads(pathlib.Path('evidence/upstream/pump.json')"
            ".read_text(encoding='utf-8'))"
        )
        self.assertEqual(pinned.returncode, 0, pinned.stderr)


if __name__ == "__main__":
    unittest.main()
