"""Count all 64-bit shift forms without changing math-window selection."""
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from deep_section_analysis import Elf, analyze_math_patterns


class ShiftCountTests(unittest.TestCase):
    def test_real_capture_counts_and_unchanged_fields(self):
        evidence = json.loads(Path(__file__).with_name('evidence.json').read_text(encoding='utf-8'))
        for name, added, affected in [('pump', 44, 12), ('pump_amm', 43, 11),
                                      ('pump_fees', 38, 9), ('mayhem', 29, 9)]:
            with self.subTest(program=name):
                path = ROOT / 'evidence/original' / name / 'deployed.so'
                expected = evidence['captures'][name]
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected['sha256'])
                elf = Elf(path)
                report = analyze_math_patterns(elf)
                arithmetic = changed = total = logical = 0
                for row in report['math_intensive_windows']:
                    start = int(row['address'], 16)
                    at, shifts, arsh = start, 0, 0
                    while at < start + row['size']:
                        opcode = elf.b[at]
                        # Independently decode ALU64 class and operation field.
                        if opcode & 7 == 7 and opcode & 0xf0 in (0x60, 0x70, 0xc0):
                            shifts += 1
                            arsh += opcode & 0xf0 == 0xc0
                        at += 16 if opcode == 0x18 else 8
                    self.assertEqual(row['shifts'], shifts)
                    arithmetic += arsh
                    changed += bool(arsh)
                    logical += shifts - arsh
                    total += row.pop('shifts')
                self.assertEqual((arithmetic, changed), (added, affected))
                self.assertEqual(logical, expected['baseline_shifts'])
                self.assertEqual(total, expected['baseline_shifts'] + added)
                encoded = json.dumps(report, sort_keys=True, separators=(',', ':')).encode()
                self.assertEqual(hashlib.sha256(encoded).hexdigest(), expected['unrelated_report_sha256'])

    def test_opcode_controls(self):
        for opcode in (0x67, 0x6f, 0x77, 0x7f, 0xc7, 0xcf, 0xc4, 0xcc, 0xa7, 0x47):
            with self.subTest(opcode=hex(opcode)):
                # Five additions admit the window under the existing threshold.
                raw = b''.join(struct.pack('<BBhi', op, 0x21, 0, 1)
                               for op in [0x07] * 5 + [opcode, 0x95])
                elf = SimpleNamespace(b=raw, entries=[0], hi=len(raw), funcs=[])
                row = analyze_math_patterns(elf)['math_intensive_windows'][0]
                self.assertEqual(row['shifts'], int(opcode in (0x67, 0x6f, 0x77, 0x7f, 0xc7, 0xcf)))
                self.assertEqual(row['additions'], 5)
                self.assertEqual(row['likely_function'], 'mixed_logic')


if __name__ == '__main__':
    unittest.main()
