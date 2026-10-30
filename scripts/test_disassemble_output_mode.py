#!/usr/bin/env python3
"""Published analyst disassembly keeps the permissions of an ordinary directory."""
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "disassemble.py"
FAKE_OBJDUMP = """#!{python}
import sys
print("fake objdump 1.0" if sys.argv[1] == "--version" else "disassembly")
"""


class DisassembleOutputModeTests(unittest.TestCase):
    def published_mode(self, umask):
        with tempfile.TemporaryDirectory() as temporary:
            objdump = Path(temporary) / "objdump"
            objdump.write_text(FAKE_OBJDUMP.format(python=sys.executable))
            os.chmod(objdump, 0o755)
            output = Path(temporary) / "asm"
            previous = os.umask(umask)
            try:
                completed = subprocess.run(
                    [sys.executable, "-B", str(SCRIPT), "--objdump", str(objdump), "--output", str(output)],
                    capture_output=True, text=True)
            finally:
                os.umask(previous)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(sorted(p.name for p in Path(temporary).iterdir()), ["asm", "objdump"])
            return stat.S_IMODE(output.stat().st_mode)

    def test_output_directory_follows_the_process_umask(self):
        for umask, mode in ((0o022, 0o755), (0o027, 0o750)):
            with self.subTest(umask=oct(umask)):
                self.assertEqual(oct(self.published_mode(umask)), oct(mode))


if __name__ == "__main__":
    unittest.main()
