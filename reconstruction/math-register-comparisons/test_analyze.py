import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
from types import SimpleNamespace
import unittest
import tempfile
import analyze as adapter


class MathComparisonPatternTests(unittest.TestCase):
    helper = adapter.load_analysis()

    def analyze(self, instructions):
        # Keep the window above the analyzer's five-arithmetic-op threshold.
        prefix = struct.pack('<BBhi', 0x07, 1, 0, 1) * 4
        blob = prefix + b''.join(instructions)
        elf = SimpleNamespace(b=blob, entries=[0], hi=len(blob), funcs=[])
        return self.helper.analyze_math_patterns(elf)['math_intensive_windows'][0]

    def test_unsigned_comparisons_accept_immediate_and_register_forms(self):
        for arithmetic in (0x07, 0x0f, 0x17, 0x1f, 0x27, 0x2f):
            for comparison in (0x25, 0x2d, 0x35, 0x3d, 0xa5, 0xad, 0xb5, 0xbd):
                with self.subTest(arithmetic=hex(arithmetic), comparison=hex(comparison)):
                    report = self.analyze([
                        struct.pack('<BBhi', arithmetic, 0x21, 0, 1),
                        struct.pack('<BBhi', comparison, 0x31, 0, 0),
                    ])
                    self.assertEqual(report['overflow_checks'], 1)

    def test_unrelated_comparisons_and_intervening_instructions_stay_excluded(self):
        add = struct.pack('<BBhi', 0x07, 1, 0, 1)
        move = struct.pack('<BBhi', 0xb7, 2, 0, 1)
        for comparison in (0x15, 0x1d, 0x55, 0x5d, 0x65, 0x6d, 0xc5, 0xcd):
            with self.subTest(comparison=hex(comparison)):
                report = self.analyze([add, struct.pack('<BBhi', comparison, 0x31, 0, 0)])
                self.assertEqual(report['overflow_checks'], 0)
        report = self.analyze([add, move, struct.pack('<BBhi', 0x2d, 0x31, 0, 0)])
        self.assertEqual(report['overflow_checks'], 0)

    def test_captured_pump_subtract_compare_is_counted(self):
        # Pump file offset 0xd278: sub64 r1, r8; jge r1, r6, +7.
        blob = (adapter.ROOT / 'evidence/original/pump/deployed.so').read_bytes()
        pair = blob[0xd278:0xd288]
        self.assertEqual(pair.hex(), '1f810000000000003d61070000000000')
        self.assertEqual(self.analyze([pair])['overflow_checks'], 1)


class SourceAndCaptureTests(unittest.TestCase):
    def test_changed_source_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'changed.py'
            path.write_text('raise RuntimeError("must not execute")\n')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                adapter.load_analysis(path)

    def test_all_captured_math_windows_match_independent_opcode_census(self):
        old = adapter.load_analysis(corrected=False)
        new = adapter.load_analysis()
        expected = {'pump': (158, 310), 'pump_amm': (121, 196),
                    'pump_fees': (119, 187), 'mayhem': (92, 293)}
        for name, totals in expected.items():
            with self.subTest(program=name):
                elf = new.Elf(adapter.ROOT / 'evidence/original' / name / 'deployed.so')
                before = old.analyze_math_patterns(elf)
                after = new.analyze_math_patterns(elf)
                self.assertEqual(tuple(sum(w['overflow_checks'] for w in r['math_intensive_windows'])
                                       for r in (before, after)), totals)
                for left, right in zip(before['math_intensive_windows'], after['math_intensive_windows']):
                    start = int(left['address'], 16)
                    added = 0
                    for at in range(start + 8, start + left['size'], 8):
                        arithmetic, comparison = elf.b[at - 8], elf.b[at]
                        # Independently decode class/source/operation bit fields.
                        if (arithmetic & 7 == 7 and arithmetic & 0xf0 in (0, 0x10, 0x20)
                                and comparison & 15 == 13 and comparison & 0xf0 in (0x20, 0x30, 0xa0, 0xb0)):
                            added += 1
                    self.assertEqual(right['overflow_checks'] - left['overflow_checks'], added)
                    self.assertEqual({k: v for k, v in left.items() if k != 'overflow_checks'},
                                     {k: v for k, v in right.items() if k != 'overflow_checks'})
                self.assertEqual({k: v for k, v in before.items() if k not in ('math_intensive_windows', 'windows_with_overflow_checks')},
                                 {k: v for k, v in after.items() if k not in ('math_intensive_windows', 'windows_with_overflow_checks')})

    def test_cli_preserves_an_existing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.json'
            path.write_bytes(b'prior evidence')
            result = subprocess.run([sys.executable, str(Path(adapter.__file__)), '--program', 'pump',
                                     '--output', str(path)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_bytes(), b'prior evidence')



if __name__ == "__main__":
    unittest.main()
