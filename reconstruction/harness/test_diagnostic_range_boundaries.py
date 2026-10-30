"""Exercise diagnostic CLIs against a retained deployed ELF, without tool mocks."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
HARNESS = Path(__file__).resolve().parent
CAPTURE = ROOT / 'evidence/original/pump_fees/deployed.so'
LDDW = 0x438


class DiagnosticRangeBoundaryTests(unittest.TestCase):
    def run_tool(self, tool, start, size):
        command = [sys.executable, '-B', str(HARNESS / (tool + '.py'))]
        if tool == 'control_flow':
            command += [str(CAPTURE), '--start', hex(start), '--size', str(size)]
        else:
            for side in ('original', 'candidate'):
                command += ['--' + side, str(CAPTURE), '--' + side + '-start', hex(start),
                            '--' + side + '-bytes', str(size)]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def test_capture_has_the_expected_two_slot_instruction(self):
        blob = CAPTURE.read_bytes()
        self.assertEqual(blob[LDDW], 0x18)
        self.assertEqual(blob[LDDW + 8:LDDW + 16], bytes(8))

    def test_clis_reject_starting_in_captured_lddw_continuation(self):
        for tool in ('stack_access', 'control_flow'):
            with self.subTest(tool=tool):
                result = self.run_tool(tool, LDDW + 8, 8)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('logical instruction boundary', result.stderr)
                self.assertEqual(result.stdout, '')

    def test_clis_reject_cutting_off_captured_lddw(self):
        for tool in ('stack_access', 'control_flow'):
            with self.subTest(tool=tool):
                result = self.run_tool(tool, LDDW, 8)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('truncated', result.stderr)
                self.assertEqual(result.stdout, '')

    def test_complete_lddw_and_following_instruction_remain_accepted(self):
        for tool in ('stack_access', 'control_flow'):
            for start, size in ((LDDW, 16), (LDDW + 16, 8)):
                with self.subTest(tool=tool, start=start):
                    result = self.run_tool(tool, start, size)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = json.loads(result.stdout)
                    if tool == 'control_flow':
                        self.assertEqual(report['instruction_count'], 1)
                    else:
                        self.assertEqual(report['differences'], [])

    def test_enclosing_origin_and_incomplete_end_are_checked(self):
        from instruction_stream import require_instruction_range
        raw = b'\x18' + bytes(15) + b'\x95' + bytes(7)
        require_instruction_range(raw, 0, 16)
        require_instruction_range(raw, 16, 8)
        for start, size in ((8, 8), (0, 8), (-8, 8), (0, 0), (16, 16)):
            with self.subTest(start=start, size=size), self.assertRaises(ValueError):
                require_instruction_range(raw, start, size)


if __name__ == '__main__':
    unittest.main()
