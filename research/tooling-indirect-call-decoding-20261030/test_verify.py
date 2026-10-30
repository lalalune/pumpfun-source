"""Real captured CALL_REG instructions and version-specific operand controls."""
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from deep_disassembly import decode_instruction, Elf


class IndirectCallTests(unittest.TestCase):
    def test_captured_indirect_calls(self):
        for name, expected in [('pump', 144), ('pump_amm', 123),
                               ('pump_fees', 121), ('mayhem', 93)]:
            with self.subTest(program=name):
                elf = Elf(ROOT / 'evidence/original' / name / 'deployed.so')
                self.assertEqual(struct.unpack_from('<I', elf.b, 48)[0], 0)
                at, count = elf.lo, 0
                while at < elf.hi:
                    step = 16 if elf.b[at] == 0x18 else 8
                    if elf.b[at] == 0x8d:
                        register = struct.unpack_from('<i', elf.b, at + 4)[0]
                        insn, size = decode_instruction(elf.b, at, elf)
                        self.assertEqual(size, 8)
                        self.assertEqual(insn['mnemonic'], f'callx r{register}')
                        self.assertEqual(insn['indirect_call_register'], register)
                        self.assertNotIn('call_target', insn)
                        self.assertNotIn('syscall', insn)
                        self.assertNotIn('extern_symbol', insn)
                        self.assertEqual(insn['hex'], elf.b[at:at+8].hex())
                        count += 1
                    at += step
                self.assertEqual(count, expected)

    def test_version_specific_register_field(self):
        for flags, expected in [(0, 2), (1, 2), (2, 3), (3, 4), (4, 4), (99, None)]:
            with self.subTest(flags=flags):
                blob = bytearray(72)
                struct.pack_into('<I', blob, 48, flags)
                struct.pack_into('<BBhi', blob, 64, 0x8d, 0x34, 0, 2)
                elf = SimpleNamespace(b=bytes(blob))
                insn, size = decode_instruction(elf.b, 64, elf)
                self.assertEqual(size, 8)
                if expected is None:
                    self.assertTrue(insn['mnemonic'].startswith('raw_0x8d'))
                    self.assertNotIn('indirect_call_register', insn)
                else:
                    self.assertEqual(insn['mnemonic'], f'callx r{expected}')
                    self.assertEqual(insn['indirect_call_register'], expected)

    def test_missing_version_stays_unresolved(self):
        blob = struct.pack('<BBhi', 0x8d, 0, 0, 2)
        insn, _ = decode_instruction(blob, 0, SimpleNamespace())
        self.assertTrue(insn['mnemonic'].startswith('raw_0x8d'))
        self.assertNotIn('indirect_call_register', insn)

    def test_invalid_register_stays_unresolved(self):
        for flags, regs, imm in [(0, 0, -1), (1, 0, 258), (2, 0xf0, 2), (3, 0x0f, 2)]:
            with self.subTest(flags=flags, regs=regs, imm=imm):
                blob = bytearray(72)
                struct.pack_into('<I', blob, 48, flags)
                struct.pack_into('<BBhi', blob, 64, 0x8d, regs, 0, imm)
                insn, _ = decode_instruction(bytes(blob), 64, SimpleNamespace(b=bytes(blob)))
                self.assertTrue(insn['mnemonic'].startswith('raw_0x8d'))
                self.assertNotIn('indirect_call_register', insn)


if __name__ == '__main__':
    unittest.main()
