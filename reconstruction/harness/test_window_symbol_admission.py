import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_elf_symbols import fixture
from test_support import copy_harness_modules


class WindowSymbolAdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        harness, base = self.root / 'harness', self.root / 'base'
        harness.mkdir()
        base.mkdir()
        copy_harness_modules(harness)
        (base / 'original.so').write_bytes(bytes(fixture()))
        (base / 'functions.tsv').write_text(
            'program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n', encoding='utf-8')
        self.candidate = self.root / 'candidate.so'
        self.script = harness / 'win.py'

    def sym(self, regex):
        return subprocess.run([sys.executable, str(self.script), 'sym', regex, '--cand', str(self.candidate)],
                              capture_output=True, text=True)

    def test_stripped_candidate_is_refused_instead_of_listing_nothing(self):
        image = fixture()
        struct.pack_into('<I', image, 64 + 4 * 64 + 4, 11)  # the fixture's only symtab becomes a dynsym
        self.candidate.write_bytes(image)
        result = self.sym('.')
        self.assertEqual(result.returncode, 1, 'a stripped candidate has no symbols to search')
        self.assertEqual(result.stdout, '')
        self.assertIn('no function symbols', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_symbolized_candidate_without_a_match_stays_an_empty_listing(self):
        self.candidate.write_bytes(bytes(fixture()))
        result = self.sym('no_such_symbol')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
