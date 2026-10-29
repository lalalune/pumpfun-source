#!/usr/bin/env python3
"""Mutation tests ensuring the byte comparator cannot hide code/padding changes."""
import struct
import unittest
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import deep_section_analysis
import analyze
from compare import compare


class RevalidationReportTests(unittest.TestCase):
    def test_real_audit_requires_every_available_packet_check(self):
        repo = Path(__file__).resolve().parents[1]
        source = (repo / 'evidence/upstream/pump.json').read_bytes()
        address = json.loads(source)['address']
        with tempfile.TemporaryDirectory(prefix='pump-revalidation-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-revalidation-'))
            (root / 'scripts').mkdir()
            shutil.copyfile(repo / 'scripts/revalidate_all.py', root / 'scripts/revalidate_all.py')
            for name in ['both-pass', 'manifest-fails', 'verifier-fails',
                         'manifest-parse-error', 'manifest-only', 'verifier-only', 'neither']:
                packet = root / 'research' / name
                packet.mkdir(parents=True)
                (packet / 'pump.json').write_bytes(source)
                (packet / 'notes.txt').write_text('recorded notes', encoding='utf-8')
                if name not in ['verifier-only', 'neither']:
                    manifest = {file: hashlib.sha256((packet / file).read_bytes()).hexdigest()
                                for file in ['pump.json', 'notes.txt']}
                    (packet / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                if name not in ['manifest-only', 'neither']:
                    # Independently check the real retained IDL's program address.
                    (packet / 'verify.py').write_text(
                        'import json\nfrom pathlib import Path\n'
                        'data = json.loads(Path("pump.json").read_text(encoding="utf-8"))\n'
                        f'raise SystemExit(0 if data["address"] == {address!r} else 3)\n',
                        encoding='utf-8')
                if name == 'manifest-fails':
                    (packet / 'notes.txt').write_text('changed notes', encoding='utf-8')
                if name == 'verifier-fails':
                    data = json.loads(source)
                    data['address'] = 'different program'
                    (packet / 'pump.json').write_text(json.dumps(data), encoding='utf-8')
                    manifest['pump.json'] = hashlib.sha256((packet / 'pump.json').read_bytes()).hexdigest()
                    (packet / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                if name == 'manifest-parse-error':
                    (packet / 'manifest.json').write_text('{', encoding='utf-8')
            output = root / 'audit'
            result = subprocess.run([sys.executable, '-B', str(root / 'scripts/revalidate_all.py'),
                                     '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            rows = {row['packet']: row for row in json.loads((output / 'results.json').read_text(encoding='utf-8'))}
            self.assertEqual(rows['manifest-fails']['manifest_check']['status'], 'fail')
            self.assertEqual(rows['manifest-fails']['verify_check']['status'], 'pass')
            self.assertEqual(rows['verifier-fails']['manifest_check']['status'], 'pass')
            self.assertEqual(rows['verifier-fails']['verify_check']['status'], 'fail')
            for name in ['manifest-fails', 'verifier-fails', 'manifest-parse-error']:
                self.assertEqual(rows[name]['overall'], 'fail', name)
            for name in ['both-pass', 'manifest-only', 'verifier-only']:
                self.assertEqual(rows[name]['overall'], 'pass', name)
            self.assertEqual(rows['neither']['overall'], 'no_verification')
            summary = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
            self.assertEqual((summary['pass'], summary['fail'], summary['skip_or_inconclusive']), (3, 3, 1))
            self.assertEqual(set(json.loads((output / 'failed.json').read_text(encoding='utf-8'))),
                             {'manifest-fails', 'verifier-fails', 'manifest-parse-error'})
            # The generated audit's own integrity verifier still succeeds.
            verified = subprocess.run([sys.executable, '-B', str(output / 'verify.py')],
                                      capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
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


if __name__=='__main__': unittest.main()
