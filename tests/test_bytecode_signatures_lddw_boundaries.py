"""Logical SBF instruction boundary and relocation regressions for scripts/bytecode_signatures.py."""
from pathlib import Path
import struct
import sys
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import bytecode_signatures  # noqa: E402


def insn(opcode, regs=0, off=0, imm=0):
    return struct.pack('<BBhi', opcode, regs, off, imm)


def lddw_raw(regs, imm_lo, second_slot_bytes):
    assert len(second_slot_bytes) == 8
    return struct.pack('<BBhI', 0x18, regs, 0, imm_lo) + second_slot_bytes


class BytecodeSignaturesBoundaryTests(unittest.TestCase):
    def test_lddw_second_slot_does_not_spoof_cpi_or_setup_stores(self):
        fake_invoke_slot = struct.pack('<BBhI', 0x85, 0x00, 0, 0xd7449092)
        blob = lddw_raw(0x01, 1, fake_invoke_slot)
        elf = SimpleNamespace(b=blob, relocations={})
        self.assertEqual(bytecode_signatures.detect_cpi_patterns(elf, 0, len(blob)), [])

        # Real CPI call preceded by an lddw whose second slot starts with 0x7b (stxdw)
        # and one real stxdw instruction.
        fake_store_slot = insn(0x7b, 0x1a, -8, 0)
        real_store = insn(0x7b, 0x2a, -16, 0)
        real_invoke = struct.pack('<BBhI', 0x85, 0x00, 0, 0xd7449092)
        blob2 = lddw_raw(0x01, 42, fake_store_slot) + real_store + real_invoke
        elf2 = SimpleNamespace(b=blob2, relocations={})
        cpis = bytecode_signatures.detect_cpi_patterns(elf2, 0, len(blob2))
        self.assertEqual(len(cpis), 1)
        self.assertEqual(cpis[0]['offset'], 24)
        self.assertEqual(cpis[0]['setup_stores'], 1)

    def test_lddw_second_slot_does_not_spoof_serialization_stores_or_memcpy(self):
        real_store = insn(0x7b, 0x1a, -8, 0)
        fake_store_slot = insn(0x7b, 0x1a, -16, 0)
        fake_memcpy_slot = struct.pack('<BBhI', 0x85, 0x00, 0, 0x717cc4a3)
        blob = (
            real_store * 3
            + lddw_raw(0x01, 1, fake_store_slot)
            + lddw_raw(0x02, 2, fake_memcpy_slot)
        )
        elf = SimpleNamespace(b=blob, relocations={})
        result = bytecode_signatures.detect_serialization_patterns(elf, 0, len(blob))
        self.assertEqual(result['sequential_stores'], 3)
        self.assertEqual(result['max_store_run'], 3)
        self.assertEqual(result['memcpy_calls'], 0)
        self.assertFalse(result['likely_serialization'])

    def test_lddw_second_slot_and_truncated_tail_do_not_spoof_account_validation(self):
        fake_disc_load = insn(0x79, 0x12, 0, 0)
        jeq_after = insn(0x15, 0x01, 0, 7)
        fake_owner_load = insn(0x79, 0x12, 32, 0)
        blob = (
            lddw_raw(0x01, 1, fake_disc_load)
            + jeq_after
            + lddw_raw(0x02, 2, fake_owner_load)
            + insn(0x79, 0x12, 0, 0)
            + b'\x15'
        )
        elf = SimpleNamespace(b=blob, relocations={})
        result = bytecode_signatures.detect_account_validation(elf, 0, len(blob))
        self.assertEqual(result['discriminator_checks'], 0)
        self.assertEqual(result['owner_field_accesses'], 0)
        self.assertFalse(result['likely_account_validation'])

    def test_token_transfer_patterns_bounds_lddw_window_and_skips_relocations(self):
        # 1. Truncated trailing 0x18 at EOF must not raise struct.error.
        eof_truncated = struct.pack('<BBhI', 0x18, 0x01, 0, 3)
        elf_eof = SimpleNamespace(b=eof_truncated, relocations={})
        self.assertEqual(
            bytecode_signatures.detect_token_transfer_patterns(elf_eof, 0, 8),
            [],
        )

        # 2. 0x18 at end - 8 must not read imm_hi across end into the next window.
        bleed_blob = struct.pack('<BBhI', 0x18, 0x01, 0, 3) + struct.pack('<BBhI', 0x00, 0, 0, 0)
        elf_bleed = SimpleNamespace(b=bleed_blob, relocations={})
        self.assertEqual(
            bytecode_signatures.detect_token_transfer_patterns(elf_bleed, 0, 8),
            [],
        )
        # A complete scalar is not the 32-byte token-program constant.
        self.assertEqual(
            bytecode_signatures.detect_token_transfer_patterns(elf_bleed, 0, 16),
            [],
        )

        token = bytecode_signatures.TOKEN_PROGRAMS['Tokenkeg']
        complete = b''.join(lddw_raw(1, int.from_bytes(token[i:i + 4], 'little'),
                                    bytes(4) + token[i + 4:i + 8])
                            for i in range(0, 32, 8))
        elf_complete = SimpleNamespace(b=complete, relocations={})
        self.assertEqual(len(bytecode_signatures.detect_token_transfer_patterns(
            elf_complete, 0, len(complete))), 1)
        self.assertEqual(bytecode_signatures.detect_token_transfer_patterns(
            elf_complete, 0, len(complete) - 8), [])

        # 3. Relocated lddw carries an address/symbol addend, not a literal chunk.
        elf_reloc = SimpleNamespace(
            b=complete,
            relocations={0: {'type': 8, 'symbol': ''}},
        )
        self.assertEqual(
            bytecode_signatures.detect_token_transfer_patterns(elf_reloc, 0, len(complete)),
            [],
        )

        # 4. Malformed lddw second slot starting with 0x18 must not be decoded as a nested lddw.
        nested_blob = (
            lddw_raw(0x01, 99, struct.pack('<BBhI', 0x18, 0x01, 0, 3))
            + struct.pack('<BBhI', 0x00, 0, 0, 0)
        )
        elf_nested = SimpleNamespace(b=nested_blob, relocations={})
        self.assertEqual(
            bytecode_signatures.detect_token_transfer_patterns(elf_nested, 0, len(nested_blob)),
            [],
        )

    def test_error_patterns_and_ngrams_respect_logical_instruction_bounds(self):
        # Branch at 0 with branch_off=1 targets offset 16, which is the second slot of lddw at 8..24.
        fake_mov_slot = insn(0xb7, 0x00, 0, 6001)
        blob = insn(0x15, 0x01, 1, 0) + lddw_raw(0x02, 123, fake_mov_slot)
        elf = SimpleNamespace(b=blob, relocations={})
        self.assertEqual(bytecode_signatures.detect_error_patterns(elf, 0, len(blob)), [])

        # Branch targeting a truncated 4-byte tail starting with 0xb7 at EOF must not unpack out of bounds.
        truncated_target = insn(0x15, 0x01, 0, 0) + b'\xb7\x00\x00\x00'
        elf_trunc = SimpleNamespace(b=truncated_target, relocations={})
        self.assertEqual(
            bytecode_signatures.detect_error_patterns(elf_trunc, 0, len(truncated_target)),
            [],
        )

        # Truncated trailing 0x18 at end - 8 is not a complete lddw instruction.
        trunc_lddw = insn(0xb7, 0x01, 0, 1) + struct.pack('<BBhI', 0x18, 0x02, 0, 5)
        _, opcodes = bytecode_signatures.extract_opcode_ngrams(
            SimpleNamespace(b=trunc_lddw, relocations={}), 0, len(trunc_lddw), n=1
        )
        self.assertEqual(opcodes, [0xb7])


if __name__ == '__main__':
    unittest.main()
