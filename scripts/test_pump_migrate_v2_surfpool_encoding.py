#!/usr/bin/env python3
"""Regression check for locale-independent IDL loading in the migrate-v2 surfpool script.

Sibling of #2689 (migrate), #2684 (holder-distribution), #2680 (exact-quote), #2678 (fee-sweep),
#2674 (creator-collect), #2669 (volume validator) and merged #2654 (offline
differentials): evidence/upstream/pump.json contains non-ASCII bytes (the
U+2192 arrow in a doc string), so the ``layouts()`` helper's bare
``read_text()`` decoded the IDL with the host locale. On a POSIX-locale host
without UTF-8 mode that is ASCII, and the load raised UnicodeDecodeError,
while UTF-8 hosts ran fine. Pinning ``encoding='utf-8'`` makes the load
host-independent.

The test executes the script's own ``layouts`` function (extracted by AST)
rather than importing the module, because the module's import chain pulls
in solders and differential fixtures, which are not needed to exercise
this load.
"""

import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_migrate_v2_surfpool.py"

DRIVER = r"""
import ast, json, sys
from pathlib import Path
source = Path(sys.argv[1]).read_text(encoding="utf-8")
tree = ast.parse(source)
layouts = None
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "layouts":
        layouts = node
assert layouts is not None, "no layouts function found"
code = compile(ast.Module(body=[layouts], type_ignores=[]), "layouts", "exec")
namespace = {"ROOT": Path(sys.argv[1]).resolve().parents[1], "json": json, "Path": Path}
exec(code, namespace)
offsets = namespace["layouts"]()
print(len(offsets))
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


class PumpMigrateV2SurfpoolEncodingTests(unittest.TestCase):
    def test_idl_loads_under_posix_locale(self):
        completed = run_hostile_locale()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(int(completed.stdout.strip()) > 0)


if __name__ == "__main__":
    unittest.main()
