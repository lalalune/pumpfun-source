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


class HarnessSymbolNameTests(unittest.TestCase):
    def test_retained_impl_symbols_drop_only_the_compiler_escape_prefix(self):
        import json
        from pathlib import Path
        import shutil
        import subprocess
        import sys
        import tempfile

        repo = Path(__file__).resolve().parents[1]
        baseline = json.loads((repo / 'reconstruction/pump-main/baseline/score.json').read_text(encoding='utf-8'))
        symbols = baseline['windows']['288']['symbols']
        self.assertEqual(len(symbols), 2)
        # Load the actual analyzer in an isolated layout. On Windows git may
        # materialize original.so as link text; copy its real capture target.
        with tempfile.TemporaryDirectory(prefix='pump-symbol-names-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-symbol-names-'))
            (root / 'harness').mkdir()
            (root / 'base').mkdir()
            for name in ['win.py', 'score.py']:
                shutil.copyfile(repo / 'reconstruction/harness' / name, root / 'harness' / name)
            shutil.copyfile(repo / 'evidence/original/pump/deployed.so', root / 'base/original.so')
            result = subprocess.run(
                [sys.executable, '-B', '-c',
                 'import json,sys;sys.path.insert(0,sys.argv[1]);import win;'
                 'print(json.dumps([win.demangle(s) for s in json.load(sys.stdin)]))',
                 str(root / 'harness')],
                input=json.dumps([*symbols, '_ZN15__STATIC_FMTSTRE', '_ZN4testE', 'ordinary_symbol']),
                capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            names = json.loads(result.stdout)
            self.assertEqual(names[0], '<anchor_lang::accounts::interface::Interface<T> as anchor_lang::Accounts<B>>::try_accounts')
            self.assertEqual(names[1], '<anchor_lang::accounts::signer::Signer as anchor_lang::Accounts<B>>::try_accounts')
            self.assertRegex(names[0], r'^<anchor_lang::accounts::interface::Interface<T> ')
            self.assertEqual(names[2:], ['__STATIC_FMTSTR', 'test', 'ordinary_symbol'])


if __name__=='__main__': unittest.main()
