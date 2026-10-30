#!/usr/bin/env python3
"""Deep section analysis packets are published only into clean output directories."""
import contextlib
import io
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import deep_section_analysis  # noqa: E402


def fake_elf_with_relocations(section_header, blob_size):
    return SimpleNamespace(
        b=bytearray(blob_size),
        secs={".rel.dyn": section_header},
        symbols={},
        lo=0,
        hi=blob_size,
    )


class DeepSectionLayer4Tests(unittest.TestCase):
    def test_idl_programs_recover_exactly_the_archived_selectors(self):
        from window_elf_reader import Elf
        for name, count in (("pump", 56), ("pump_amm", 38), ("pump_fees", 31)):
            with self.subTest(program=name):
                elf = Elf(SCRIPTS.parent / "evidence/original" / name / "deployed.so")
                recovered = deep_section_analysis.recover_anchor_idl(elf)["discriminators"]
                idl = deep_section_analysis.load_idl_discriminators(elf)
                self.assertEqual(len(recovered), count)
                self.assertEqual({bytes.fromhex(d["bytes"]) for d in recovered}, set(idl))

    @staticmethod
    def heuristic_elf(instructions):
        blob = bytearray(0xe0)
        for offset, data in instructions.items():
            blob[offset:offset + len(data)] = data
        # No .path attribute: no archived IDL, so the register-bound heuristic runs.
        return SimpleNamespace(b=bytes(blob), lo=0x40, hi=len(blob), entries=[])

    def test_branches_on_other_registers_are_not_discriminators(self):
        def lddw(dst, value):
            return (struct.pack("<BBHI", 0x18, dst, 0, value & 0xFFFFFFFF)
                    + struct.pack("<BBHI", 0, 0, 0, (value >> 32) & 0xFFFFFFFF))

        elf = self.heuristic_elf({
            # lddw r1, const; jeq r2, ... — the branch does not test r1.
            0x40: lddw(1, 0x300000000) + struct.pack("<BBhi", 0x1d, 0x20, 1, 0),
            # lddw r1, selector; jeq r1, ... — the branch tests the loaded register.
            0x60: lddw(1, 0x1122334455667788) + struct.pack("<BBhi", 0x1d, 0x10, 1, 0),
            # The same selector loaded again is reported once.
            0x80: lddw(2, 0x1122334455667788) + struct.pack("<BBhi", 0x5d, 0x02, 1, 0),
            # Immediate branches have no source register; the zero high nibble
            # must not make a branch on r2 appear to test a loaded r0.
            0xa0: lddw(0, 0x9988776655443322) + struct.pack("<BBhi", 0x15, 0x02, 1, 0),
            # An immediate comparison on the loaded destination is valid.
            0xc0: lddw(3, 0x8877665544332211) + struct.pack("<BBhi", 0x55, 0x03, 1, 0),
        })
        recovered = deep_section_analysis.recover_anchor_idl(elf)["discriminators"]
        self.assertEqual([d["bytes"] for d in recovered],
                         [value.to_bytes(8, "little").hex() for value in
                          (0x1122334455667788, 0x8877665544332211)])


class DeepSectionRelocationBoundsTests(unittest.TestCase):
    # sh_offset=8, sh_size=32 claims two entries reaching byte 40.
    TRUNCATED = (0, 0, 0, 0, 8, 32, 0, 0, 0, 16)
    # A size that is not a whole number of 16-byte entries.
    MISALIGNED = (0, 0, 0, 0, 0, 24, 0, 0, 0, 16)
    # One in-bounds entry: offset 0, size 16, blob of 32 bytes.
    VALID = (0, 0, 0, 0, 0, 16, 0, 0, 0, 16)

    def test_truncated_relocation_table_is_rejected(self):
        elf = fake_elf_with_relocations(self.TRUNCATED, 16)
        with self.assertRaisesRegex(ValueError, "truncated or misaligned relocation table"):
            deep_section_analysis.analyze_relocations(elf)

    def test_misaligned_relocation_table_is_rejected(self):
        elf = fake_elf_with_relocations(self.MISALIGNED, 64)
        with self.assertRaisesRegex(ValueError, "truncated or misaligned relocation table"):
            deep_section_analysis.analyze_relocations(elf)

    def test_in_bounds_table_is_still_analyzed(self):
        elf = fake_elf_with_relocations(self.VALID, 32)
        # One R_BPF_64_RELATIVE entry at offset 0 with no symbol reference.
        struct.pack_into("<QQ", elf.b, 0, 0x1000, 8)
        result = deep_section_analysis.analyze_relocations(elf)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["type_distribution"], {"R_BPF_64_RELATIVE": 1})


def generate(output):
    argv = ["deep_section_analysis.py", "--program", "mayhem", "--output", str(output)]
    with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
        return deep_section_analysis.main()


class DeepSectionStringAddressTests(unittest.TestCase):
    def test_run_reaching_the_section_end_uses_the_virtual_address_base(self):
        # .rodata mapped at 0x2000 but stored at file offset 0x40; the last
        # eight bytes are printable, so the run is flushed after the loop.
        blob = bytearray(0x50)
        blob[0x40:0x50] = b"\x00" * 8 + b"SECTION!"
        elf = SimpleNamespace(
            b=bytes(blob),
            secs={".rodata": (0, 0, 0, 0x2000, 0x40, 16, 0, 0, 0, 1)},
            relocations={},
            lo=0x100,
            hi=0x120,
        )
        layout = deep_section_analysis.analyze_data_layout(elf)
        (string,) = layout[".rodata"]["strings"]
        self.assertEqual(string["value"], "SECTION!")
        self.assertEqual(string["offset"], 8)
        self.assertEqual(string["address"], hex(0x2000 + 8))


class DeepSectionPublicationTests(unittest.TestCase):
    def test_stale_entry_is_rejected_before_any_packet_file_is_written(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            output.mkdir()
            (output / "stale.txt").write_text("not generated by this analysis\n")
            with self.assertRaisesRegex(ValueError, "unexpected packet entry: stale.txt"):
                generate(output)
            self.assertEqual([path.name for path in output.iterdir()], ["stale.txt"])

    def test_packet_bytes_do_not_follow_the_host_line_ending(self):
        # Model Windows text-I/O defaults at the actual file-open boundary.
        # Patching os.linesep alone does not change CPython TextIOWrapper.
        real_open = Path.open

        def windows_text_open(path, mode="r", buffering=-1, encoding=None,
                              errors=None, newline=None):
            if "b" not in mode and any(flag in mode for flag in "wax"):
                if newline is None:
                    newline = "\r\n"
                if encoding is None:
                    encoding = "cp1252"
            return real_open(path, mode, buffering=buffering, encoding=encoding,
                             errors=errors, newline=newline)

        with tempfile.TemporaryDirectory() as temporary:
            control = Path(temporary) / "control"
            output = Path(temporary) / "windows-defaults"
            with contextlib.redirect_stdout(io.StringIO()):
                generate(control)
                with mock.patch.object(Path, "open", windows_text_open):
                    generate(output)
            self.assertEqual(sorted(p.name for p in control.iterdir()),
                             sorted(p.name for p in output.iterdir()))
            for path in sorted(output.iterdir()):
                with self.subTest(entry=path.name):
                    self.assertEqual(path.read_bytes(),
                                     (control / path.name).read_bytes())
                    self.assertNotIn(b"\r", path.read_bytes())

    def test_regenerated_packet_still_verifies(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            self.assertEqual(generate(output), 0)
            self.assertEqual(generate(output), 0)
            completed = subprocess.run([sys.executable, "-I", "-B", str(output / "verify.py")],
                                       capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
