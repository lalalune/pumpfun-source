#!/usr/bin/env python3
"""Bytecode signature packets require every captured program before writing."""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import bytecode_signatures  # noqa: E402


def run_main(root, output):
    argv = ["bytecode_signatures.py", "--output", str(output)]
    with mock.patch.object(bytecode_signatures, "REPO", root), \
            mock.patch.object(sys, "argv", argv), \
            contextlib.redirect_stdout(io.StringIO()):
        bytecode_signatures.main()


class BytecodeSignatureInputTests(unittest.TestCase):
    def test_missing_program_elf_is_rejected_before_any_read_or_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            for program in bytecode_signatures.PROGRAMS[1:]:
                elf = root / "evidence" / "original" / program / "deployed.so"
                elf.parent.mkdir(parents=True)
                elf.write_bytes(b"")
            output = Path(temporary) / "out" / "packet"
            with mock.patch.object(bytecode_signatures, "Elf", side_effect=AssertionError("ELF read")):
                with self.assertRaises(SystemExit) as raised:
                    run_main(root, output)
            self.assertIn("evidence/original/pump/deployed.so", str(raised.exception))
            self.assertFalse(output.parent.exists())

    def test_checkout_without_program_elfs_publishes_no_packet(self):
        # A packet generated from zero programs would otherwise self-verify.
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            try:
                run_main(Path(temporary) / "repo", output)
            except SystemExit:
                pass
            if output.exists():
                verified = subprocess.run([sys.executable, "-I", "-B", str(output / "verify.py")],
                                          capture_output=True, text=True)
                self.assertNotEqual(verified.returncode, 0, "zero-program packet verified")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
