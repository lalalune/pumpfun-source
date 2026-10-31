"""Host-architecture code must not be compared as legacy SBF stack accesses."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

from test_elf_symbols import fixture


class StackAccessMachineTests(unittest.TestCase):
    def run_cli(self, root, machine):
        image = fixture()
        struct.pack_into('<H', image, 18, machine)
        candidate = root / 'candidate.so'
        candidate.write_bytes(image)
        return subprocess.run([sys.executable, '-B', str(H / 'stack_access.py'),
                               '--original', str(candidate), '--original-start', '0x1000',
                               '--original-bytes', '16',
                               '--candidate', str(candidate), '--candidate-start', '0x1000',
                               '--candidate-bytes', '16'],
                              capture_output=True, text=True)

    def test_host_machines_are_refused(self):
        for machine in (0, 3, 40, 62, 183):
            with self.subTest(machine=machine), tempfile.TemporaryDirectory() as temporary:
                result = self.run_cli(Path(temporary), machine)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn('EM_BPF or EM_SBPF', result.stderr)
                self.assertEqual(result.stdout, '')

    def test_sbf_machines_still_compare(self):
        for machine in (247, 263):
            with self.subTest(machine=machine), tempfile.TemporaryDirectory() as temporary:
                result = self.run_cli(Path(temporary), machine)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(json.loads(result.stdout)['decoded_access_sequence_equal'])


if __name__ == '__main__':
    unittest.main()
