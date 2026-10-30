#!/usr/bin/env python3
"""Mutation tests ensuring the byte comparator cannot hide code/padding changes."""
import json
import pathlib
import struct


import contextlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


from pathlib import Path
import compare as compare_module
import struct
import sys
import unittest
from test_analysis_interface_inventory import InterfaceInventoryEncodingTests
from types import SimpleNamespace
import deep_disassembly
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import deep_section_analysis
import deep_disassembly
import analyze
import local_validation
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


class ControlFlowJumpTests(unittest.TestCase):
    def edges(self, opcode, branch_offset=0):
        blob = bytes(16) + struct.pack('<BBhi', opcode, 0, branch_offset, 0)
        insn, _ = deep_disassembly.decode_instruction(blob, 16, SimpleNamespace())
        return deep_disassembly.build_cfg_edges([insn], 0, len(blob))

    def test_unconditional_forward_and_backward_jumps_have_one_edge(self):
        for branch_offset in (0, 2, -2):
            with self.subTest(branch_offset=branch_offset):
                self.assertEqual(self.edges(0x05, branch_offset), [{
                    'from': '0x10', 'to': hex(24 + branch_offset * 8),
                    'type': 'branch', 'conditional': False,
                }])

    def test_conditional_jumps_keep_both_edges(self):
        for opcode in (0x15, 0x1d, 0x55, 0x5d):
            with self.subTest(opcode=hex(opcode)):
                self.assertEqual(self.edges(opcode, -2), [
                    {'from': '0x10', 'to': '0x8', 'type': 'branch', 'conditional': True},
                    {'from': '0x10', 'to': '0x18', 'type': 'fallthrough', 'conditional': False},
                ])

    def test_exit_and_non_branch_behavior_is_unchanged(self):
        self.assertEqual(self.edges(0x95), [{
            'from': '0x10', 'to': 'return', 'type': 'exit', 'conditional': False,
        }])
        self.assertEqual(self.edges(0xb7), [])

    def test_captured_unconditional_jumps_have_no_fallthrough(self):
        for name in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
            with self.subTest(program=name):
                elf = deep_disassembly.Elf(
                    analyze.ROOT / 'evidence/original' / name / 'deployed.so')
                offset = elf.lo
                jumps = invalid = 0
                while offset < elf.hi:
                    instruction, size = deep_disassembly.decode_instruction(elf.b, offset, elf)
                    if elf.b[offset] == 0x05:
                        jumps += 1
                        edges = deep_disassembly.build_cfg_edges([instruction], elf.lo, elf.hi)
                        expected = [{
                            'from': hex(offset), 'to': hex(instruction['branch_target']),
                            'type': 'branch', 'conditional': False,
                        }]
                        invalid += edges != expected
                    offset += size
                self.assertGreater(jumps, 0)
                self.assertEqual(invalid, 0)


class InstructionLogNameTests(unittest.TestCase):
    def test_scan_does_not_copy_binary_suffixes(self):
        class UnslicedBytes(bytes):
            def __getitem__(self, key):
                if isinstance(key, slice):
                    raise AssertionError('instruction scan copied binary bytes')
                return super().__getitem__(key)

        blob = UnslicedBytes(
            b'Instruction: Buyadjacent\0Instruction: Unknown42\0' + bytes(1024 * 1024)
        )
        self.assertEqual(analyze.instruction_log_names(blob, ('Buy',)), ['Buy', 'Unknown42'])

    def test_scan_preserves_marker_boundaries_and_fallback(self):
        blob = (b'Instruction: BuyV2adjacent\0Instruction: Buytail\0'
                b'Instruction: Unknown42Instruction\0Instruction: Instruction\0'
                b'Instruction: lowercaseLater\0Instruction: \xffBad\0'
                b'Instruction: Unknown42\0Instruction: End9')
        self.assertEqual(
            analyze.instruction_log_names(blob, ('BuyV2', 'Buy')),
            ['Buy', 'BuyV2', 'End9', 'Instruction', 'Unknown42'],
        )
        self.assertEqual(analyze.instruction_log_names(b'Instruction: '), [])
        self.assertEqual(analyze.instruction_log_names(b'no marker'), [])
        self.assertEqual(analyze.instruction_log_names(b''), [])


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


# capture.json program ids. pump, pump_amm and pump_fees also match their IDL
# address; mayhem has a receipt and no IDL.
_CAPTURED_PROGRAMS = {
    'pump': '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P',
    'pump_amm': 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA',
    'pump_fees': 'pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ',
    'mayhem': 'MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e',
}


class LocalValidationProgramTests(unittest.TestCase):
    def test_missing_selector_uses_capture_receipts(self):
        got = local_validation.program_addresses()
        self.assertEqual(got, _CAPTURED_PROGRAMS)
        root = local_validation.ROOT
        self.assertFalse((root / 'repro/programs.json').is_file())
        for name, address in _CAPTURED_PROGRAMS.items():
            receipt = json.loads((root / 'evidence/original' / name / 'capture.json').read_text())
            self.assertEqual(receipt['program'], address)
            idl_path = root / 'evidence/upstream' / f'{name}.json'
            if idl_path.is_file():
                self.assertEqual(json.loads(idl_path.read_text())['address'], address)
            else:
                self.assertEqual(name, 'mayhem')

    def test_archived_selector_overrides_capture_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'repro').mkdir()
            (root / 'repro/programs.json').write_text(json.dumps({'pump': 'archived-id'}))
            receipt = root / 'evidence/original/pump'
            receipt.mkdir(parents=True)
            (receipt / 'deployed.so').write_bytes(b'\x7fELF')
            (receipt / 'capture.json').write_text(json.dumps({'program': 'capture-id'}))
            self.assertEqual(local_validation.program_addresses(root), {'pump': 'archived-id'})

    def test_capture_fallback_skips_absent_binaries_and_rejects_blank_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            pump = root / 'evidence/original/pump'
            pump.mkdir(parents=True)
            (pump / 'deployed.so').write_bytes(b'\x7fELF')
            (pump / 'capture.json').write_text(json.dumps({'program': 'pump-id'}))
            fees = root / 'evidence/original/pump_fees'
            fees.mkdir(parents=True)
            (fees / 'capture.json').write_text(json.dumps({'program': 'fees-without-binary'}))
            self.assertEqual(local_validation.program_addresses(root), {'pump': 'pump-id'})
            (pump / 'capture.json').write_text(json.dumps({'program': ''}))
            with self.assertRaises(ValueError):
                local_validation.program_addresses(root)

    def test_no_captures_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                local_validation.program_addresses(tmp)

    def test_archived_selector_must_be_an_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'repro').mkdir()
            (root / 'repro/programs.json').write_text('["pump"]')
            with self.assertRaises(ValueError):
                local_validation.program_addresses(root)


class DispatchRecoveryTests(unittest.TestCase):
    def test_every_captured_program_is_recovered(self):
        import json
        import recover_dispatch
        report = recover_dispatch.dispatch()
        self.assertEqual(
            list(report), ['pump', 'pump_amm', 'pump_fees', 'mayhem'])
        self.assertEqual(
            [sum(bool(row['matches']) for row in rowset['instructions'].values())
             for rowset in report.values()],
            [56, 38, 31, 25])
        self.assertEqual(
            report,
            json.loads((analyze.ROOT / 'evidence/dispatch-map.json').read_text()))


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


def load_window_scorer():
    path = pathlib.Path(__file__).resolve().parents[1] / 'reconstruction/harness/score.py'
    spec = importlib.util.spec_from_file_location('window_score', path)
    module = importlib.util.module_from_spec(spec)
    # score.py imports its sibling llvm_tools module.
    with patch('sys.path', [str(path.parent), *sys.path]):
        spec.loader.exec_module(module)
    return module


class WindowScorerBaselineTests(unittest.TestCase):
    def run_main(self, scorer, *args):
        out = io.StringIO()
        with patch('sys.argv', ['score.py', 'candidate.so', *args]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            scorer.main()
        return json.loads(out.getvalue())

    def test_default_baseline_reports_a_lost_window(self):
        scorer = load_window_scorer()
        # Window 0x120 is a normalized match in the committed baseline.
        lost = {0x120: {'normalized': False, 'raw': False, 'symbols': [], 'bytes': 176}}
        with patch.object(scorer, 'score_with_hash', return_value=(lost, 'mock-sha256')), \
                patch.object(pathlib.Path, 'read_bytes', return_value=b''):
            summary = self.run_main(scorer)
        self.assertEqual(summary['losses'], ['0x120'])

    def test_missing_baseline_is_an_error(self):
        scorer = load_window_scorer()
        with patch.object(scorer, 'score_with_hash', side_effect=AssertionError('scored without a baseline')):
            with self.assertRaises(SystemExit) as exit_:
                self.run_main(scorer, '--baseline', 'missing/score.json')
        self.assertEqual(exit_.exception.code, 2)


if __name__=='__main__': unittest.main()
