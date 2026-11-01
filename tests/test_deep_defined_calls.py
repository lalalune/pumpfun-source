"""Defined dynamic symbols reach the complete disassembly reports as internal calls."""
import copy
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import deep_disassembly as deep
from window_elf_reader import Elf
from test_deep_elf_coordinates import image

spec = importlib.util.spec_from_file_location('defined_calls_probe',
    ROOT / 'research/deep-defined-calls-20261101/probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class DefinedDynamicCallTests(unittest.TestCase):
    def retained(self, program='mayhem'):
        group = 'dependencies' if program == 'donation_relay' else 'original'
        elf = Elf(ROOT / 'evidence' / group / program / 'deployed.so')
        row = probe.raw_calls(elf.b)['defined'][0]
        return elf, row

    def test_actual_symbols_resolve_and_leave_matching_inputs_unchanged(self):
        for program in probe.PROGRAMS:
            with self.subTest(program=program):
                elf, row = self.retained(program)
                before = (elf.b, elf.normalized, list(elf.entries), dict(elf.calls),
                          elf.pattern(elf.lo, elf.hi - elf.lo))
                at, target = int(row['call_offset'], 16), int(row['target_offset'], 16)
                record, width = deep.decode_instruction(elf.b, at, elf)
                self.assertEqual(width, 8)
                self.assertEqual(record['call_target'], target)
                self.assertEqual(record['call_name'], row['symbol'])
                self.assertEqual(record['mnemonic'], 'call ' + row['symbol'])
                self.assertEqual(record['extern_symbol'], row['symbol'])
                self.assertNotIn('syscall', record)
                after = (elf.b, elf.normalized, list(elf.entries), dict(elf.calls),
                         elf.pattern(elf.lo, elf.hi - elf.lo))
                self.assertEqual(before, after)

    def test_unadmitted_symbol_metadata_does_not_become_an_internal_target(self):
        original, row = self.retained()
        at = int(row['call_offset'], 16)
        symbol_at = original.secs['.dynsym'][4] + row['symbol_index'] * 24
        changes = {'undefined': (6, '<H', 0), 'not_function': (4, '<B', 0x11),
                   'zero_value': (8, '<Q', 0), 'zero_size': (16, '<Q', 0),
                   'outside_text': (8, '<Q', original.text[3] + original.text[5]),
                   'interior_target': (8, '<Q', int(row['symbol_value'], 16) + 8),
                   'partial_extent': (16, '<Q', row['symbol_size'] - 1)}
        for name, (offset, encoding, value) in changes.items():
            with self.subTest(case=name):
                elf = copy.copy(original)
                data = bytearray(elf.b)
                struct.pack_into(encoding, data, symbol_at + offset, value)
                elf.b = bytes(data)
                record, _ = deep.decode_instruction(elf.b, at, elf)
                self.assertNotIn('call_target', record)
                self.assertNotIn('call_name', record)
                # Bounded unresolved/fallback behavior remains available.
                self.assertEqual(record['extern_symbol'], row['symbol'])

    def test_actual_undefined_symbols_keep_the_existing_external_behavior(self):
        elf, defined = self.retained()
        defined_at = int(defined['call_offset'], 16)
        for at, relocation in elf.relocations.items():
            if relocation['type'] != 10 or at == defined_at:
                continue
            record, _ = deep.decode_instruction(elf.b, at, elf)
            self.assertEqual(record['extern_symbol'], relocation['symbol'])
            self.assertNotIn('call_target', record)
        self.assertIsNone(deep.relocated_syscalls(elf)[defined_at])

    def test_unadmitted_relocation_table_link_does_not_borrow_a_definition(self):
        original, row = self.retained()
        elf = copy.copy(original)
        elf.secs = dict(original.secs)
        relocation = list(elf.secs['.rel.dyn'])
        relocation[6] = original.raw.index(original.text)
        elf.secs['.rel.dyn'] = tuple(relocation)
        self.assertEqual(deep.defined_dynamic_calls(elf), {})
        record, _ = deep.decode_instruction(elf.b, int(row['call_offset'], 16), elf)
        self.assertNotIn('call_target', record)
        self.assertEqual(record['extern_symbol'], row['symbol'])

    def test_other_defined_names_and_nonidentity_coordinates_are_resolved(self):
        # Supplemental structural control; primary proof uses retained captures.
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'coordinates.so'
            for address in (0x100, 0x1000):
                with self.subTest(text_address=address):
                    path.write_bytes(image(address))
                    elf = Elf(path)
                    data = bytearray(elf.b)
                    # The existing fixture's symbol 2 defines the handler at +40.
                    struct.pack_into('<Q', data, elf.secs['.rel.dyn'][4] + 8,
                                     (2 << 32) | 10)
                    path.write_bytes(data)
                    elf = Elf(path)
                    record, _ = deep.decode_instruction(elf.b, 0x118, elf)
                    self.assertEqual(record['call_target'], 0x128)
                    self.assertEqual(record['call_name'], 'handler')
                    self.assertEqual(record['mnemonic'], 'call handler')
                    self.assertEqual(record['extern_symbol'], 'handler')

    def test_defined_function_at_zero_virtual_address_is_admitted(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'zero-address.so'
            path.write_bytes(image(0))
            elf = Elf(path)
            data = bytearray(elf.b)
            # Entry is a complete positive-size STT_FUNC in .text at VA zero.
            struct.pack_into('<Q', data, elf.secs['.rel.dyn'][4] + 8, (1 << 32) | 10)
            path.write_bytes(data)
            elf = Elf(path)
            record, _ = deep.decode_instruction(elf.b, 0x118, elf)
            self.assertEqual(record['call_target'], 0x100)
            self.assertEqual(record['call_name'], 'entry')
            self.assertEqual(record['extern_symbol'], 'entry')

    def test_complete_cli_reclassifies_only_the_five_retained_defined_calls(self):
        report = probe.collect(ROOT, expected='fixed')
        self.assertTrue(report['all_input_bytes_preserved'])
        for row in report['programs'].values():
            self.assertEqual(row['generated_verifier_exit'], 0)
            self.assertEqual(len(row['raw']['defined']), 1)
            self.assertEqual(row['summary']['total_internal_calls'], row['raw']['direct_calls'] + 1)
            self.assertEqual(row['summary']['total_extern_calls'], row['raw']['dynamic_calls'] - 1)
            if 'analyzer' in row:
                self.assertEqual(row['analyzer']['generated_verifier_exit'], 0)
                self.assertEqual(row['analyzer']['total_call_edges'], row['raw']['direct_calls'] + 1)
                self.assertEqual(len(row['analyzer']['defined_edges']), 1)


if __name__ == '__main__':
    unittest.main()
