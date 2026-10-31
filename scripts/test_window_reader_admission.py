"""Mutate owned copies; captured program bytes are never changed or executed."""
from pathlib import Path
import struct
import tempfile
import unittest
from window_elf_reader import Elf


class ReaderAdmission(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def test_rejects_inconsistent_relocation_headers(self):
        for program in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
            source = self.root / f'evidence/original/{program}/deployed.so'
            admitted = Elf(source)
            table = struct.unpack_from('<Q', admitted.b, 40)[0]
            header = table + admitted.raw.index(admitted.secs['.rel.dyn']) * 64
            changes = (
                ('section type', header + 4, '<I', 1),
                ('entry size', header + 56, '<Q', 8),
                ('out-of-range link', header + 40, '<I', len(admitted.raw)),
                ('non-symbol-table link', header + 40, '<I',
                 admitted.raw.index(admitted.text)),
            )
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'mutated.so'
                for label, offset, fmt, value in changes:
                    with self.subTest(program=program, field=label):
                        raw = bytearray(admitted.b)
                        struct.pack_into(fmt, raw, offset, value)
                        path.write_bytes(raw)
                        with self.assertRaisesRegex(ValueError, 'relocation'):
                            Elf(path)

    def test_rejects_relocation_symbol_outside_linked_table(self):
        source = self.root / 'evidence/original/pump/deployed.so'
        admitted = Elf(source)
        section = admitted.secs['.rel.dyn']
        linked = admitted.raw[section[6]]
        position = next(pos for pos in range(section[4], section[4] + section[5], 16)
                        if struct.unpack_from('<Q', admitted.b, pos + 8)[0] & 0xffffffff == 10)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'mutated.so'
            raw = bytearray(admitted.b)
            struct.pack_into('<Q', raw, position + 8, ((linked[5] // 24) << 32) | 10)
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'relocation.*symbol'):
                Elf(path)

    def test_rejects_inconsistent_machine_text_and_name_tables(self):
        original = (self.root / 'evidence/original/pump/deployed.so').read_bytes()
        admitted = Elf(self.root / 'evidence/original/pump/deployed.so')
        table = struct.unpack_from('<Q', original, 40)[0]
        name_index = struct.unpack_from('<H', original, 62)[0]
        text_index = admitted.raw.index(admitted.text)
        symbol_index = admitted.raw.index(admitted.secs['.dynsym'])
        symbol = admitted.secs['.dynsym']
        changes = [
            ('foreign machine', 18, '<H', 62),
            ('non-executable text', table + text_index * 64 + 8, '<Q', 2),
            ('non-PROGBITS text', table + text_index * 64 + 4, '<I', 3),
            ('name table type', table + name_index * 64 + 4, '<I', 1),
            ('name out of bounds', table + text_index * 64, '<I', 0xffffffff),
            ('symbol entry size', table + symbol_index * 64 + 56, '<Q', 8),
            ('symbol strings type', table + symbol[6] * 64 + 4, '<I', 1),
            ('symbol name out of bounds', symbol[4], '<I', 0xffffffff),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'mutated.so'
            for label, offset, fmt, value in changes:
                with self.subTest(label=label):
                    raw = bytearray(original)
                    struct.pack_into(fmt, raw, offset, value)
                    path.write_bytes(raw)
                    with self.assertRaises(ValueError): Elf(path)

    def test_all_retained_programs_still_load(self):
        for name in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
            with self.subTest(name=name):
                elf = Elf(self.root / 'evidence/original' / name / 'deployed.so')
                self.assertGreater(elf.hi, elf.lo)
                self.assertTrue(elf.entries)


if __name__ == '__main__': unittest.main()
