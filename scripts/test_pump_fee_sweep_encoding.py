#!/usr/bin/env python3
"""Regression check for locale-independent IDL loading in the fee-sweep differential.

Sibling of #2674 (creator-collect) and #2669 (volume validator) and open
#2654 (offline differentials): evidence/upstream/pump.json contains
non-ASCII bytes (the U+2192 arrow in a doc string), so this script's bare
``json.load(open(...))`` decoded the IDL with the host locale. On a
POSIX-locale host without UTF-8 mode that is ASCII, and the load raised
UnicodeDecodeError, while UTF-8 hosts ran fine. Pinning
``encoding='utf-8'`` makes the load host-independent.

The test executes the script's own PIDL assignment statement (extracted by
AST) rather than importing the module, because the module's import chain
pulls in pump_validate_admin, whose own IDL read is already covered by
open #2654 and would fail first under a hostile locale.
"""

import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_fee_sweep_differential.py"

DRIVER = r"""
import ast, json, sys
from pathlib import Path
source = Path(sys.argv[1]).read_text(encoding="utf-8")
tree = ast.parse(source)
pidl = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "PIDL":
                pidl = node
assert pidl is not None, "no PIDL assignment found"
code = compile(ast.Module(body=[pidl], type_ignores=[]), "pidl", "exec")
namespace = {"ROOT": Path(sys.argv[1]).resolve().parents[1], "json": json, "Path": Path}
exec(code, namespace)
print(namespace["PIDL"]["address"])
"""


def run_hostile_locale():
    environment = dict(os.environ)
    environment.update({
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONUTF8": "0",
        "PYTHONCOERCECLOCALE": "0",
    })
    return subprocess.run(
        [sys.executable, "-c", DRIVER, str(SCRIPTS / SCRIPT)],
        cwd=SCRIPTS.parent,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class PumpFeeSweepEncodingTests(unittest.TestCase):
    def test_idl_loads_under_posix_locale(self):
        completed = run_hostile_locale()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P", completed.stdout)


if __name__ == "__main__":
    unittest.main()
