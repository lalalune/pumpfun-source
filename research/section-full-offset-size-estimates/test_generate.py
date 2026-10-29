from collections import defaultdict
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import generate


class FullOffsetEstimateTests(unittest.TestCase):
    def test_all_original_estimates_use_all_matching_load_offsets(self):
        module = generate.corrected_module()
        import deep_section_analysis as archived
        from window_elf_reader import Elf
        for program, expected_changes in [('pump', 3), ('pump_amm', 3), ('mayhem', 7)]:
            with self.subTest(program=program):
                elf = Elf(generate.ROOT / f'evidence/original/{program}/deployed.so')
                before, after = archived.recover_anchor_idl(elf), module.recover_anchor_idl(elf)
                groups, expected_sizes = {}, set()
                for start, end in zip(elf.entries, elf.entries[1:] + [elf.hi]):
                    offsets = defaultdict(list)
                    for at in range(start, end, 8):
                        if elf.b[at] in (0x61, 0x69, 0x71, 0x79):
                            offsets[elf.b[at+1] >> 4].append(struct.unpack_from('<h', elf.b, at+2)[0])
                    for register, values in offsets.items():
                        unique = sorted(set(values))
                        if len(unique) >= 3 and all(1 <= b-a <= 32 for a, b in zip(unique[:5], unique[1:6])):
                            groups[(hex(start), register)] = unique
                            if max(unique) + 8 > 0:
                                expected_sizes.add(max(unique) + 8)
                changes = 0
                for old, new in zip(before['deserialization_patterns'], after['deserialization_patterns']):
                    self.assertEqual({k:v for k,v in old.items() if k != 'likely_struct_size'}, {k:v for k,v in new.items() if k != 'likely_struct_size'})
                    offsets = groups[(new['window'], new['base_reg'])]
                    self.assertEqual(new['likely_struct_size'], max(offsets) + 8)
                    self.assertLessEqual(len(new['field_offsets']), 20)
                    changes += old['likely_struct_size'] != new['likely_struct_size']
                self.assertEqual(changes, expected_changes)
                self.assertEqual(after['inferred_struct_sizes'], sorted(expected_sizes))
                for key in before.keys() - {'deserialization_patterns', 'inferred_struct_sizes'}:
                    self.assertEqual(before[key], after[key])

    def test_reviewed_checkout_forms_and_source_drift(self):
        raw = generate.SOURCE.read_bytes().replace(b'\r\n', b'\n')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.py'
            with patch.object(generate, 'SOURCE', path):
                for data in (raw, raw.replace(b'\n', b'\r\n')):
                    path.write_bytes(data)
                    self.assertTrue(callable(generate.corrected_module().recover_anchor_idl))
                path.write_bytes(raw + b'\n# drift\n')
                with self.assertRaisesRegex(ValueError, 'reviewed section-analysis source'):
                    generate.corrected_module()


if __name__ == '__main__':
    unittest.main()
