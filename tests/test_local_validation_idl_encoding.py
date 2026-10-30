"""local_validation must read its IDL as UTF-8 on every host.

Sibling of merged #2188, which fixed the same locale-dependent read in
scripts/deep_disassembly.py and scripts/recover_dispatch.py but could not
reach this third IDL consumer: scripts/local_validation.py (run by the
evidence suite in .github/workflows/verify.yml) reads
evidence/upstream/<name>.json with the platform default encoding. The
checked-in pump IDL carries non-ASCII documentation bytes (U+2192 in the
buy instruction docs), so on an ASCII-locale host the default read raises
UnicodeDecodeError before any smoke test runs, while an explicit UTF-8
read returns all 56 instructions.
"""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("LOCAL_VALIDATION_TEST_REPO", HERE.parent)).resolve()

READER = (
    "import json,pathlib,sys;"
    "print(json.loads(pathlib.Path(sys.argv[1]).read_text())['instructions'].__len__())"
)
READER_UTF8 = (
    "import json,pathlib,sys;"
    "print(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))['instructions'].__len__())"
)


def idl_read_call():
    """The read_text call on the `idl` path inside local_validation.py."""
    tree = ast.parse(
        (ROOT / "scripts/local_validation.py").read_text(encoding="utf-8")
    )
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "read_text"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "idl"
        ):
            return node
    return None


class LocalValidationIdlEncodingTests(unittest.TestCase):
    def test_idl_read_specifies_utf8(self):
        call = idl_read_call()
        self.assertIsNotNone(call, "no idl.read_text call found")
        encodings = [
            keyword.value.value
            for keyword in call.keywords
            if keyword.arg == "encoding"
        ]
        self.assertEqual(encodings, ["utf-8"])

    def test_checked_in_pump_idl_is_locale_sensitive(self):
        idl = ROOT / "evidence/upstream/pump.json"
        self.assertTrue(idl.is_file(), f"missing checked-in IDL: {idl}")
        env = dict(os.environ, LC_ALL="C", PYTHONCOERCECLOCALE="0")
        env.pop("PYTHONUTF8", None)
        base = subprocess.run(
            [sys.executable, "-B", "-X", "utf8=0", "-c", READER, str(idl)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=30,
        )
        self.assertNotEqual(
            base.returncode, 0, "default read unexpectedly succeeded on ASCII locale"
        )
        self.assertIn(b"UnicodeDecodeError", base.stdout)
        fixed = subprocess.run(
            [sys.executable, "-B", "-X", "utf8=0", "-c", READER_UTF8, str(idl)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=30,
        )
        self.assertEqual(fixed.returncode, 0, fixed.stdout.decode("utf-8", "replace"))
        self.assertEqual(fixed.stdout.decode().strip(), "56")


if __name__ == "__main__":
    unittest.main()
