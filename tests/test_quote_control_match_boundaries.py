"""Logical SBF instruction-boundary and ELF section checks for pump_quote_control_function_match."""

import argparse
import contextlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
import pump_quote_control_function_match as matcher  # noqa: E402


def slot(op=0x95, src=0, dst=0, offset=0, immediate=0) -> bytes:
    return struct.pack("<BBhi", op, (src << 4) | dst, offset, immediate)


def minimal_elf64(
    *,
    ei_class: int = 2,
    ei_data: int = 1,
    shentsize: int = 64,
    text_type: int = 1,
    strtab_type: int = 3,
    text_name_offset: int = 1,
    strtab_bytes: bytes = b"\x00.text\x00.shstrtab\x00",
    trailing_bytes: bytes = b"FAKE\x00",
) -> bytearray:
    code = slot(0xb7, dst=1, immediate=7) + slot(0x95)
    ehdr = bytearray(64)
    ehdr[0:4] = b"\x7fELF"
    ehdr[4] = ei_class
    ehdr[5] = ei_data
    ehdr[6] = 1
    code_offset = 64
    strtab_offset = code_offset + len(code)
    trailing_offset = strtab_offset + len(strtab_bytes)
    shoff = trailing_offset + len(trailing_bytes)

    struct.pack_into("<Q", ehdr, 0x28, shoff)
    struct.pack_into("<HHH", ehdr, 0x3A, shentsize, 3, 2)

    null_shdr = bytes(max(shentsize, 64))[:shentsize]
    text_shdr = bytearray(max(shentsize, 64))
    struct.pack_into(
        "<IIQQQQIIQQ",
        text_shdr,
        0,
        text_name_offset,
        text_type,
        6,
        0x1000,
        code_offset,
        len(code),
        0,
        0,
        8,
        0,
    )
    str_shdr = bytearray(max(shentsize, 64))
    struct.pack_into(
        "<IIQQQQIIQQ",
        str_shdr,
        0,
        7,
        strtab_type,
        0,
        0,
        strtab_offset,
        len(strtab_bytes),
        0,
        0,
        1,
        0,
    )
    return bytearray(
        bytes(ehdr)
        + code
        + strtab_bytes
        + trailing_bytes
        + null_shdr
        + bytes(text_shdr[:shentsize])
        + bytes(str_shdr[:shentsize])
    )


class QuoteControlMatchBoundaryTests(unittest.TestCase):
    def test_aligned_matches_skips_lddw_continuation_slots(self):
        # First 16 bytes are one wide lddw whose second slot happens to carry 0x95 in byte 8;
        # the genuine single-slot exit instruction starts at byte 16.
        original = slot(0x18, dst=1, immediate=42) + slot(0x95, immediate=0) + slot(0x95)
        candidate = slot(0x95)
        self.assertEqual(
            matcher._aligned_matches(matcher.mask(candidate), matcher.mask(original)),
            [16],
        )

    def test_main_does_not_report_lddw_continuation_as_masked_or_raw_match(self):
        original = slot(0x18, dst=1, immediate=0) + slot(0x95, immediate=0) + slot(0x95)
        candidate = slot(0x95)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            orig_path = root / "orig.so"
            cand_path = root / "cand.so"
            out_path = root / "report.json"
            orig_path.write_bytes(original)
            cand_path.write_bytes(candidate)
            args = argparse.Namespace(
                candidate=cand_path,
                objdump="not-executed",
                pattern="quote_control",
                output=out_path,
            )
            fake_sections = [
                {".text": {"addr": 0x100, "offset": 0, "size": len(original)}},
                {".text": {"addr": 0x200, "offset": 0, "size": len(candidate)}},
            ]
            with (
                mock.patch.object(matcher.argparse.ArgumentParser, "parse_args", return_value=args),
                mock.patch.object(matcher, "ORIGINAL", orig_path),
                mock.patch.object(matcher, "sections", side_effect=fake_sections),
                mock.patch.object(
                    matcher,
                    "candidate_functions",
                    return_value=[(0x200, len(candidate), "quote_control_exit")],
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                matcher.main()
            report = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(report["functions"][0]["masked_matches"], [0x110])
            self.assertEqual(report["functions"][0]["raw_matches"], [0x110])

    def test_aligned_matches_rejects_window_splitting_trailing_lddw(self):
        haystack = slot(0xb7, dst=1, immediate=3) + slot(0x18, dst=2, immediate=0) + slot(0, immediate=0)
        needle = slot(0xb7, dst=1, immediate=3) + slot(0x18, dst=2, immediate=0)
        self.assertEqual(matcher._aligned_matches(needle, haystack), [])

    def test_nobits_text_section_is_rejected_by_function_body(self):
        elf = minimal_elf64(text_type=8)  # SHT_NOBITS
        parsed = matcher.sections(elf)
        with self.assertRaisesRegex(ValueError, "SHT_NOBITS|file payload"):
            matcher.function_body(elf, parsed, 0x1000, 16)

    def test_malformed_elf_and_section_string_table_bounds_raise_value_error(self):
        bad_blobs = {
            "truncated_blob": b"\x7fELF",
            "bad_magic": bytes(minimal_elf64()).replace(b"\x7fELF", b"NOPE", 1),
            "elf32_class": bytes(minimal_elf64(ei_class=1)),
            "big_endian": bytes(minimal_elf64(ei_data=2)),
            "undersized_shentsize": bytes(minimal_elf64(shentsize=32)),
            "nobits_shstrtab": bytes(minimal_elf64(strtab_type=8)),
            "name_offset_outside_shstrtab": bytes(
                minimal_elf64(
                    strtab_bytes=b"\x00.text\x00.shstrtab\x00",
                    trailing_bytes=b"OUTSIDE\x00",
                    text_name_offset=17,  # points into trailing_bytes past .shstrtab!
                )
            ),
            "unterminated_shstrtab": bytes(
                minimal_elf64(
                    strtab_bytes=b"\x00.shstrtab\x00.text_no_nul",
                    trailing_bytes=b"LEAKED\x00",
                    text_name_offset=11,
                )
            ),
        }
        for label, blob in bad_blobs.items():
            with self.subTest(case=label), self.assertRaises(ValueError):
                matcher.sections(blob)


if __name__ == "__main__":
    unittest.main()
