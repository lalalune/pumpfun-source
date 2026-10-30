"""Static corruption controls for the maintained Mayhem ELF identity boundary."""
import json
from pathlib import Path
import tempfile
import unittest

from analyze import elf_layout
from verify_mayhem_checkpoint import ROOT, verify_meaningful_elf


class MayhemMeaningfulElfIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        capture = ROOT/'evidence/original/mayhem'
        cls.original = (capture/'deployed.so').read_bytes()
        cls.receipt = json.loads((capture/'capture.json').read_text())
        cls.extent = elf_layout(cls.original)['elf_extent']

    def check(self, candidate, original=None, receipt=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = root/'evidence/original/mayhem'
            capture.mkdir(parents=True)
            (capture/'deployed.so').write_bytes(self.original if original is None else original)
            (capture/'capture.json').write_text(json.dumps(self.receipt if receipt is None else receipt))
            selected = root/'candidate.so'
            selected.write_bytes(candidate)
            return verify_meaningful_elf(root, selected)

    def test_retained_capture_prefix_defines_the_boundary(self):
        result = self.check(self.original[:self.extent])
        self.assertEqual(result['meaningful_elf_bytes'], 775416)
        self.assertEqual(result['excluded_zero_allocation_tail_bytes'], 1992)

    def test_candidate_corruption_and_appended_tail_are_rejected(self):
        candidate = bytearray(self.original[:self.extent])
        candidate[512] ^= 1
        for bad in (bytes(candidate), self.original):
            with self.subTest(length=len(bad)), self.assertRaisesRegex(ValueError, 'selected meaningful ELF bytes'):
                self.check(bad)

    def test_capture_corruption_and_receipt_substitution_are_rejected(self):
        original = bytearray(self.original)
        original[512] ^= 1
        with self.assertRaisesRegex(ValueError, 'captured payload identity'):
            self.check(self.original[:self.extent], original=bytes(original))
        forged = dict(self.receipt, payload_sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'captured payload identity'):
            self.check(self.original[:self.extent], receipt=forged)


if __name__ == '__main__':
    unittest.main()
