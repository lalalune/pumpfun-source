"""Every scripts/ consumer must read the upstream Pump IDL as UTF-8.

Sibling of merged #2188 (scripts/deep_disassembly.py, scripts/recover_dispatch.py)
and #2217 (scripts/local_validation.py), which fixed the CI-reachable consumers of
this read. The checked-in IDL carries non-ASCII documentation bytes (U+2192 in the
buy instruction docs), so a read with the platform default encoding raises
UnicodeDecodeError on an ASCII-locale host before any analysis runs:

    $ LC_ALL=C PYTHONUTF8=0 PYTHONCOERCECLOCALE=0 python3 scripts/pump_create_differential.py --help
    UnicodeDecodeError: 'ascii' codec can't decode byte 0xe2 in position 56968

The remaining consumers are the offline differential/probe scripts under scripts/
and the captured-behaviour tests that still read it inline, so this pins the
contract for them: the IDL is always decoded explicitly. Frozen research packets
under research/ are deliberately out of scope: their producers are pinned evidence.
"""
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("PUMP_IDL_READER_TEST_REPO", HERE.parent)).resolve()
SCANNED = (ROOT / "scripts", ROOT / "tests")

IDL_REL = "evidence/upstream/pump.json"
READER = (
    "import json,pathlib,sys;"
    "print(json.loads(pathlib.Path(sys.argv[1]).read_text())['instructions'].__len__())"
)
READER_UTF8 = (
    "import json,pathlib,sys;"
    "print(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))['instructions'].__len__())"
)

# Reads of the IDL literal that fall back to the platform default encoding.
BARE_READS = (
    f"'{IDL_REL}').read_text()",
    f'"{IDL_REL}").read_text()',
    f"open('{IDL_REL}')",
    f'open("{IDL_REL}")',
)
BINDINGS = (f'IDL = ROOT / "{IDL_REL}"', f"IDL = ROOT / '{IDL_REL}'")


def bare_reads(text):
    found = [pattern for pattern in BARE_READS if pattern in text]
    if any(binding in text for binding in BINDINGS) and "IDL.read_text()" in text:
        found.append("IDL.read_text()")
    return found


class PumpIdlReaderTests(unittest.TestCase):
    def test_no_script_reads_the_idl_with_the_platform_default_encoding(self):
        offenders = {}
        for directory in SCANNED:
            for path in sorted(directory.glob("*.py")):
                found = bare_reads(path.read_text(encoding="utf-8"))
                if found:
                    offenders[path.relative_to(ROOT).as_posix()] = found
        self.assertEqual(offenders, {}, "scripts and tests must decode the pump IDL as UTF-8")

    def test_checked_in_pump_idl_is_locale_sensitive(self):
        idl = ROOT / IDL_REL
        self.assertTrue(idl.is_file(), f"missing checked-in IDL: {idl}")
        env = dict(os.environ, LC_ALL="C", PYTHONCOERCECLOCALE="0")
        env.pop("PYTHONUTF8", None)
        base = subprocess.run(
            [sys.executable, "-B", "-X", "utf8=0", "-c", READER, str(idl)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
        )
        self.assertNotEqual(base.returncode, 0, "default read unexpectedly succeeded on an ASCII locale")
        self.assertIn(b"UnicodeDecodeError", base.stdout)
        fixed = subprocess.run(
            [sys.executable, "-B", "-X", "utf8=0", "-c", READER_UTF8, str(idl)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
        )
        self.assertEqual(fixed.returncode, 0, fixed.stdout.decode("utf-8", "replace"))
        self.assertEqual(fixed.stdout.decode().strip(), "56")


if __name__ == "__main__":
    unittest.main()