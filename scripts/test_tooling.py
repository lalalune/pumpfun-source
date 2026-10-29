#!/usr/bin/env python3
"""Mutation tests ensuring the byte comparator cannot hide code/padding changes."""
import struct
import unittest
from types import SimpleNamespace
import deep_section_analysis
import analyze
from compare import compare
class ComparisonTests(unittest.TestCase):
    def test_equal(self): self.assertTrue(compare(b'abc\0\0',b'abc\0\0')['full_byte_equality'])
    def test_code_mutation(self): self.assertEqual(compare(b'abc\0\0',b'axc\0\0')['first_difference'],1)
    def test_padding_mutation(self): self.assertEqual(compare(b'abc\0\0',b'abc\0x')['first_difference'],4)
    def test_truncated_padding(self): self.assertFalse(compare(b'abc\0\0',b'abc\0')['full_byte_equality'])
    def test_extended_padding(self): self.assertFalse(compare(b'abc\0',b'abc\0\0')['full_byte_equality'])
    def test_empty(self): self.assertEqual(compare(b'a',b'')['first_difference'],0)


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

    def test_mayhem_fallback_is_unchanged(self):
        names = self.names('mayhem')
        self.assertEqual(len(names), 25)
        self.assertIn('Buy', names)
        self.assertIn('InitializeGlobalParams', names)


class SourceCoordinatePairingTests(unittest.TestCase):
    def test_cli_keeps_reused_source_descriptors_at_their_own_lines(self):
        import json
        from pathlib import Path
        import shutil
        import subprocess
        import sys
        import tempfile

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='pump-coordinate-pairing-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-coordinate-pairing-'))
            (root / 'harness').mkdir()
            (root / 'base').mkdir()
            for name in ['coords.py', 'score.py']:
                shutil.copyfile(repo / 'reconstruction/harness' / name, root / 'harness' / name)
            shutil.copyfile(repo / 'evidence/original/pump/deployed.so', root / 'base/original.so')
            shutil.copyfile(repo / 'reconstruction/base/functions.tsv', root / 'base/functions.tsv')
            result = subprocess.run(
                [sys.executable, '-B', '-X', 'utf8', str(root / 'harness/coords.py'), 'window', '0x18678'],
                capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            sites = {site['slot']: site for site in json.loads(result.stdout)}
            for length_slot, line_slot, line in [(4296, 4288, 466), (4520, 4512, 493)]:
                self.assertEqual(sites[length_slot]['path'], 'programs/pump/src/create_v2.rs')
                self.assertEqual(sites[length_slot]['line_slot'], line_slot)
                self.assertEqual(sites[length_slot]['line'], line)


if __name__=='__main__': unittest.main()
