#!/usr/bin/env python3
"""Repeat the real Mayhem analysis with distinct hash seeds and output paths."""
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DisassemblyReproducibilityTests(unittest.TestCase):
    def test_packet_bytes_are_repeatable(self):
        with tempfile.TemporaryDirectory() as temporary:
            outputs = [Path(temporary) / 'first', Path(temporary) / 'nested/second']
            for index, output in enumerate(outputs):
                if index:
                    # gzip's default timestamp has one-second resolution.
                    time.sleep(1.1)
                env = dict(os.environ, PYTHONHASHSEED=str(index + 1),
                           PYTHONUTF8=str(index), PYTHONIOENCODING='utf-8')
                result = subprocess.run(
                    [sys.executable, str(ROOT / 'scripts/deep_disassembly.py'),
                     '--program', 'mayhem', '--output', str(output)],
                    cwd=ROOT, env=env, capture_output=True, timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                verified = subprocess.run(
                    [sys.executable, str(output / 'verify.py')],
                    cwd=ROOT, env=env, capture_output=True, timeout=30,
                )
                self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

            first, second = outputs
            files = sorted(path.name for path in first.iterdir())
            self.assertEqual(files, sorted([
                'README.md', 'disassembly.json.gz', 'dispatch-table.json',
                'error-strings.json', 'extern-usage.json', 'fingerprints.json',
                'manifest.json', 'rodata-strings.json', 'summary.json',
                'syscall-usage.json', 'verify.py', 'windows-deep.json',
            ]))
            self.assertEqual(files, sorted(path.name for path in second.iterdir()))
            for name in files:
                with self.subTest(file=name):
                    self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

            compressed = (first / 'disassembly.json.gz').read_bytes()
            self.assertEqual(compressed[3] & 0x08, 0)  # no original filename
            self.assertEqual(compressed[4:8], bytes(4))  # no creation time
            decoded = gzip.decompress(compressed)
            self.assertNotIn(b'\r\n', decoded)
            self.assertTrue(json.loads(decoded))
            for path in first.iterdir():
                if path.suffix != '.gz':
                    self.assertNotIn(b'\r\n', path.read_bytes())
            (first / 'README.md').read_bytes().decode('utf-8')


if __name__ == '__main__':
    unittest.main()
