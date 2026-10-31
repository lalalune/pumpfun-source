#!/usr/bin/env python3
"""build_fee_selection reports where a shorter or longer body stops matching.

Comparing bytes with zip stops at the shorter body, so an equal prefix used to
publish first_difference null beside a failed comparison. compare.py and the
other whole-image reports use the shorter length in that case.
"""
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "build_fee_selection.py"
START, END = 0xAB158, 0xAB2D0
FAKE_RUSTC = """#!{python}
import pathlib, shutil, sys
argv = sys.argv[1:]
if "--version" in argv:
    print("rustc 1.44.0-fake")
    sys.exit(0)
shutil.copy(pathlib.Path(__file__).with_name("obj.o"), argv[argv.index("-o") + 1])
"""


def elf_object(body):
    """A relocatable ELF64 object holding `body` in .text.select_fee_tier."""
    names = b"\0.text.select_fee_tier\0.shstrtab\0"
    text_offset = 64
    names_offset = text_offset + len(body)
    table = names_offset + len(names)
    header = b"\x7fELF\x02\x01\x01" + bytes(9) + struct.pack(
        "<HHIQQQIHHHHHH", 1, 247, 1, 0, 0, table, 0, 64, 0, 0, 64, 3, 2)
    sections = [
        bytes(64),
        struct.pack("<IIQQQQIIQQ", 1, 1, 6, 0, text_offset, len(body), 0, 0, 8, 0),
        struct.pack("<IIQQQQIIQQ", 23, 3, 0, 0, names_offset, len(names), 0, 0, 1, 0),
    ]
    return header + body + names + b"".join(sections)


class FirstDifferenceTests(unittest.TestCase):
    def report(self, temporary, compiled_bytes):
        root = Path(temporary) / "repo"
        script = root / "scripts" / "build_fee_selection.py"
        script.parent.mkdir(parents=True)
        script.write_bytes(SCRIPT.read_bytes())
        source = root / "programs" / "pump-fees" / "recovered" / "fee_selection.rs"
        source.parent.mkdir(parents=True)
        source.write_text("pub fn select_fee_tier() -> u64 { 0 }\n")
        deployed = root / "evidence" / "original" / "pump_fees" / "deployed.so"
        deployed.parent.mkdir(parents=True)
        deployed.write_bytes(bytes(END))
        rustc = Path(temporary) / "toolchain" / "rust" / "bin" / "rustc"
        rustc.parent.mkdir(parents=True)
        rustc.write_text(FAKE_RUSTC.format(python=sys.executable))
        rustc.with_name("obj.o").write_bytes(elf_object(compiled_bytes))
        os.chmod(rustc, 0o755)
        output = Path(temporary) / "out"
        completed = subprocess.run(
            [sys.executable, "-B", str(script), "--toolchain", str(rustc.parents[2]),
             "--output", str(output)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads((output / "comparison.json").read_text())

    def test_longer_body_with_an_equal_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = self.report(temporary, bytes(END - START + 8))
        self.assertEqual(report["different_byte_offsets"], [])
        self.assertEqual(report["first_difference"], END - START)

    def test_shorter_body_with_an_equal_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = self.report(temporary, bytes(16))
        self.assertEqual(report["first_difference"], 16)

    def test_equal_bodies_have_no_first_difference(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = self.report(temporary, bytes(END - START))
        self.assertIsNone(report["first_difference"])
        self.assertTrue(report["instruction_match_except_unresolved_relocations"])

    def test_a_changed_byte_stays_the_first_difference(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = self.report(temporary, bytes(4) + b"\x01" + bytes(100))
        self.assertEqual(report["first_difference"], 4)


if __name__ == "__main__":
    unittest.main()
