"""Real CLI attribution and interval-boundary controls."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import deep_disassembly as disasm


class StringReferenceTests(unittest.TestCase):
    def test_real_cli_packets(self):
        for name, expected in [('pump', 2482), ('pump_amm', 1770),
                               ('pump_fees', 1163), ('mayhem', 894)]:
            with self.subTest(program=name), tempfile.TemporaryDirectory() as directory:
                env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONHASHSEED': '1'}
                run = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/deep_disassembly.py'),
                    '--program', name, '--output', directory], env=env, capture_output=True)
                self.assertEqual(run.returncode, 0, run.stderr.decode('utf-8', errors='replace'))
                rows = json.loads((Path(directory) / 'windows-deep.json').read_text(encoding='utf-8'))
                references = [r for w in rows for r in w['string_references']]
                self.assertEqual(len(references), expected)
                self.assertTrue(all(len(r['string']) <= 120 for r in references))
                elf = disasm.Elf(ROOT / 'evidence/original' / name / 'deployed.so')
                strings = disasm.extract_rodata_strings(elf)
                by_site = {w['address_decimal'] + r['offset']: r['string']
                           for w in rows for r in w['string_references']}
                exact = 0
                for site, preview in by_site.items():
                    self.assertEqual(elf.b[site], 0x18)
                    target = (struct.unpack_from('<I', elf.b, site + 4)[0]
                              | struct.unpack_from('<I', elf.b, site + 12)[0] << 32)
                    if target in strings:
                        exact += 1
                        self.assertEqual(preview, strings[target][:120])
                    else:
                        self.assertEqual(elf.relocations[site]['type'], 8)
                    self.assertEqual(elf.b[target:target + len(preview)], preview.encode('ascii'))
                self.assertEqual(exact, {'pump': 114, 'pump_amm': 135, 'pump_fees': 79, 'mayhem': 29}[name])
                if name == 'mayhem':
                    sites = {w['address_decimal'] + r['offset']: r['string']
                             for w in rows for r in w['string_references']}
                    self.assertEqual(sites[0x36c8], 'true')
                    self.assertEqual(sites[0x36e0], 'false')
                    elf = disasm.Elf(ROOT / 'evidence/original/mayhem/deployed.so')
                    self.assertEqual(elf.relocations[0x36c8]['type'], 8)
                    self.assertEqual(elf.relocations[0x36e0]['type'], 8)
                verify = subprocess.run([sys.executable, '-B', str(Path(directory) / 'verify.py')],
                                        env=env, capture_output=True)
                self.assertEqual(verify.returncode, 0, verify.stderr)

    def test_interval_bounds(self):
        strings = {100: 'prefixtrue', 120: 'next'}
        starts = sorted(strings)
        expected = {99: None, 100: 'prefixtrue', 106: 'true', 109: 'e',
                    110: None, 119: None, 120: 'next', 123: 't', 124: None}
        for address, preview in expected.items():
            with self.subTest(address=address):
                self.assertEqual(disasm.rodata_string_preview(strings, starts, address), preview)
        self.assertIsNone(disasm.rodata_string_preview({}, [], 100))
        self.assertEqual(disasm.rodata_string_preview({0: 'a' * 200}, [0], 10), 'a' * 120)
        # The map's address domain is opaque: the pending virtual-address key
        # correction composes without another conversion here.
        shifted = {start + 0x1000: text for start, text in strings.items()}
        self.assertEqual(disasm.rodata_string_preview(shifted, sorted(shifted), 0x1000 + 106), 'true')


if __name__ == '__main__':
    unittest.main()
