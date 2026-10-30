"""Exercise ISA admission through the real stack-access comparison CLI."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from test_elf_symbols import fixture
from score_admission import sections


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name('stack_access.py')


class StackAccessISATests(unittest.TestCase):
    def cli(self, original, candidate, start=0x1000, size=16):
        return subprocess.run(
            [sys.executable, '-B', str(SCRIPT),
             '--original', str(original), '--original-start', str(start),
             '--original-bytes', str(size), '--candidate', str(candidate),
             '--candidate-start', str(start), '--candidate-bytes', str(size)],
            cwd=ROOT, capture_output=True, text=True, timeout=30)

    def test_unsupported_versions_reject_either_input_before_reporting(self):
        for version in (2, 3, 4, 32):
            for side in ('original', 'candidate'):
                with self.subTest(version=version, side=side), \
                        tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    legacy = fixture()
                    legacy[424:440] = (struct.pack('<BBhi', 0x7b, 0x1a, -8, 0)
                                       + struct.pack('<BBhi', 0x79, 0xa0, -8, 0))
                    unsupported = bytearray(legacy)
                    struct.pack_into('<I', unsupported, 48, version)
                    if version == 2:
                        # SBPFv2 store/load opcodes occupy ALU classes. A
                        # legacy decoder silently reports no accesses here.
                        unsupported[424:440] = (struct.pack('<BBhi', 0x9f, 0x1a, -8, 0)
                                                + struct.pack('<BBhi', 0x9c, 0xa0, -8, 0))
                    original, candidate = root / 'original.so', root / 'candidate.so'
                    original.write_bytes(unsupported if side == 'original' else legacy)
                    candidate.write_bytes(unsupported if side == 'candidate' else legacy)
                    before = [path.read_bytes() for path in (original, candidate)]
                    result = self.cli(original, candidate)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn('SBPFv0/v1', result.stderr)
                    self.assertEqual(result.stdout, '')
                    self.assertEqual([path.read_bytes() for path in (original, candidate)], before)

    def test_legacy_versions_keep_their_stack_access_results(self):
        for version in (0, 1):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
                image = fixture()
                struct.pack_into('<I', image, 48, version)
                image[424:440] = (struct.pack('<BBhi', 0x7b, 0x1a, -8, 0)
                                  + struct.pack('<BBhi', 0x79, 0xa0, -8, 0))
                path = Path(temporary) / 'legacy.so'
                path.write_bytes(image)
                result = self.cli(path, path)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report['differences'], [])
                self.assertEqual([(row['kind'], row['offset'], row['width'])
                                  for row in report['original']['accesses']],
                                 [('write', -8, 8), ('read', -8, 8)])
                self.assertEqual(path.read_bytes(), image)

    def test_all_nine_captured_images_remain_accepted(self):
        paths = sorted((ROOT / 'evidence').glob('*/*/deployed.so'))
        self.assertEqual(len(paths), 9)
        with tempfile.TemporaryDirectory() as temporary:
            for index, source in enumerate(paths):
                with self.subTest(program=source.parent.name):
                    image = source.read_bytes()
                    # Copy the real image; the diagnostic must leave it intact.
                    path = Path(temporary) / f'{index}.so'
                    path.write_bytes(image)
                    text = sections(image)['.text']
                    size = 16 if image[text['offset']] == 0x18 else 8
                    result = self.cli(path, path, text['addr'], size)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report['differences'], [])
                    self.assertEqual(report['original_input']['sha256'],
                                     hashlib.sha256(image).hexdigest())
                    self.assertEqual(path.read_bytes(), image)


if __name__ == '__main__':
    unittest.main()
