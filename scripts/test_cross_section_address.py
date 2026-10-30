#!/usr/bin/env python3
"""Cross-section pointer classification must use section virtual addresses.

`analyze_cross_section()` compares lddw pointer immediates (virtual
addresses) against data-section extents.  It previously compared them
against the section file offset, so every data reference in a
non-identity-mapped ELF was misclassified.

The fixtures below are synthetic in-memory ELF stand-ins; no real files
are read.  Section tuples follow the window_elf_reader shape:
(name, type, flags, addr, offset, size, link, info, align, entsize).
"""
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deep_section_analysis import analyze_cross_section


# Section tuple indices, as unpacked by window_elf_reader.Elf.
SEC_ADDR = 3
SEC_OFFSET = 4
SEC_SIZE = 5


def _section(addr, offset, size):
    return (0, 1, 0, addr, offset, size, 0, 0, 8, 0)


def _lddw(imm, dst=0, src=0):
    """Encode an lddw (opcode 0x18) with a 64-bit immediate.

    Layout consumed by the analyzer: opcode at +0, imm_lo at +4,
    imm_hi at +12.  The two unused pseudo-instruction words are zero.
    """
    insn = bytearray(16)
    insn[0] = 0x18
    insn[1] = (src << 4) | (dst & 0xF)
    struct.pack_into("<I", insn, 4, imm & 0xFFFFFFFF)
    struct.pack_into("<I", insn, 12, (imm >> 32) & 0xFFFFFFFF)
    return insn


def _fake_elf(text_offset, text_size, code, rodata, data_rel_ro=None):
    """Build a minimal Elf stand-in with one text window at text_offset."""
    total = max(
        text_offset + text_size,
        *(s[SEC_OFFSET] + s[SEC_SIZE] for s in (rodata, data_rel_ro) if s),
    )
    blob = bytearray(total)
    blob[text_offset:text_offset + len(code)] = code

    secs = {".text": _section(0, text_offset, text_size), ".rodata": rodata}
    if data_rel_ro is not None:
        secs[".data.rel.ro"] = data_rel_ro

    return SimpleNamespace(
        b=bytes(blob),
        lo=text_offset,
        hi=text_offset + text_size,
        secs=secs,
        funcs=[],
        entries=[text_offset],
    )


class CrossSectionAddressTest(unittest.TestCase):
    def test_rodata_reference_uses_section_address(self):
        # .rodata lives at virtual address 0x1000 but at file offset 0x20.
        rodata = _section(0x1000, 0x20, 0x20)
        # The text window is at file offset 0x100; the lddw points at 0x1000.
        elf = _fake_elf(0x100, 0x40, _lddw(0x1000), rodata)

        result = analyze_cross_section(elf)
        window = result["window_data_refs"][0]

        self.assertEqual(window["rodata_refs"], 1)
        self.assertEqual(window["data_rel_ro_refs"], 0)
        self.assertEqual(window["text_refs"], 0)
        self.assertEqual(window["other_refs"], 0)
        self.assertEqual(window["rodata_addresses"], [hex(0x1000)])
        self.assertEqual(result["total_rodata_refs"], 1)
        self.assertEqual(result["windows_with_rodata_refs"], 1)
        self.assertEqual(
            result["hot_rodata_addresses"],
            [{"address": hex(0x1000), "ref_count": 1}],
        )

    def test_file_offset_immediate_is_not_a_rodata_reference(self):
        # An immediate equal to the rodata *file offset* is not an address.
        rodata = _section(0x1000, 0x20, 0x20)
        elf = _fake_elf(0x100, 0x40, _lddw(0x20), rodata)

        result = analyze_cross_section(elf)
        window = result["window_data_refs"][0]

        self.assertEqual(window["rodata_refs"], 0)
        self.assertEqual(window["other_refs"], 1)
        self.assertEqual(result["total_rodata_refs"], 0)

    def test_data_rel_ro_reference_uses_section_address(self):
        rodata = _section(0x1000, 0x20, 0x20)
        data_rel_ro = _section(0x2000, 0x40, 0x18)
        elf = _fake_elf(0x100, 0x40, _lddw(0x2000), rodata, data_rel_ro)

        result = analyze_cross_section(elf)
        window = result["window_data_refs"][0]

        self.assertEqual(window["rodata_refs"], 0)
        self.assertEqual(window["data_rel_ro_refs"], 1)
        self.assertEqual(result["total_data_refs"], 1)
        self.assertEqual(window["data_rel_ro_addresses"], [hex(0x2000)])

    def test_identity_mapped_section_still_matches(self):
        # addr == offset must keep working after switching to sec[3].
        rodata = _section(0x1000, 0x1000, 0x20)
        elf = _fake_elf(0x100, 0x40, _lddw(0x1000), rodata)

        result = analyze_cross_section(elf)
        self.assertEqual(result["window_data_refs"][0]["rodata_refs"], 1)

    def test_boundary_refs_are_half_open(self):
        rodata = _section(0x1000, 0x20, 0x20)
        last = _fake_elf(0x100, 0x40, _lddw(0x101F), rodata)
        past = _fake_elf(0x180, 0x40, _lddw(0x1020), rodata)
        # Two windows so the out-of-range pointer lands in "other".
        past.entries = [0x100, 0x180]
        past.lo, past.hi = 0x100, 0x1C0

        self.assertEqual(
            analyze_cross_section(last)["window_data_refs"][0]["rodata_refs"], 1)
        refs = analyze_cross_section(past)["window_data_refs"]
        self.assertEqual([w["rodata_refs"] for w in refs], [0, 0])
        self.assertEqual([w["other_refs"] for w in refs], [0, 1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
