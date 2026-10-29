"""Original-capture and negative controls for relocated data pointer analysis."""
import struct
import hashlib
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from deep_section_analysis import Elf, analyze_data_layout


class PointerAnalysisTests(unittest.TestCase):
    def test_saved_input_hashes(self):
        evidence = json.loads(Path(__file__).with_name('evidence.json').read_text())
        for path, expected in evidence['inputs'].items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)

    def test_original_captures(self):
        cases = [('pump', 163, 0x1bd738, 0xaef0),
                 ('pump_amm', 157, 0x1220f8, 0x9b20),
                 ('pump_fees', 111, 0xc8768, 0x9978),
                 ('mayhem', 67, 0xb1238, 0x7ed8)]
        for name, count, slot, target in cases:
            with self.subTest(name=name):
                elf = Elf(ROOT / 'evidence/original' / name / 'deployed.so')
                original = elf.b
                self.assertEqual(struct.unpack_from('<I', original, 48)[0], 0)
                report = analyze_data_layout(elf)['.data.rel.ro']
                self.assertEqual(report['pointer_count'], count)
                pointer = next(p for p in report['pointer_like_values']
                               if p['address'] == hex(slot))
                self.assertEqual(pointer['points_to'], hex(target))
                self.assertTrue(pointer['in_text'])
                self.assertEqual(pointer['raw_value'], hex(target << 32))
                self.assertEqual(pointer['relocation_type'], 8)
                self.assertEqual(elf.b, original)

    def test_versions_relocation_types_and_raw_pointers(self):
        for version in (0, 1, 2, 3, 4, 99):
            for relocation in (None, 1, 8, 10):
                with self.subTest(version=version, relocation=relocation):
                    blob = bytearray(80)
                    struct.pack_into('<I', blob, 48, version)
                    struct.pack_into('<QQ', blob, 64, 0x100 << 32, 0x108)
                    elf = SimpleNamespace(b=bytes(blob), lo=0x100, hi=0x200,
                        secs={'.data.rel.ro': (0, 1, 2, 64, 64, 16, 0, 0, 8, 0)},
                        relocations={} if relocation is None else {64: {'type': relocation}})
                    report = analyze_data_layout(elf)['.data.rel.ro']
                    resolved = version in (0, 1, 2) and relocation == 8
                    self.assertEqual(report['pointer_count'], 2 if resolved else 1)
                    raw = report['pointer_like_values'][-1]
                    self.assertEqual(raw['points_to'], '0x108')
                    self.assertNotIn('raw_value', raw)


if __name__ == '__main__':
    unittest.main()
