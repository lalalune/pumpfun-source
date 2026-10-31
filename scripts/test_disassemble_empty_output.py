#!/usr/bin/env python3
"""An objdump run that prints no disassembly must not publish an analysis directory."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "disassemble.py"
# Exits 0 on every invocation; prints nothing for the program named in the marker.
FAKE_OBJDUMP = """#!{python}
import os
import sys
if sys.argv[1] == "--version":
    print("fake objdump 1.0")
elif os.path.basename(os.getcwd()) != "{silent}":
    print("disassembly of " + os.path.basename(os.getcwd()))
"""


class DisassembleEmptyOutputTests(unittest.TestCase):
    def run_tool(self, temporary, silent):
        objdump = Path(temporary) / "objdump"
        objdump.write_text(FAKE_OBJDUMP.format(python=sys.executable, silent=silent))
        os.chmod(objdump, 0o755)
        output = Path(temporary) / "asm"
        completed = subprocess.run([sys.executable, "-B", str(SCRIPT), "--objdump", str(objdump),
                                    "--output", str(output)], capture_output=True, text=True)
        return completed, output

    def test_empty_program_disassembly_is_not_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed, output = self.run_tool(temporary, "pump_fees")
            self.assertNotEqual(completed.returncode, 0, "empty pump_fees.asm was published")
            self.assertIn("pump_fees", completed.stderr)
            self.assertFalse(output.exists())
            self.assertEqual(sorted(path.name for path in Path(temporary).iterdir()), ["objdump"])

    def test_nonempty_disassembly_is_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed, output = self.run_tool(temporary, "no-such-program")
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual((output / "pump.asm").read_text(), "disassembly of pump\n")


if __name__ == "__main__":
    unittest.main()
