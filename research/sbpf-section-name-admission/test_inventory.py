"""Reject ambiguous section-name lookups in disassembly evidence tooling."""
from pathlib import Path
import struct
import unittest
import tempfile

import inventory

sections = inventory.load_inventory().sections


def elf_with_names(names):
    """Build an ELF64 image with separate, complete named section payloads."""
    strings = b'\0.shstrtab\0'
    offsets = []
    for name in names:
        offsets.append(len(strings))
        strings += name.encode() + b'\0'
    count = 2 + len(names)
    table = 64
    names_at = table + count * 64
    payload_at = names_at + len(strings)
    image = bytearray(payload_at + 8 * len(names))
    image[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHI', image, 16, 3, 247, 1)
    struct.pack_into('<H', image, 52, 64)
    struct.pack_into('<Q', image, 40, table)
    struct.pack_into('<HHH', image, 58, 64, count, 1)
    struct.pack_into('<IIQQQQIIQQ', image, table + 64,
                     1, 3, 0, 0, names_at, len(strings), 0, 0, 1, 0)
    image[names_at:payload_at] = strings
    for i, offset in enumerate(offsets):
        struct.pack_into('<IIQQQQIIQQ', image, table + (i + 2) * 64,
                         offset, 1, 6, 0x1000 + i * 8,
                         payload_at + i * 8, 8, 0, 0, 8, 0)
        image[payload_at + i * 8:payload_at + (i + 1) * 8] = bytes([i + 1]) * 8
    return bytes(image)


class SectionNameTests(unittest.TestCase):
    def test_duplicate_text_cannot_hide_an_earlier_body(self):
        image = elf_with_names(['.text', '.text'])
        with self.assertRaisesRegex(ValueError, 'duplicate section names'):
            sections(image)

    def test_duplicate_data_name_is_also_ambiguous(self):
        with self.assertRaisesRegex(ValueError, 'duplicate section names'):
            sections(elf_with_names(['.text', '.rodata', '.rodata']))

    def test_unique_names_preserve_each_payload(self):
        image = elf_with_names(['.text', '.rodata'])
        result = sections(image)
        self.assertEqual(set(result), {'', '.shstrtab', '.text', '.rodata'})
        for i, name in enumerate(['.text', '.rodata']):
            row = result[name]
            self.assertEqual(image[row[4]:row[4] + row[5]], bytes([i + 1]) * 8)

    def test_changed_archived_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'scripts/sbpf_disassembly_inventory.py'
            path.parent.mkdir()
            path.write_text('raise RuntimeError("must not execute")\n')
            with self.assertRaisesRegex(ValueError, 'source drift'):
                inventory.load_inventory(root)

    def test_inventory_rejects_duplicate_before_invoking_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'duplicate.so'
            image = elf_with_names(['.text', '.text'])
            path.write_bytes(image)
            with self.assertRaisesRegex(ValueError, 'duplicate section names'):
                inventory.load_inventory().inventory(root / 'absent-tool', 'fixture', path, root)
            self.assertEqual(path.read_bytes(), image)
            self.assertEqual(list(root.iterdir()), [path])

    def test_retained_capture_tables_are_unambiguous(self):
        root = Path(__file__).resolve().parents[2]
        paths = sorted((root / 'evidence').glob('**/deployed.so'))
        self.assertTrue(paths, 'retained ELF captures are required')
        for path in paths:
            with self.subTest(path=path.relative_to(root)):
                image = path.read_bytes()
                result = sections(image)
                self.assertIn('.text', result)
                count = struct.unpack_from('<H', image, 60)[0]
                self.assertEqual(len(result), count)


if __name__ == '__main__':
    unittest.main()
