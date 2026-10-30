#!/usr/bin/env python3
"""Mutation tests ensuring the byte comparator cannot hide code/padding changes."""
import tempfile
import unittest
from pathlib import Path
import compare as compare_module
import struct
import unittest
from types import SimpleNamespace
import deep_disassembly
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import deep_section_analysis
import analyze
from compare import compare
from test_pump_diagnostic_audit import DiagnosticMetadataTests
class ComparisonTests(unittest.TestCase):
    def test_equal(self): self.assertTrue(compare(b'abc\0\0',b'abc\0\0')['full_byte_equality'])
    def test_code_mutation(self): self.assertEqual(compare(b'abc\0\0',b'axc\0\0')['first_difference'],1)
    def test_padding_mutation(self): self.assertEqual(compare(b'abc\0\0',b'abc\0x')['first_difference'],4)
    def test_truncated_padding(self): self.assertFalse(compare(b'abc\0\0',b'abc\0')['full_byte_equality'])
    def test_extended_padding(self): self.assertFalse(compare(b'abc\0',b'abc\0\0')['full_byte_equality'])
    def test_empty(self): self.assertEqual(compare(b'a',b'')['first_difference'],0)


class CompareProgramNamesTests(unittest.TestCase):
    def test_program_names_fall_back_to_captures(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = root / 'evidence/original/probe'
            capture.mkdir(parents=True)
            (capture / 'deployed.so').write_bytes(b'ELF')
            self.assertEqual(compare_module.program_names(root), ['probe'])


class RodataStringAddressTests(unittest.TestCase):
    def test_string_keys_use_virtual_address(self):
        blob = bytearray(0x40)
        blob[0x20:0x24] = b'TEST'
        elf = SimpleNamespace(
            b=bytes(blob),
            secs={'.rodata': (0, 1, 2, 0x1000, 0x20, 0x10, 0, 0, 1, 0)},
        )
        strings = deep_disassembly.extract_rodata_strings(elf)
        self.assertEqual(strings[0x1000], 'TEST')
        self.assertNotIn(0x20, strings)


class DataLayoutAddressTests(unittest.TestCase):
    def test_string_address_uses_virtual_address(self):
        blob = bytearray(0x40)
        blob[0x20:0x24] = b'TEST'
        elf = SimpleNamespace(
            b=bytes(blob),
            lo=0x2000,
            hi=0x3000,
            secs={'.rodata': (0, 1, 2, 0x1000, 0x20, 0x10, 0, 0, 1, 0)},
        )
        report = deep_section_analysis.analyze_data_layout(elf)
        self.assertEqual(report['.rodata']['strings'][0]['address'], '0x1000')
class SectionTerminalStringTests(unittest.TestCase):
    def test_terminal_strings_match_delimited_strings(self):
        for section in ('.rodata', '.data.rel.ro'):
            for text in (b'abcd', b'x' * 240):
                with self.subTest(section=section, length=len(text)):
                    def report(data):
                        elf = SimpleNamespace(
                            b=b'!' * 16 + data, lo=0x1000, hi=0x2000,
                            secs={section: (0, 1, 2, 16, 16, len(data), 0, 0, 1, 0)},
                        )
                        return deep_section_analysis.analyze_data_layout(elf)[section]
                    terminal = report(b'\0' + text)
                    delimited = report(b'\0' + text + b'\0')
                    self.assertEqual(terminal['strings'], delimited['strings'])
                    self.assertEqual(terminal['string_count'], 1)
                    self.assertEqual(terminal['strings'][0]['length'], len(text))
                    self.assertEqual(terminal['strings'][0]['value'], text.decode()[:200])

    def test_short_terminal_run_is_ignored(self):
        elf = SimpleNamespace(b=b'abc', lo=0x1000, hi=0x2000,
            secs={'.rodata': (0, 1, 2, 0, 0, 3, 0, 0, 1, 0)})
        self.assertEqual(deep_section_analysis.analyze_data_layout(elf)['.rodata']['strings'], [])


class RelocationTargetTests(unittest.TestCase):
    def test_target_section_uses_address_not_file_offset(self):
        blob = bytearray(64)
        struct.pack_into('<QQ', blob, 0, 0x1000, 2)
        elf = SimpleNamespace(
            b=bytes(blob),
            symbols={},
            lo=0x2000,
            hi=0x3000,
            secs={
                '.rel.dyn': (0, 9, 0, 0, 0, 16, 0, 0, 1, 16),
                '.rodata': (0, 1, 2, 0x1000, 0x20, 0x100, 0, 0, 1, 0),
            },
        )
        report = deep_section_analysis.analyze_relocations(elf)
        self.assertEqual(report['entries'][0]['target_section'], '.rodata')


class InstructionLogNameTests(unittest.TestCase):
    def test_idl_names_are_independent_of_locale_encoding(self):
        original_open = Path.open
        for program in ('pump', 'pump_amm', 'pump_fees'):
            expected = analyze.known_instruction_names(program)
            self.assertIn('Buy' if program != 'pump_fees' else 'Withdraw', expected)
            for locale_encoding in ('ascii', 'cp1252', 'cp936'):
                with self.subTest(program=program, encoding=locale_encoding):
                    def locale_open(path, mode='r', buffering=-1, encoding=None,
                                    errors=None, newline=None):
                        # Emulate a non-UTF-8 host for implicit text reads only.
                        if 'b' not in mode and encoding in (None, 'locale'):
                            encoding = locale_encoding
                        return original_open(path, mode, buffering, encoding,
                                             errors, newline)

                    with patch.object(Path, 'open', locale_open):
                        self.assertEqual(analyze.known_instruction_names(program), expected)

    def names(self, name):
        blob = (analyze.ROOT / 'evidence/original' / name / 'deployed.so').read_bytes()
        return set(analyze.instruction_log_names(blob, analyze.known_instruction_names(name)))

    def test_idl_names_do_not_absorb_adjacent_text(self):
        pump = self.names('pump')
        self.assertIn('Buy', pump)
        self.assertIn('UpdateBuybackConfig', pump)
        self.assertIn('IdlResizeAccount', pump)
        self.assertNotIn('BuyCreateV2Disabled', pump)
        self.assertNotIn('UpdateBuybackConfigAn', pump)
        self.assertNotIn('IdlResizeAccountdata', pump)

        amm = self.names('pump_amm')
        self.assertIn('ClaimCashback', amm)
        self.assertIn('IdlCreateAccount', amm)
        self.assertNotIn('ClaimCashbacksol', amm)
        self.assertNotIn('IdlCreateAccountanchor', amm)

        fees = self.names('pump_fees')
        self.assertIn('Withdraw', fees)
        self.assertIn('CrankDonationFeePda', fees)
        self.assertNotIn('Withdrawaccountsol', fees)
        self.assertNotIn('CrankDonationFeePdaFee', fees)

    def test_program_names_fall_back_to_captures(self):
        self.assertEqual(
            analyze.program_names(),
            ['pump', 'pump_amm', 'pump_fees', 'mayhem'],
        )

    def test_program_addresses_fall_back_to_captures(self):
        # Matches the archived repro/programs.json removed in fce9f28.
        self.assertEqual(
            analyze.program_addresses(),
            {
                'pump': '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P',
                'pump_amm': 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA',
                'pump_fees': 'pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ',
                'mayhem': 'MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e',
            },
        )

    def test_mayhem_fallback_is_unchanged(self):
        names = self.names('mayhem')
        self.assertEqual(len(names), 25)
        self.assertIn('Buy', names)
        self.assertIn('InitializeGlobalParams', names)


class SbpfInventoryInputTests(unittest.TestCase):
    def test_inputs_fall_back_to_captured_originals(self):
        import tempfile
        from pathlib import Path
        from sbpf_disassembly_inventory import program_inputs
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'evidence/original/pump').mkdir(parents=True)
            (root / 'evidence/original/pump/deployed.so').write_bytes(b'ELF')
            (root / 'evidence/original/no-binary').mkdir()
            self.assertEqual(
                program_inputs(root),
                [('pump', root / 'evidence/original/pump/deployed.so')],
            )

    def test_selector_mapping_still_wins(self):
        import tempfile
        from pathlib import Path
        from sbpf_disassembly_inventory import program_inputs
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'repro').mkdir()
            (root / 'repro/programs.json').write_text('{"pump": "address"}')
            (root / 'evidence/original/pump').mkdir(parents=True)
            (root / 'evidence/original/pump/deployed.so').write_bytes(b'ELF')
            self.assertEqual(
                program_inputs(root)[0][1],
                root / 'evidence/original/pump/deployed.so',
            )


if __name__=='__main__': unittest.main()
