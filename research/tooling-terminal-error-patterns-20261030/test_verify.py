"""Regression controls for terminal branch candidates."""
import json
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import proof


class ErrorPatternBoundaryTests(unittest.TestCase):
    @staticmethod
    def instruction(opcode, offset=0, immediate=0):
        return struct.pack('<BBhi', opcode, 0, offset, immediate)

    def patterns(self, blob, start=0, end=None):
        return proof.detect_error_patterns(
            SimpleNamespace(b=blob), start, len(blob) if end is None else end)

    def test_two_instruction_window(self):
        blob = self.instruction(0x15) + self.instruction(0xb7, immediate=6000)
        self.assertEqual(self.patterns(blob), [{
            'offset': 0, 'branch_target_offset': 8,
            'error_code': 6000, 'type': 'conditional_error',
        }])

    def test_final_instruction_can_branch_backward(self):
        blob = self.instruction(0xb4, immediate=6001) + self.instruction(0x55, offset=-2)
        self.assertEqual(self.patterns(blob), [{
            'offset': 8, 'branch_target_offset': 0,
            'error_code': 6001, 'type': 'conditional_error',
        }])

    def test_target_must_be_a_complete_instruction_inside_window(self):
        blob = self.instruction(0x15) + self.instruction(0xb7, immediate=6000)
        for end in (8, 9, 12, 15):
            with self.subTest(end=end):
                self.assertEqual(self.patterns(blob, end=end), [])
        backward = self.instruction(0xb7) + self.instruction(0x15, offset=-2)
        self.assertEqual(self.patterns(backward, start=8), [])

    def test_empty_and_partial_branch_windows(self):
        self.assertEqual(self.patterns(b''), [])
        self.assertEqual(self.patterns(self.instruction(0x15)[:4]), [])

    def test_non_move_target_is_not_a_pattern(self):
        blob = self.instruction(0x15) + self.instruction(0x95)
        self.assertEqual(self.patterns(blob), [])

    def test_terminal_branches_in_captured_programs(self):
        cases = (
            ('pump', 0xef40, 0xefc8, 0xefb8, 0xef58),
            ('pump', 0x197650, 0x197868, 0x197858, 0x197788),
            ('pump_amm', 0xd038, 0xd0c0, 0xd0b0, 0xd050),
            ('mayhem', 0x9028, 0x92b8, 0x92a8, 0x9260),
        )
        for name, start, end, branch, target in cases:
            with self.subTest(program=name, branch=hex(branch)):
                blob = (proof.REPO / 'evidence/original' / name / 'deployed.so').read_bytes()
                self.assertIn({
                    'offset': branch - start, 'branch_target_offset': target - start,
                    'error_code': 0, 'type': 'conditional_error',
                }, self.patterns(blob, start, end))



class EvidenceTests(unittest.TestCase):
    def test_changed_source_is_rejected_before_loading(self):
        with patch.object(proof.Path, 'read_bytes', return_value=b'changed source'):
            with self.assertRaisesRegex(ValueError, 'bound input changed: scripts/bytecode_signatures.py'):
                proof.reviewed()

    def test_archived_detector_still_reproduces_omission(self):
        blob = ErrorPatternBoundaryTests.instruction(0x15) + ErrorPatternBoundaryTests.instruction(0xb7, immediate=6000)
        self.assertEqual(proof.reviewed().detect_error_patterns(SimpleNamespace(b=blob), 0, len(blob)), [])

    def test_full_corpus_matches_saved_observations(self):
        self.assertEqual(proof.check(), json.loads((proof.P / 'observations.json').read_text(encoding='utf-8')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
