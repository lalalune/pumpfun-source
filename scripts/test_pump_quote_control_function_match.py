#!/usr/bin/env python3
"""Pure byte-array regressions; no captured ELF, objdump, or target execution."""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

import pump_quote_control_function_match as matcher


def slot(op=0x95, src=0, dst=0, offset=0, immediate=0):
    return struct.pack('<BBhi', op, (src << 4) | dst, offset, immediate)


class MaskTests(unittest.TestCase):
    def test_empty_code_is_unchanged(self):
        self.assertEqual(matcher.mask(b''), b'')

    def test_ordinary_instructions_keep_every_byte(self):
        code = slot(0xb7, 3, 4, -7, 123) + slot(0x8d, 1, 2, 5, 9) + slot()
        self.assertEqual(matcher.mask(code), code)

    def test_legacy_relative_call_policy_is_unchanged(self):
        for src in (0, 1):
            for immediate in (-2147483648, -2, 0, 1, 2147483647):
                with self.subTest(src=src, immediate=immediate):
                    code = slot(0x85, src, 3, -2, immediate)
                    self.assertEqual(matcher.mask(code), code[:4] + b'\0' * 4)

    def test_unresolved_call_sentinel_is_preserved(self):
        for src in (0, 1):
            with self.subTest(src=src):
                code = slot(0x85, src, immediate=-1)
                self.assertEqual(matcher.mask(code), code)

    def test_other_call_source_registers_are_preserved(self):
        for src in range(2, 16):
            with self.subTest(src=src):
                code = slot(0x85, src, immediate=17)
                self.assertEqual(matcher.mask(code), code)

    def test_lddw_masks_only_its_two_immediate_words(self):
        code = slot(0x18, 2, 3, -4, 123) + slot(0, 0, 0, 0, -456) + slot()
        expected = code[:4] + b'\0' * 4 + code[8:12] + b'\0' * 4 + code[16:]
        self.assertEqual(matcher.mask(code), expected)
        self.assertEqual(len(matcher.mask(code)), len(code))

    def test_lddw_continuation_is_not_decoded_as_another_opcode(self):
        # This mask is not a verifier: the second slot is opaque except its imm.
        code = slot(0x18, immediate=5) + slot(0x18, immediate=6)
        self.assertEqual(matcher.mask(code), code[:4] + b'\0' * 4 + code[8:12] + b'\0' * 4)

    def test_partial_instruction_slots_are_rejected(self):
        for length in range(1, 32):
            if length % 8:
                with self.subTest(length=length):
                    with self.assertRaisesRegex(ValueError, 'complete 8-byte'):
                        matcher.mask(b'\0' * length)

    def test_truncated_lddw_is_rejected_without_growing_input(self):
        for prefix in (b'', slot()):
            with self.subTest(prefix_length=len(prefix)):
                code = prefix + slot(0x18, immediate=1)
                before = bytes(code)
                with self.assertRaisesRegex(ValueError, 'truncated lddw'):
                    matcher.mask(code)
                self.assertEqual(code, before)


class AlignedMatchTests(unittest.TestCase):
    def test_all_overlapping_aligned_matches_are_reported(self):
        instruction = slot()
        self.assertEqual(matcher._aligned_matches(instruction * 2, instruction * 3), [0, 8])

    def test_unaligned_hit_does_not_hide_later_aligned_hits(self):
        self.assertEqual(matcher._aligned_matches(b'\0' * 8, b'\xff' * 4 + b'\0' * 20), [8, 16])

    def test_no_match_and_empty_haystack(self):
        for needle, haystack in ((slot(), b''), (slot() * 2, slot()), (slot(), b'\0' * 24)):
            with self.subTest(needle=needle, haystack=haystack):
                self.assertEqual(matcher._aligned_matches(needle, haystack), [])

    def test_empty_candidate_body_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'must not be empty'):
            matcher._aligned_matches(b'', slot())

    def test_only_raw_match_can_be_an_overlapping_masked_match(self):
        calls = [slot(0x85, 1, immediate=immediate) for immediate in (10, 20, 30)]
        original, candidate = b''.join(calls), b''.join(calls[1:])
        hits = matcher._aligned_matches(matcher.mask(candidate), matcher.mask(original))
        raw = [hit for hit in hits if original[hit:hit + len(candidate)] == candidate]
        self.assertEqual(hits, [0, 8])
        self.assertEqual(raw, [8])


class FunctionInstructionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.code = slot(0x18, dst=1, immediate=7) + slot(0, immediate=2) + slot()
        self.image = b'header!!' + self.code
        self.sections = {'.text': {'addr': 0x1000, 'offset': 8, 'size': len(self.code)}}

    def test_lddw_continuation_is_not_a_function_start(self):
        with self.assertRaisesRegex(ValueError, 'logical instruction boundary'):
            matcher.function_body(self.image, self.sections, 0x1008, 8)

    def test_function_end_cannot_split_lddw(self):
        with self.assertRaisesRegex(ValueError, 'logical instruction boundary'):
            matcher.function_body(self.image, self.sections, 0x1000, 8)

    def test_complete_lddw_and_following_function_are_unchanged(self):
        self.assertEqual(matcher.function_body(self.image, self.sections, 0x1000, 16), self.code[:16])
        self.assertEqual(matcher.function_body(self.image, self.sections, 0x1010, 8), self.code[16:])

    def test_changed_mutable_image_does_not_reuse_stale_boundaries(self):
        image = bytearray(self.image)
        image[8] = 0xb7
        self.assertEqual(matcher.function_body(image, self.sections, 0x1008, 8), self.code[8:16])
        image[8] = 0x18
        with self.assertRaisesRegex(ValueError, 'logical instruction boundary'):
            matcher.function_body(image, self.sections, 0x1008, 8)

    def test_truncated_enclosing_instruction_stream_is_rejected(self):
        image = self.image[:-8] + slot(0x18)
        with self.assertRaisesRegex(ValueError, 'truncated instruction'):
            matcher.function_body(image, self.sections, 0x1000, 16)


class BoundaryHelperProtectionTests(unittest.TestCase):
    def test_report_cannot_replace_the_logical_instruction_reader(self):
        helper = Path(matcher.instruction_boundaries.__code__.co_filename)
        before = helper.read_bytes()
        with self.assertRaisesRegex(ValueError, 'aliases an input'):
            matcher.protect_report_output(helper, [], 'not-executed')
        self.assertEqual(helper.read_bytes(), before)


class SyntheticMainTests(unittest.TestCase):
    def test_main_keeps_json_schema_and_reports_overlapping_raw_match(self):
        calls = [slot(0x85, 1, immediate=immediate) for immediate in (10, 20, 30)]
        original, candidate = b''.join(calls), b''.join(calls[1:])
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        candidate_path, original_path, output = (root / name for name in ('candidate', 'original', 'report.json'))
        candidate_path.write_bytes(candidate)
        original_path.write_bytes(original)
        args = argparse.Namespace(candidate=candidate_path,
                                  objdump='not-executed', pattern='quote_control', output=output)
        sections = [{'.text': {'addr': 0x100, 'offset': 0, 'size': len(original)}},
                    {'.text': {'addr': 0x200, 'offset': 0, 'size': len(candidate)}}]
        stdout = io.StringIO()
        with mock.patch.object(matcher.argparse.ArgumentParser, 'parse_args', return_value=args), \
                mock.patch.object(matcher, 'ORIGINAL', original_path), \
                mock.patch.object(matcher, 'sections', side_effect=sections), \
                mock.patch.object(matcher, 'candidate_functions', return_value=[(0x200, len(candidate), 'quote_control_synthetic')]), \
                mock.patch.object(matcher.subprocess, 'check_output', side_effect=AssertionError('no subprocess permitted')), \
                contextlib.redirect_stdout(stdout):
            matcher.main()
        report = json.loads(output.read_text())
        self.assertEqual(set(report), {'candidate', 'candidate_sha256', 'original_sha256', 'functions'})
        self.assertEqual(report['candidate'], str(candidate_path))
        self.assertEqual(report['candidate_sha256'], hashlib.sha256(candidate).hexdigest())
        self.assertEqual(report['original_sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(report['functions'], [{
            'symbol': 'quote_control_synthetic', 'size': len(candidate),
            'masked_matches': [0x100, 0x108], 'raw_matches': [0x108],
            'sha256': hashlib.sha256(candidate).hexdigest(),
        }])
        self.assertIn('masked=2 raw=1', stdout.getvalue())
        self.assertIn('1/1 functions have masked matches', stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
