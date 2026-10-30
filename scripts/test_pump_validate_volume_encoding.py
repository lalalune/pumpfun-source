#!/usr/bin/env python3
"""Regression check for locale-independent IDL loading in the volume validator.

Sibling of open #2654, which pins UTF-8 for the upstream Pump IDL reads in
the offline differentials: evidence/upstream/pump.json contains non-ASCII
bytes (the U+2192 arrow in a doc string), so this validator's bare
``json.load(open(...))`` decoded the IDL with the host locale. On a
POSIX-locale host without UTF-8 mode that is ASCII, and the module-level
load raised UnicodeDecodeError before argument parsing, while UTF-8 hosts
ran fine. Pinning ``encoding='utf-8'`` makes the load host-independent.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_validate_volume.py"


def run_hostile_locale():
    environment = dict(os.environ)
    environment.update({
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONUTF8": "0",
        "PYTHONCOERCECLOCALE": "0",
    })
    return subprocess.run(
        [sys.executable, str(SCRIPTS / SCRIPT), "--help"],
        cwd=SCRIPTS.parent,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class PumpValidateVolumeEncodingTests(unittest.TestCase):
    def test_idl_loads_under_posix_locale(self):
        completed = run_hostile_locale()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
