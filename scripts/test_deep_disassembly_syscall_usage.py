#!/usr/bin/env python3
"""Syscall reports count the relocated call sites that captured programs use."""
import collections
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import deep_disassembly  # noqa: E402
from window_elf_reader import Elf  # noqa: E402


class DeepDisassemblySyscallUsageTests(unittest.TestCase):
    def test_captured_program_reports_its_relocated_syscalls(self):
        elf = Elf(SCRIPTS.parent / "evidence/original/mayhem/deployed.so")
        expected = collections.Counter(
            name for name in deep_disassembly.relocated_syscalls(elf).values() if name)
        self.assertGreater(expected["sol_log_"], 0)
        self.assertNotIn("custom_panic", expected)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            argv = ["deep_disassembly.py", "--program", "mayhem", "--output", str(output)]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(deep_disassembly.main(), 0)
            usage = json.loads((output / "syscall-usage.json").read_text(encoding="utf-8"))
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            windows = json.loads((output / "windows-deep.json").read_text(encoding="utf-8"))
            externs = json.loads((output / "extern-usage.json").read_text(encoding="utf-8"))
            readme = (output / "README.md").read_text(encoding="utf-8")
        self.assertEqual(usage, dict(expected))
        self.assertEqual(summary["total_syscalls"], sum(expected.values()))
        self.assertEqual(summary["unique_syscalls"], len(expected))
        self.assertEqual(sorted({name for window in windows for name in window["syscalls"]}),
                         sorted(expected))
        self.assertIn("`sol_log_`", readme)
        self.assertNotIn("custom_panic", externs)
        # The hook has a positive-size dynamic function definition in .text.
        self.assertEqual(summary["total_internal_calls"], len(elf.calls) + 1)


if __name__ == "__main__":
    unittest.main()
