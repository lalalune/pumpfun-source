#!/usr/bin/env python3
"""Analyst disassembly output is created only after every program is disassembled."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "disassemble.py"
ROOT = SCRIPT.parents[1]
CAPTURES = {
    "donation_relay": "evidence/dependencies/donation_relay",
    "mayhem": "evidence/original/mayhem",
    "pump": "evidence/original/pump",
    "pump_amm": "evidence/original/pump_amm",
    "pump_fees": "evidence/original/pump_fees",
}
FAKE_OBJDUMP = """#!{python}
import os
import sys
if sys.argv[1] == "--version":
    print("fake objdump 1.0")
elif "{fail}" and os.path.basename(os.getcwd()) == "{fail}":
    print("INJECTED_OBJDUMP_FAILURE " + os.path.basename(os.getcwd()) + " " + sys.argv[-1], file=sys.stderr)
    sys.exit(3)
else:
    print("disassembly of " + os.path.basename(os.getcwd()) + " from " + sys.argv[-1])
"""


class DisassemblePublicationTests(unittest.TestCase):
    def run_tool(self, temporary, fail=""):
        objdump = Path(temporary) / "objdump"
        objdump.write_text(FAKE_OBJDUMP.format(python=sys.executable, fail=fail))
        os.chmod(objdump, 0o755)
        output = Path(temporary) / "asm"
        completed = subprocess.run([sys.executable, "-B", str(SCRIPT), "--objdump", str(objdump),
                                    "--output", str(output)], capture_output=True, text=True)
        return completed, output

    def test_failed_disassembly_leaves_no_output_and_can_be_rerun(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed, output = self.run_tool(temporary, fail="pump_fees")
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("INJECTED_OBJDUMP_FAILURE pump_fees deployed.so", completed.stderr)
            self.assertEqual(sorted(path.name for path in Path(temporary).iterdir()), ["objdump"])
            completed, output = self.run_tool(temporary)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            outputs = json.loads((output / "manifest.json").read_text())["outputs"]
            self.assertEqual(sorted(outputs), sorted(CAPTURES))
            for name, capture in CAPTURES.items():
                self.assertEqual(outputs[name]["input_sha256"],
                                 hashlib.sha256((ROOT / capture / "deployed.so").read_bytes()).hexdigest(),
                                 name)
            # Each program is disassembled from its own input directory under the
            # bare snapshot name, so objdump's file heading stays deterministic.
            self.assertEqual((output / "pump.asm").read_text(),
                             "disassembly of pump from deployed.so\n")

    def test_missing_objdump_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "asm"
            completed = subprocess.run([sys.executable, "-B", str(SCRIPT), "--objdump",
                                        str(Path(temporary) / "missing"), "--output", str(output)],
                                       capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_existing_output_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / "asm").mkdir()
            completed, output = self.run_tool(temporary)
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(list(output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
