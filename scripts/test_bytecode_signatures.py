#!/usr/bin/env python3
"""Relocation-aware syscall recognition in bytecode_signatures.py."""
import pathlib
import struct
import unittest
from types import SimpleNamespace

import bytecode_signatures
from window_elf_reader import Elf


class RelocatedSyscallTests(unittest.TestCase):
    def sites(self, elf, symbol):
        return sum(
            1 for at, rel in elf.relocations.items()
            if rel.get('type') == 10 and rel.get('symbol') == symbol
            and elf.lo <= at < elf.hi
        )

    def test_hash_immediate_syscalls_still_count(self):
        blob = bytearray(8)
        blob[0] = 0x85
        struct.pack_into('<I', blob, 4, 0xe4042040)
        elf = SimpleNamespace(b=bytes(blob), relocations={})
        found = bytecode_signatures.detect_cpi_patterns(elf, 0, 8)
        self.assertEqual([row['syscall'] for row in found], ['sol_invoke_signed_rust'])
        struct.pack_into('<I', blob, 4, 0xa22b9c85)
        elf.b = bytes(blob)
        self.assertEqual(
            bytecode_signatures.detect_serialization_patterns(elf, 0, 8)['memcpy_calls'],
            1,
        )

    def test_relocated_invoke_is_cpi_and_log_is_not(self):
        blob = bytearray(8)
        blob[0] = 0x85
        blob[1] = 0x10
        struct.pack_into('<i', blob, 4, -1)
        elf = SimpleNamespace(
            b=bytes(blob),
            relocations={0: {'type': 10, 'symbol': 'sol_invoke_signed_rust'}},
        )
        found = bytecode_signatures.detect_cpi_patterns(elf, 0, 8)
        self.assertEqual(found[0]['syscall'], 'sol_invoke_signed_rust')
        elf.relocations[0]['symbol'] = 'sol_log_'
        self.assertEqual(bytecode_signatures.detect_cpi_patterns(elf, 0, 8), [])
        self.assertEqual(
            bytecode_signatures.detect_serialization_patterns(elf, 0, 8)['memcpy_calls'],
            0,
        )
        elf.relocations[0]['symbol'] = 'sol_memcpy_'
        self.assertEqual(
            bytecode_signatures.detect_serialization_patterns(elf, 0, 8)['memcpy_calls'],
            1,
        )
        elf.relocations[0]['type'] = 8
        self.assertEqual(
            bytecode_signatures.detect_serialization_patterns(elf, 0, 8)['memcpy_calls'],
            0,
        )

    def test_captured_syscall_sites_match_the_relocation_table(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        expected = {
            'pump': ('sol_invoke_signed_rust', 1, 'sol_memcpy_', 2),
            'pump_amm': ('sol_invoke_signed_rust', 1, 'sol_memcpy_', 2),
            'pump_fees': ('sol_invoke_signed_rust', 1, 'sol_memcpy_', 2),
            'mayhem': ('sol_invoke_signed_rust', 1, 'sol_memcpy_', 2),
        }
        for name, (invoke_name, invoke_n, copy_name, copy_n) in expected.items():
            elf = Elf(root / 'evidence/original' / name / 'deployed.so')
            self.assertEqual(self.sites(elf, invoke_name), invoke_n, name)
            self.assertEqual(self.sites(elf, copy_name), copy_n, name)
            self.assertEqual(
                len(bytecode_signatures.detect_cpi_patterns(elf, elf.lo, elf.hi)),
                invoke_n,
                name,
            )
            self.assertEqual(
                bytecode_signatures.detect_serialization_patterns(elf, elf.lo, elf.hi)['memcpy_calls'],
                copy_n,
                name,
            )


if __name__ == '__main__':
    unittest.main()
