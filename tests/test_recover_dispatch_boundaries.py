#!/usr/bin/env python3
"""Boundary and relocation regression tests for scripts/recover_dispatch.py."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import recover_dispatch  # noqa: E402


DISC_VAL = 0x1122334455667788
DISC_BYTES = struct.pack("<Q", DISC_VAL)
EXIT = struct.pack("<BBhi", 0x95, 0, 0, 0)


def insn(op, regs=0, off=0, imm=0):
    return struct.pack("<BBhi", op, regs, off, imm)


def lddw(dst, value):
    return (struct.pack("<BBHI", 0x18, dst, 0, value & 0xFFFFFFFF)
            + struct.pack("<BBHI", 0x00, 0x00, 0, (value >> 32) & 0xFFFFFFFF))


def build_elf(text, *, text_addr=0x1000, text_type=1, text_size=None,
              rodata=b"", relocations=(), rel_section_type=9, raw_rel_bytes=None,
              sections_before_text=False):
    names = b"\0.text\0.rodata\0.rel.dyn\0.shstrtab\0"
    name_off = {
        name: names.index(name.encode() + b"\0")
        for name in (".text", ".rodata", ".rel.dyn", ".shstrtab")
    }
    if raw_rel_bytes is not None:
        rel_payload = raw_rel_bytes
        rel_entsize = 24 if rel_section_type == 4 else 16
    elif rel_section_type == 4:
        rel_payload = b"".join(
            struct.pack("<QQq", text_addr + off, rtype, 0)
            for off, rtype in relocations
        )
        rel_entsize = 24
    else:
        rel_payload = b"".join(
            struct.pack("<QQ", text_addr + off, rtype)
            for off, rtype in relocations
        )
        rel_entsize = 16

    blob = bytearray(64)

    def pad8():
        if len(blob) % 8:
            blob.extend(bytes(8 - (len(blob) % 8)))

    if sections_before_text:
        shstr_off = len(blob)
        blob.extend(names)
        pad8()
        rel_off = len(blob)
        blob.extend(rel_payload)
        pad8()
        shoff = len(blob)
        blob.extend(bytes(64 * 4))
        text_off = len(blob)
        blob.extend(text)
        rows = [
            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (name_off[".text"], text_type, 6, text_addr, text_off,
             len(text) if text_size is None else text_size, 0, 0, 8, 0),
            (name_off[".rel.dyn"], rel_section_type, 0, 0, rel_off,
             len(rel_payload), 0, 0, 8, rel_entsize),
            (name_off[".shstrtab"], 3, 0, 0, shstr_off, len(names), 0, 0, 1, 0),
        ]
        shstr_idx = 3
        blob[shoff:shoff + 64 * 4] = b"".join(
            struct.pack("<IIQQQQIIQQ", *r) for r in rows
        )
    else:
        pad8()
        text_off = len(blob)
        blob.extend(text)
        ro_off = len(blob)
        blob.extend(rodata)
        pad8()
        rel_off = len(blob)
        blob.extend(rel_payload)
        shstr_off = len(blob)
        blob.extend(names)
        pad8()
        shoff = len(blob)
        rows = [
            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (name_off[".text"], text_type, 6, text_addr, text_off,
             len(text) if text_size is None else text_size, 0, 0, 8, 0),
            (name_off[".rodata"], 1, 2, text_addr + len(text), ro_off,
             len(rodata), 0, 0, 1, 0),
            (name_off[".rel.dyn"], rel_section_type, 0, 0, rel_off,
             len(rel_payload), 0, 0, 8, rel_entsize),
            (name_off[".shstrtab"], 3, 0, 0, shstr_off, len(names), 0, 0, 1, 0),
        ]
        shstr_idx = 4
        blob.extend(b"".join(struct.pack("<IIQQQQIIQQ", *r) for r in rows))

    blob[:64] = struct.pack(
        "<16sHHIQQQIHHHHHH",
        b"\x7fELF\x02\x01\x01" + bytes(9),
        3,
        247,
        1,
        text_addr,
        0,
        shoff,
        0,
        64,
        0,
        0,
        64,
        len(rows),
        shstr_idx,
    )
    return bytes(blob)


class RecoverDispatchBoundaryTests(unittest.TestCase):
    def run_recover(self, elf_bytes, discriminator=DISC_BYTES):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        root = Path(workspace.name)
        (root / "evidence/original/pump").mkdir(parents=True)
        (root / "evidence/upstream").mkdir(parents=True)
        (root / "evidence/original/pump/deployed.so").write_bytes(elf_bytes)
        idl = {
            "instructions": [
                {"name": "probe_ix", "discriminator": list(discriminator)}
            ]
        }
        (root / "evidence/upstream/pump.json").write_text(
            json.dumps(idl), encoding="utf-8"
        )
        return recover_dispatch.recover("pump", root)

    def test_comparison_scan_does_not_read_past_text_into_rodata_or_eof(self):
        with self.subTest(case="rodata_after_text"):
            # ASCII ']a' (0x5d, 0x61) in .rodata immediately after .text has
            # opcode 0x5d (jne) and low register nibble 1, matching dst=r1.
            rodata_elf = build_elf(lddw(1, DISC_VAL), rodata=b"]a0123456789abcdef")
            recovered = self.run_recover(rodata_elf)
            self.assertEqual(recovered["instructions"]["probe_ix"]["matches"], [])

        with self.subTest(case="text_at_eof"):
            # When .text is the final byte range in the file, scanning past
            # .text must return no match rather than raising struct.error.
            eof_elf = build_elf(lddw(1, DISC_VAL), sections_before_text=True)
            eof_recovered = self.run_recover(eof_elf)
            self.assertEqual(eof_recovered["instructions"]["probe_ix"]["matches"], [])

    def test_branch_target_must_land_on_logical_text_instruction(self):
        with self.subTest(case="jne_fallthrough_past_text"):
            jne_at_end = build_elf(
                lddw(1, DISC_VAL) + insn(0x5D, 0x21, 4, 0),
                rodata=b"not executable code",
            )
            self.assertEqual(
                self.run_recover(jne_at_end)["instructions"]["probe_ix"]["matches"], []
            )

        for bad_off in (5, -10):
            with self.subTest(case="jeq_outside_text", bad_off=bad_off):
                bad_jeq = build_elf(
                    lddw(1, DISC_VAL) + insn(0x1D, 0x21, bad_off, 0) + EXIT
                )
                self.assertEqual(
                    self.run_recover(bad_jeq)["instructions"]["probe_ix"]["matches"],
                    [],
                )

        with self.subTest(case="jeq_into_lddw_continuation_slot"):
            fake_call_in_imm = struct.unpack("<I", b"\x02\x00\x00\x00")[0]
            embedded_lddw = (
                struct.pack("<BBHI", 0x18, 3, 0, 0)
                + insn(0x85, 0x10, 0, fake_call_in_imm)
            )
            mid_lddw_target = build_elf(
                lddw(1, DISC_VAL)
                + insn(0x1D, 0x21, 1, 0)  # jumps +1 slot into embedded_lddw+8
                + embedded_lddw
                + EXIT * 3
            )
            self.assertEqual(
                self.run_recover(mid_lddw_target)["instructions"]["probe_ix"]["matches"],
                [],
            )

    def test_rejects_invalid_text_extent_and_truncated_lddw(self):
        with self.subTest(case="nobits_text"):
            nobits = build_elf(EXIT, text_type=8, text_size=0x10000)
            with self.assertRaisesRegex(ValueError, "text"):
                self.run_recover(nobits)

        with self.subTest(case="unaligned_text"):
            unaligned = build_elf(EXIT + b"\x00" * 4)
            with self.assertRaisesRegex(ValueError, "text"):
                self.run_recover(unaligned)

        with self.subTest(case="truncated_lddw_at_text_end"):
            truncated_lddw = struct.pack("<BBHI", 0x18, 1, 0, DISC_VAL & 0xFFFFFFFF)
            rodata_tail = (
                struct.pack("<BBHI", 0x00, 0x00, 0, (DISC_VAL >> 32) & 0xFFFFFFFF)
                + insn(0x1D, 0x21, 0, 0)
                + EXIT
            )
            with self.assertRaisesRegex(ValueError, "truncated.*instruction"):
                self.run_recover(build_elf(truncated_lddw, rodata=rodata_tail))

    def test_skips_relocated_lddw_address_matching_discriminator_bytes(self):
        text = (
            lddw(1, DISC_VAL)
            + insn(0x1D, 0x21, 1, 0)
            + EXIT
            + insn(0x85, 0x10, 0, 0)
            + EXIT
        )
        for sec_type in (9, 4):
            with self.subTest(rel_section_type=sec_type):
                relocated = build_elf(
                    text, relocations=[(0, 8)], rel_section_type=sec_type
                )
                self.assertEqual(
                    self.run_recover(relocated)["instructions"]["probe_ix"]["matches"],
                    [],
                )

        with self.subTest(case="null_relocation_control"):
            none_reloc = build_elf(text, relocations=[(0, 0)])
            matches = self.run_recover(none_reloc)["instructions"]["probe_ix"]["matches"]
            self.assertEqual(len(matches), 1)
            self.assertEqual(
                matches[0]["first_direct_calls"],
                [{"call_address": 0x1020, "target": 0x1028}],
            )

        for bad_rel_off in (4, 8):
            with self.subTest(case="unaligned_or_continuation_relocation", offset=bad_rel_off):
                with self.assertRaisesRegex(ValueError, "relocation.*instruction"):
                    self.run_recover(build_elf(text, relocations=[(bad_rel_off, 8)]))

    def test_handler_scan_skips_relocated_extern_calls_and_invalid_call_targets(self):
        with self.subTest(case="relocated_extern_calls_skipped"):
            text = (
                lddw(2, DISC_VAL)          # 0x1000..0x1010
                + insn(0x1D, 0x20, 1, 0)   # 0x1010: jeq r0, r2, +1 -> 0x1020
                + EXIT                     # 0x1018
                + insn(0x85, 0x10, 0, -1)  # 0x1020: extern call (type 10, imm=-1)
                + insn(0x85, 0x10, 0, 0)   # 0x1028: extern call (type 10, imm=0)
                + insn(0x85, 0x10, 0, 2)   # 0x1030: internal call -> 0x1048
                + EXIT                     # 0x1038
                + EXIT                     # 0x1040
                + EXIT                     # 0x1048: internal handler entry
            )
            elf = build_elf(text, relocations=[(0x20, 10), (0x28, 10)])
            matches = self.run_recover(elf)["instructions"]["probe_ix"]["matches"]
            self.assertEqual(len(matches), 1)
            self.assertEqual(
                matches[0],
                {
                    "constant_address": 0x1000,
                    "comparison_address": 0x1010,
                    "matched_branch_address": 0x1020,
                    "first_direct_calls": [{"call_address": 0x1030, "target": 0x1048}],
                },
            )

        with self.subTest(case="unlinked_and_out_of_text_calls_ignored"):
            bad_calls = (
                lddw(2, DISC_VAL)
                + insn(0x1D, 0x20, 0, 0)   # -> 0x1018
                + insn(0x85, 0x10, 0, -1)  # unlinked -1 placeholder
                + insn(0x85, 0x10, 0, 50)  # jumps past .text
                + EXIT
            )
            bad_matches = self.run_recover(build_elf(bad_calls))["instructions"]["probe_ix"]["matches"]
            self.assertEqual(len(bad_matches), 1)
            self.assertEqual(bad_matches[0]["first_direct_calls"], [])

        with self.subTest(case="malformed_relocation_table_size"):
            malformed_rel = build_elf(EXIT, raw_rel_bytes=b"\x00" * 8)
            with self.assertRaisesRegex(ValueError, "relocation"):
                self.run_recover(malformed_rel)

    def test_captured_programs_retain_exact_dispatch_recovery(self):
        expected = json.loads((REPO / "evidence/dispatch-map.json").read_text(encoding="utf-8"))
        actual = recover_dispatch.dispatch(REPO)
        self.assertEqual({name: actual[name] for name in expected}, expected)
        self.assertEqual(
            sum(bool(row["matches"]) for row in actual["donation_relay"]["instructions"].values()),
            10,
        )


if __name__ == "__main__":
    unittest.main()
