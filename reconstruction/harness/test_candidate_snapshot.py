"""Replace an actual ELF path between the diagnostic loader's reads."""
import struct
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from elf_symbols import function_symbols
from test_elf_symbols import fixture
import win


class CandidateSnapshotTests(unittest.TestCase):
    def test_replacement_cannot_mix_old_bytes_with_new_symbols(self):
        first = bytes(fixture())
        second = bytearray(first)
        struct.pack_into('<Q', second, 504 + 8, 0x1008)
        self.assertNotEqual(function_symbols(first), function_symbols(second))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'candidate.so'
            path.write_bytes(first)
            read = Path.read_bytes
            replaced = False
            def replace_after_read(current):
                nonlocal replaced
                data = read(current)
                if current == path and not replaced:
                    replaced = True
                    path.write_bytes(second)
                return data
            with patch.object(Path, 'read_bytes', replace_after_read):
                candidate = win.Cand(path)
            self.assertEqual(path.read_bytes(), second)
            self.assertEqual(candidate.blob, first)
            self.assertEqual(candidate.funcs, function_symbols(first))
            path.unlink()
            self.assertEqual(candidate.fn(0x1000, 8), first[424:432])


if __name__ == '__main__': unittest.main()
