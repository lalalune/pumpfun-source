"""Host-architecture code must not be decoded as a legacy SBF instruction stream."""
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


class ControlFlowMachineTests(unittest.TestCase):
    def run_cli(self, root, machine):
        image = fixture()
        struct.pack_into('<H', image, 18, machine)
        candidate, output = root / 'candidate.so', root / 'cfg.json'
        candidate.write_bytes(image)
        result = subprocess.run([sys.executable, '-B', str(H / 'control_flow.py'), str(candidate),
                                 '--start', '0x1000', '--size', '16', '--json', str(output)],
                                capture_output=True, text=True)
        return result, output

    def test_host_machines_are_refused(self):
        for machine in (0, 3, 40, 62, 183):
            with self.subTest(machine=machine), tempfile.TemporaryDirectory() as temporary:
                result, output = self.run_cli(Path(temporary), machine)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn('EM_BPF or EM_SBPF', result.stderr)
                self.assertFalse(output.exists())

    def test_sbf_machines_still_decode(self):
        for machine in (247, 263):
            with self.subTest(machine=machine), tempfile.TemporaryDirectory() as temporary:
                result, output = self.run_cli(Path(temporary), machine)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['start'], 0x1000)


if __name__ == '__main__':
    unittest.main()
