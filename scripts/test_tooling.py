#!/usr/bin/env python3
"""Mutation tests ensuring the byte comparator cannot hide code/padding changes."""
import hashlib
import io
import json
import os
import struct
import sys
import tarfile
import tempfile
from pathlib import Path


import contextlib
import io
import json


import os
import struct
import codecs
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


import tempfile
from pathlib import Path


import contextlib
import io
import json
import pathlib
import shutil
import struct
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import copy
import json
import pump_validate_all as corpus
import pump_validate_parallel as parallel


from window_elf_reader import Elf


from amm_sell.test_best_version import BestScoreVersionTests
from amm_sell.test_sell_distance import AlignmentDistanceTests


from amm_sell.test_cached_status import CachedAttemptStatusTests


import gzip


import warnings


import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


import os
import subprocess
import sys


import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile






import pathlib
import shutil
import struct


import hashlib
import json
import pathlib
import shutil
import struct
import subprocess
import sys


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
from test_fees_external_codec_cases import ExternalCodecBooleanCases
from types import SimpleNamespace
import deep_disassembly
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import deep_section_analysis
import deep_disassembly
import analyze
from window_elf_reader import Elf
from compare import compare
class CaseComparisonReceiptTests(unittest.TestCase):
    original = analyze.ROOT / 'evidence/original/pump/deployed.so'
    candidate = analyze.ROOT / 'evidence/original/mayhem/deployed.so'

    def report(self, row):
        return json.loads(json.dumps({
            'original_sha256': corpus.sha(self.original),
            'candidate_sha256': corpus.sha(self.candidate),
            'case_count': corpus.EXPECTED_CASES['volume'],
            'mismatches': [],
            'cases': [copy.deepcopy(row) for _ in range(corpus.EXPECTED_CASES['volume'])],
        }))

    def validate(self, report):
        return parallel.validate_result('volume', report, self.candidate, self.original)

    def test_explicit_case_differences_cannot_hide_behind_empty_summary(self):
        for field in ('different_fields', 'diff', 'differences', 'mismatched_fields'):
            with self.subTest(field=field):
                report = self.report({'original': {}, 'candidate': {}, field: []})
                report['cases'][0][field] = ['account']
                with self.assertRaises(AssertionError):
                    self.validate(report)

    def test_false_case_match_cannot_hide_behind_empty_summary(self):
        report = self.report({'original': {}, 'candidate': {}, 'match': True})
        report['cases'][0]['match'] = False
        with self.assertRaises(AssertionError):
            self.validate(report)

    def test_missing_paired_outcomes_or_comparison_are_rejected(self):
        for row in ({'original': {}, 'match': True},
                    {'original': {}, 'candidate': None, 'diff': []},
                    {'original': {}, 'candidate': {}},
                    {'original': {}, 'candidate': {}, 'diff': None},
                    {'original': {}, 'candidate': {}, 'match': 1}):
            with self.subTest(row=row), self.assertRaises(AssertionError):
                self.validate(self.report(row))

    def test_all_published_generic_case_comparison_encodings_still_pass(self):
        for field in ('different_fields', 'diff', 'differences', 'mismatched_fields', 'match'):
            with self.subTest(field=field):
                self.assertEqual(self.validate(self.report({
                    'original': {}, 'candidate': {}, field: True if field == 'match' else [],
                })), corpus.EXPECTED_CASES['volume'])






class MathDensityOrderTests(unittest.TestCase):
    def analyze(self, windows):
        data = bytearray()
        entries = []
        for opcodes in windows:
            entries.append(len(data))
            data.extend(b''.join(struct.pack('<BBhi', opcode, 0, 0, 0) for opcode in opcodes))
        return deep_section_analysis.analyze_math_patterns(SimpleNamespace(b=bytes(data), entries=entries, hi=len(data), funcs=[]))

    def test_addition_heavy_window_ranks_by_density(self):
        report = self.analyze([[0x27, 0x37, *([0x07] * 3), *([0x95] * 15)], [0x07] * 5])
        rows = report['math_intensive_windows']
        self.assertEqual([row['arithmetic_density'] for row in rows], [1.0, 0.25])
        self.assertEqual([row['address'] for row in rows], ['0xa0', '0x0'])
        self.assertEqual(report['total_math_windows'], 2)
        self.assertEqual(sum(row['additions'] for row in rows), 8)

    def test_equal_density_preserves_entry_order(self):
        rows = self.analyze([[0x07] * 5, [0x07] * 10])['math_intensive_windows']
        self.assertEqual([row['address'] for row in rows], ['0x0', '0x28'])
        self.assertEqual([row['arithmetic_density'] for row in rows], [1.0, 1.0])

    def test_real_captured_math_windows_are_density_ordered(self):
        for name in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
            with self.subTest(program=name):
                elf = Elf(analyze.ROOT / 'evidence/original' / name / 'deployed.so')
                rows = deep_section_analysis.analyze_math_patterns(elf)['math_intensive_windows']
                densities = [row['arithmetic_density'] for row in rows]
                self.assertEqual(densities, sorted(densities, reverse=True))


import deep_disassembly
from compare import compare


class StackAddressOperandTests(unittest.TestCase):
    def analyze(self, *instructions):
        raw = b''.join(struct.pack('<BBhi', *instruction) for instruction in instructions)
        decoded = []
        for offset in range(0, len(raw), 8):
            decoded.append(deep_disassembly.decode_instruction(raw, offset, None)[0])
        return deep_disassembly.analyze_stack_frame(decoded)

    def test_storing_frame_pointer_value_is_not_a_stack_address(self):
        # stxdw [r1-64], r10: r1 is the address; r10 is only the stored value.
        result = self.analyze((0x7b, 0xa1, -64, 0))
        self.assertEqual(result, {'max_stack_depth': 0, 'stack_slots': 0, 'most_accessed_offsets': []})

    def test_frame_pointer_as_both_base_and_value_counts_once(self):
        result = self.analyze((0x7b, 0xaa, -16, 0))
        self.assertEqual(result['max_stack_depth'], 16)
        self.assertEqual(result['most_accessed_offsets'], [{'offset': -16, 'count': 1}])

    def test_load_and_store_address_bases_keep_real_stack_accesses(self):
        result = self.analyze(
            (0x79, 0xa2, -24, 0),  # ldxdw r2, [r10-24]
            (0x7b, 0x2a, -24, 0),  # stxdw [r10-24], r2
            (0x7a, 0x0a, -8, 5),  # stdw [r10-8], 5
        )
        self.assertEqual(result['max_stack_depth'], 24)
        self.assertEqual(result['stack_slots'], 2)
        self.assertEqual(result['most_accessed_offsets'], [{'offset': -24, 'count': 2}, {'offset': -8, 'count': 1}])

    def test_nonmemory_frame_pointer_operand_does_not_count(self):
        self.assertEqual(self.analyze((0xbf, 0xa1, 0, 0))['stack_slots'], 0)


import bytecode_signatures
from window_elf_reader import Elf


import check_sbf_backend_diagnostics as backend_diagnostics
import test_sbf_backend_diagnostics as backend_cases
from compare import compare


class BackendLogSignatureTests(unittest.TestCase):
    def setUp(self):
        folder = analyze.ROOT / 'work'
        folder.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='backend-bom-', dir=folder)
        self.path = Path(self.temporary.name) / 'build.log'

    def tearDown(self):
        self.temporary.cleanup()

    def test_bom_errors_reject_in_plain_gzip_and_ansi_logs(self):
        for compressed in (False, True):
            for colored in (False, True):
                with self.subTest(compressed=compressed, colored=colored):
                    line = ('\x1b[31m' if colored else '') + backend_cases.ERROR + ('\x1b[0m' if colored else '')
                    decoded = codecs.BOM_UTF8 + (line + '\nCargo exit: 0\nstrip exit: 0\n').encode('utf-8')
                    raw = gzip.compress(decoded, mtime=0) if compressed else decoded
                    self.path.write_bytes(raw)
                    result = backend_diagnostics.check([self.path])
                    self.assertFalse(result['diagnostic_gate_passed'])
                    self.assertEqual(result['backend_error_count'], 1)
                    record = result['logs'][0]
                    self.assertEqual(record['backend_errors'][0]['kind'], 'stack_offset_exceeded')
                    self.assertEqual(record['backend_errors'][0]['line_number'], 1)
                    self.assertEqual(record['input_sha256'], hashlib.sha256(raw).hexdigest())
                    self.assertEqual(record['decoded_sha256'], hashlib.sha256(decoded).hexdigest())
                    self.assertEqual(self.path.read_bytes(), raw)

    def test_clean_bom_log_still_makes_no_readiness_claim(self):
        self.path.write_bytes(codecs.BOM_UTF8 + b'Finished release\n')
        result = backend_diagnostics.check([self.path])
        self.assertTrue(result['diagnostic_gate_passed'])
        self.assertFalse(result['program_readiness_proven'])

    def test_only_the_initial_signature_is_removed(self):
        self.path.write_bytes(codecs.BOM_UTF8 + 'Error: internal \ufeff payload\n'.encode('utf-8'))
        errors = backend_diagnostics.inspect(self.path)['backend_errors']
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['text'], 'Error: internal \ufeff payload')

    def test_actual_cli_rejects_a_bom_prefixed_error(self):
        self.path.write_bytes(codecs.BOM_UTF8 + (backend_cases.ERROR + '\n').encode('utf-8'))
        result = subprocess.run([sys.executable, backend_diagnostics.__file__, '--log', str(self.path)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['diagnostic_gate_passed'])


import deep_disassembly
from window_elf_reader import Elf


import bytecode_signatures
from compare import compare


def symbol_hash(name):
    """Independent seed-zero MurmurHash3 x86_32 reference for table checks.

    SBPF ebpf::hash_symbol_name uses hash32::Murmur3Hasher::default().
    Reference: aappleby/smhasher, MurmurHash3.cpp, MurmurHash3_x86_32.
    """
    data = name.encode('utf-8')
    mask = 0xffffffff
    def rotate(n, bits):
        return ((n << bits) | (n >> (32 - bits))) & mask
    def mix(k):
        return (rotate((k * 0xcc9e2d51) & mask, 15) * 0x1b873593) & mask
    h = 0
    complete = len(data) // 4 * 4
    for at in range(0, complete, 4):
        h ^= mix(int.from_bytes(data[at:at+4], 'little'))
        h = (rotate(h, 13) * 5 + 0xe6546b64) & mask
    if complete != len(data):
        h ^= mix(int.from_bytes(data[complete:], 'little'))
    h ^= len(data)
    h ^= h >> 16
    h = h * 0x85ebca6b & mask
    h ^= h >> 13
    h = h * 0xc2b2ae35 & mask
    return h ^ (h >> 16)


class SyscallHashTests(unittest.TestCase):
    def test_reference_vectors(self):
        self.assertEqual(symbol_hash(''), 0)
        self.assertEqual(symbol_hash('foo'), 0xf6a5c420)
        self.assertEqual(symbol_hash('sol_log_'), 0x207559bd)

    def test_each_table_key_is_the_hash_of_its_symbol(self):
        for module in (deep_disassembly, bytecode_signatures, deep_section_analysis):
            for value, name in module.SYSCALL_NAMES.items():
                with self.subTest(module=module.__name__, symbol=name):
                    self.assertEqual(value, symbol_hash(name))

    def test_literal_calls_decode_and_fingerprint_the_hashed_name(self):
        for name in deep_disassembly.SYSCALL_NAMES.values():
            with self.subTest(symbol=name):
                raw = struct.pack('<BBhI', 0x85, 0, 0, symbol_hash(name))
                result, size = deep_disassembly.decode_instruction(raw, 0, None)
                self.assertEqual(result['syscall'], name)
                self.assertEqual(size, 8)
                self.assertEqual(deep_disassembly.fingerprint_window(SimpleNamespace(b=raw, secs={}), 0, 8)['syscall_sequence'], [name])

    def test_cpi_and_memcpy_selectors_use_the_same_hash_rule(self):
        cpi = b''.join(struct.pack('<BBhI', 0x85, 0, 0, symbol_hash(name))
                       for name in ('sol_invoke_signed_c', 'sol_invoke_signed_rust'))
        patterns = bytecode_signatures.detect_cpi_patterns(SimpleNamespace(b=cpi), 0, len(cpi))
        self.assertEqual([p['syscall'] for p in patterns], ['sol_invoke_signed_c', 'sol_invoke_signed_rust'])
        memcpy = struct.pack('<BBhI', 0x85, 0, 0, symbol_hash('sol_memcpy_'))
        self.assertEqual(bytecode_signatures.detect_serialization_patterns(SimpleNamespace(b=memcpy), 0, 8)['memcpy_calls'], 1)
        clock = struct.pack('<BBhI', 0x85, 0, 0, symbol_hash('sol_get_clock_sysvar'))
        self.assertEqual(bytecode_signatures.detect_cpi_patterns(SimpleNamespace(b=clock), 0, 8), [])
        self.assertEqual(bytecode_signatures.detect_serialization_patterns(SimpleNamespace(b=cpi), 0, len(cpi))['memcpy_calls'], 0)

    def test_unknown_hash_keeps_the_existing_fallback(self):
        raw = struct.pack('<BBhI', 0x85, 0, 0, 0x12345678)
        self.assertEqual(deep_disassembly.decode_instruction(raw, 0, None)[0]['syscall'], 'syscall_0x12345678')


import analyze_program
import deep_disassembly
from window_elf_reader import Elf
from compare import compare
class InferredStructExtentTests(unittest.TestCase):
    def analyze_offsets(self, offsets):
        code = b''.join(struct.pack('<BBhi', 0x79, 0x21, offset, 0) for offset in offsets)
        header = bytearray(64)
        struct.pack_into('<Q', header, 24, 64)
        elf = SimpleNamespace(b=bytes(header) + code, lo=64, hi=64+len(code),
                              entries=[64], funcs=[], secs={})
        return deep_section_analysis.recover_anchor_idl(elf)

    def test_size_inference_is_not_limited_to_twenty_displayed_fields(self):
        for count in (20, 21, 35):
            with self.subTest(count=count):
                result = self.analyze_offsets(list(range(0, count*8, 8)))
                row = result['deserialization_patterns'][0]
                self.assertEqual(row['field_offsets'], list(range(0, min(count, 20)*8, 8)))
                self.assertEqual(row['field_sizes'], [8]*min(count, 20))
                self.assertEqual(row['likely_struct_size'], count*8)
                self.assertEqual(result['inferred_struct_sizes'], [count*8])

    def test_duplicate_reads_do_not_change_the_observed_extent(self):
        offsets = list(range(0, 21*8, 8))
        result = self.analyze_offsets(offsets + offsets[-5:])
        self.assertEqual(result['deserialization_patterns'][0]['likely_struct_size'], 168)
        self.assertEqual(len(result['deserialization_patterns'][0]['field_offsets']), 20)

    def test_retained_patterns_use_the_full_observed_load_extent(self):
        checked = capped = 0
        for path in sorted(analyze.ROOT.glob('evidence/**/deployed.so')):
            elf = Elf(path)
            ends = dict(zip(elf.entries, elf.entries[1:] + [elf.hi]))
            result = deep_section_analysis.recover_anchor_idl(elf)
            for row in result['deserialization_patterns']:
                start = int(row['window'], 16)
                offsets = {struct.unpack_from('<h', elf.b, at+2)[0]
                           for at in range(start, ends[start], 8)
                           if elf.b[at] in (0x61, 0x69, 0x71, 0x79)
                           and elf.b[at+1] >> 4 == row['base_reg']}
                self.assertEqual(row['likely_struct_size'], max(offsets)+8,
                                 f'{path.parent.name}:{start:#x}:r{row["base_reg"]}')
                self.assertLessEqual(len(row['field_offsets']), 20)
                checked += 1
                capped += len(offsets) > 20
        self.assertGreater(checked, 0)
        self.assertGreater(capped, 0)




import verify_evidence


from source_manifest_guard import strict_manifest


class DiagnosticOutputPreservationTests(unittest.TestCase):
    def invoke(self, source, output):
        return subprocess.run([sys.executable, str(analyze.ROOT / 'scripts/pump_diagnostic_audit.py'),
                               '--report', str(source), '--output', str(output)],
                              capture_output=True, text=True)

    def test_input_report_cannot_be_its_own_output(self):
        parent = analyze.ROOT / 'work'
        parent.mkdir(exist_ok=True)
        for compressed in (False, True):
            with self.subTest(compressed=compressed), tempfile.TemporaryDirectory(dir=parent) as folder:
                source = Path(folder) / 'report.json'
                raw = json.dumps({'suites': {}}).encode()
                if compressed:
                    raw = gzip.compress(raw, mtime=0)
                source.write_bytes(raw)
                result = self.invoke(source, source)
                self.assertEqual(source.read_bytes(), raw)
                self.assertNotEqual(result.returncode, 0)

    def test_prior_audit_is_preserved(self):
        parent = analyze.ROOT / 'work'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as folder:
            source, output = Path(folder) / 'report.json', Path(folder) / 'audit.json'
            raw = b'{"suites":{}}'
            prior = b'previous bounded audit\n'
            source.write_bytes(raw)
            output.write_bytes(prior)
            result = self.invoke(source, output)
            self.assertEqual(output.read_bytes(), prior)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(source.read_bytes(), raw)

    def test_fresh_outputs_preserve_success_and_mismatch_receipts(self):
        parent = analyze.ROOT / 'work'
        parent.mkdir(exist_ok=True)
        for different in (False, True):
            with self.subTest(different=different), tempfile.TemporaryDirectory(dir=parent) as folder:
                source, output = Path(folder) / 'report.json', Path(folder) / 'audit.json'
                logs = ['Program log: AnchorError. Error Code: One. Error Number: 6000. Error Message: original']
                other = [logs[0].replace('original', 'different')] if different else logs
                raw = json.dumps({'suites': {'fixture': {'original': {'logs': logs}, 'candidate': {'logs': other}}}}).encode()
                source.write_bytes(raw)
                result = self.invoke(source, output)
                self.assertEqual(result.returncode, int(different), result.stderr)
                receipt = json.loads(output.read_bytes())
                self.assertEqual(receipt['source_report_sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(receipt['log_bearing_cases'], 1)
                self.assertEqual(len(receipt['mismatches']), int(different))
                self.assertEqual(source.read_bytes(), raw)






class AnalysisInputSnapshotTests(unittest.TestCase):
    def check_generation(self, module, replace):
        parent = analyze.ROOT / 'work'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='analysis-input-', dir=parent) as folder:
            view = Path(folder)
            source = view / 'evidence/original/mayhem/deployed.so'
            source.parent.mkdir(parents=True)
            shutil.copyfile(analyze.ROOT / 'evidence/original/mayhem/deployed.so', source)
            snapshot = Elf(source)
            original = snapshot.b
            replacement = bytearray(original)
            replacement[snapshot.entries[0] + 4] ^= 1
            replacement.extend(b'\0' * 8)
            output = view / 'packet'
            original_repo, original_reader, original_argv = module.REPO, module.Elf, sys.argv

            class ReplaceAfterRealRead(original_reader):
                def __init__(self, path):
                    super().__init__(path)
                    if replace:
                        path.write_bytes(replacement)

            try:
                module.REPO = view
                module.Elf = ReplaceAfterRealRead
                sys.argv = [module.__file__, '--program', 'mayhem', '--output', str(output)]
                with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
                    warnings.simplefilter("ignore", ResourceWarning)
                    if module is analyze_program:
                        result = module.analyze_program('mayhem', output)
                    else:
                        result = module.main()
                self.assertEqual(result, 0)
            finally:
                module.REPO, module.Elf, sys.argv = original_repo, original_reader, original_argv

            self.assertEqual(source.read_bytes(), replacement if replace else original)
            summary = json.loads((output / 'summary.json').read_bytes())
            digest = hashlib.sha256(original).hexdigest()
            self.assertEqual(summary['deployed_sha256'], digest)
            self.assertIn(digest, (output / 'README.md').read_text(encoding='utf-8'))
            if module is analyze_program:
                self.assertEqual(summary['file_size'], len(original))
                self.assertIn(f'File size: {len(original):,} bytes', (output / 'README.md').read_text(encoding='utf-8'))
                windows = json.loads((output / 'window-inventory.json').read_bytes())
                first = windows[0]
                self.assertEqual(first['raw_sha256'], hashlib.sha256(original[first['address_decimal']:first['address_decimal'] + first['size']]).hexdigest())

    def test_replaced_files_do_not_rebind_already_parsed_analysis(self):
        # The instrumented read parses real ELF bytes before replacing only
        # the temporary path. No analysis results or digest values are mocked.
        for module in (analyze_program, deep_disassembly, deep_section_analysis):
            with self.subTest(generator=module.__name__):
                self.check_generation(module, True)

    def test_unchanged_inputs_keep_their_existing_identity(self):
        for module in (analyze_program, deep_disassembly, deep_section_analysis):
            with self.subTest(generator=module.__name__):
                self.check_generation(module, False)




import pump_diagnostic_audit
from compare import compare


class GeneratedPacketMembershipTests(unittest.TestCase):
    generators = (
        ('analyze_program.py', 'function-index.json'),
        ('deep_disassembly.py', 'fingerprints.json'),
        ('deep_section_analysis.py', 'summary.json'),
        ('bytecode_signatures.py', 'shared-signatures.json'),
    )

    @classmethod
    def run_python(cls, script, *arguments):
        env = dict(os.environ, PYTHONUTF8='1')
        return subprocess.run([sys.executable, str(script), *map(str, arguments)],
                              env=env, capture_output=True, timeout=60)

    @classmethod
    def setUpClass(cls):
        folder = analyze.ROOT / 'work'
        folder.mkdir(exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(prefix='packet-membership-', dir=folder)
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.packets = {}
        for script, _ in cls.generators:
            output = cls.root / Path(script).stem
            arguments = [] if script == 'bytecode_signatures.py' else ['--program', 'mayhem']
            result = cls.run_python(analyze.ROOT / 'scripts' / script, *arguments, '--output', output)
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            cls.packets[script] = output

    def test_complete_generated_packets_verify(self):
        for name, output in self.packets.items():
            with self.subTest(generator=name):
                result = self.run_python(output / 'verify.py')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_artifact_cannot_be_removed_from_the_manifest(self):
        for script, target in self.generators:
            with self.subTest(generator=script):
                output = self.packets[script]
                manifest_path = output / 'manifest.json'
                raw, artifact = manifest_path.read_bytes(), (output / target).read_bytes()
                manifest = json.loads(raw)
                del manifest[target]
                try:
                    (output / target).unlink()
                    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
                    self.assertNotEqual(self.run_python(output / 'verify.py').returncode, 0)
                finally:
                    (output / target).write_bytes(artifact)
                    manifest_path.write_bytes(raw)

    def test_existing_artifact_cannot_be_left_unmanifested(self):
        for script, target in self.generators:
            with self.subTest(generator=script):
                output = self.packets[script]
                path = output / 'manifest.json'
                raw = path.read_bytes()
                manifest = json.loads(raw)
                del manifest[target]
                try:
                    path.write_text(json.dumps(manifest), encoding='utf-8')
                    self.assertNotEqual(self.run_python(output / 'verify.py').returncode, 0)
                finally:
                    path.write_bytes(raw)

    def test_unrelated_file_cannot_be_admitted_by_adding_its_hash(self):
        for script, _ in self.generators:
            with self.subTest(generator=script):
                output = self.packets[script]
                path = output / 'manifest.json'
                raw = path.read_bytes()
                manifest = json.loads(raw)
                extra = output / 'unrelated.txt'
                data = b'not produced by the generator'
                try:
                    extra.write_bytes(data)
                    manifest[extra.name] = hashlib.sha256(data).hexdigest()
                    path.write_text(json.dumps(manifest), encoding='utf-8')
                    self.assertNotEqual(self.run_python(output / 'verify.py').returncode, 0)
                finally:
                    extra.unlink()
                    path.write_bytes(raw)

    def test_existing_digest_checks_still_reject_changed_bytes(self):
        for script, target in self.generators:
            with self.subTest(generator=script):
                output = self.packets[script]
                artifact = output / target
                raw = artifact.read_bytes()
                try:
                    artifact.write_bytes(raw + b'\n ')
                    self.assertNotEqual(self.run_python(output / 'verify.py').returncode, 0)
                finally:
                    artifact.write_bytes(raw)

    def test_partial_signature_packet_keeps_its_generated_program_set(self):
        view = self.root / 'partial-view'
        (view / 'scripts').mkdir(parents=True)
        capture = view / 'evidence/original/mayhem/deployed.so'
        capture.parent.mkdir(parents=True)
        shutil.copyfile(analyze.ROOT / 'evidence/original/mayhem/deployed.so', capture)
        for name in ('bytecode_signatures.py', 'window_elf_reader.py'):
            shutil.copyfile(analyze.ROOT / 'scripts' / name, view / 'scripts' / name)
        output = view / 'packet'
        generated = self.run_python(view / 'scripts/bytecode_signatures.py', '--output', output)
        self.assertEqual(generated.returncode, 0, generated.stdout + generated.stderr)
        self.assertEqual(self.run_python(output / 'verify.py').returncode, 0)
        manifest = json.loads((output / 'manifest.json').read_bytes())
        self.assertIn('mayhem-signatures.json', manifest)
        self.assertNotIn('pump-signatures.json', manifest)


class CorpusOptimizationTests(unittest.TestCase):
    def run_script(self, name, flags=(), optimize=None):
        env = dict(os.environ)
        env.pop('PYTHONOPTIMIZE', None)
        if optimize is not None:
            env['PYTHONOPTIMIZE'] = optimize
        return subprocess.run([sys.executable, *flags, str(analyze.ROOT / 'scripts' / name), '--help'],
                              env=env, capture_output=True)

    def test_optimized_import_cannot_admit_an_invalid_report(self):
        code = '''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import pump_validate_parallel as runner
artifact = Path(sys.argv[2])
report = {'original_sha256': 'wrong', 'candidate_sha256': 'wrong',
          'case_count': 66, 'cases': [], 'mismatches': ['synthetic failure']}
print(runner.validate_result('volume', report, artifact, artifact))
'''
        for flag in ('-O', '-OO'):
            with self.subTest(flag=flag):
                result = subprocess.run([sys.executable, flag, '-c', code, str(analyze.ROOT / 'scripts'),
                                         str(analyze.ROOT / 'evidence/original/pump/deployed.so')], capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'Normal Python is required', result.stderr)

    def test_both_clis_reject_optimized_startup(self):
        for name in ('pump_validate_all.py', 'pump_validate_parallel.py'):
            for flags, environment in ((('-O',), None), (('-OO',), None), ((), '1')):
                with self.subTest(script=name, flags=flags, environment=environment):
                    result = self.run_script(name, flags, environment)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(b'Normal Python is required', result.stderr)

    def test_both_normal_clis_remain_available(self):
        for name in ('pump_validate_all.py', 'pump_validate_parallel.py'):
            with self.subTest(script=name):
                result = self.run_script(name)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(b'--candidate', result.stdout)

    def test_normal_mode_still_rejects_invalid_artifact_bindings(self):
        code = '''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import pump_validate_parallel as runner
artifact = Path(sys.argv[2])
runner.validate_result('volume', {'original_sha256': 'wrong', 'candidate_sha256': 'wrong',
                                 'case_count': 66, 'cases': [], 'mismatches': ['synthetic failure']},
                       artifact, artifact)
'''
        env = dict(os.environ)
        env.pop('PYTHONOPTIMIZE', None)
        result = subprocess.run([sys.executable, '-c', code, str(analyze.ROOT / 'scripts'),
                                 str(analyze.ROOT / 'evidence/original/pump/deployed.so')], env=env, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'AssertionError', result.stderr)
        self.assertNotIn(b'Normal Python is required', result.stderr)


class PanicPayloadTests(unittest.TestCase):
    def audit(self, left, right):
        return pump_diagnostic_audit.audit({'synthetic': {'cases': [{
            'original': {'logs': [left]}, 'candidate': {'logs': [right]},
        }]}})

    def test_legacy_multiline_first_line_is_not_discarded(self):
        result = self.audit("Program log: panicked at 'first A\nshared tail', src/lib.rs:1:2",
                            "Program log: panicked at 'first B\nshared tail', src/lib.rs:1:2")
        self.assertEqual(result['log_bearing_cases'], 1)
        self.assertEqual(len(result['mismatches']), 1)
        self.assertEqual(result['mismatches'][0]['original']['panic'], ['first A\nshared tail'])

    def test_legacy_source_locations_are_excluded_from_the_payload(self):
        for message in ('same message', "same 'quoted' message\nsecond line"):
            with self.subTest(message=message):
                result = self.audit(f"Program log: panicked at '{message}', old/src.rs:1:2",
                                    f"Program log: panicked at '{message}', new/src.rs:90:7")
                self.assertEqual(result['mismatches'], [])

    def test_modern_payload_and_location_boundary_are_preserved(self):
        result = self.audit('Program log: panicked at old/src.rs:1:2:\nfirst\nsecond',
                            'Program log: panicked at new/src.rs:90:7:\nfirst\nsecond')
        self.assertEqual(result['mismatches'], [])
        self.assertEqual(pump_diagnostic_audit.messages(['Program log: panicked at src.rs:1:2:\nfirst\nsecond'])['panic'], ['first\nsecond'])

    def test_unrecognized_multiline_text_is_compared_in_full(self):
        for left, right in (
            ('custom first A\nshared tail', 'custom first B\nshared tail'),
            ('message A:١:٢:\nshared tail', 'message B:١:٢:\nshared tail'),
        ):
            with self.subTest(left=left):
                result = self.audit('Program log: panicked at ' + left, 'Program log: panicked at ' + right)
                self.assertEqual(len(result['mismatches']), 1)

    def test_real_cli_fails_for_a_changed_legacy_first_line(self):
        temporary_root = analyze.ROOT / 'work'
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='panic-audit-', dir=temporary_root) as folder:
            report, output = Path(folder) / 'input.json', Path(folder) / 'output.json'
            data = {'suites': {'synthetic': {'cases': [{
                'original': {'logs': ["Program log: panicked at 'A\nshared', src.rs:1:2"]},
                'candidate': {'logs': ["Program log: panicked at 'B\nshared', src.rs:1:2"]},
            }]}}}
            raw = json.dumps(data).encode('utf-8')
            report.write_bytes(raw)
            result = subprocess.run([sys.executable, pump_diagnostic_audit.__file__, '--report', str(report), '--output', str(output)], capture_output=True)
            self.assertEqual(result.returncode, 1)
            audited = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(audited['mismatches']), 1)
            self.assertEqual(audited['source_report_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(report.read_bytes(), raw)


import pump_validate_parallel
from compare import compare


class ParallelCaseCountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = analyze.ROOT / 'evidence/original/pump/deployed.so'
        cls.digest = pump_validate_parallel.sha(cls.artifact)

    def suites(self):
        return {name: count for name, count in pump_validate_parallel.base.EXPECTED_CASES.items()
                if name not in ('quote_control', 'multi_hop_curve_partial', 'tokenkeg_two_curve')}

    def report(self, count):
        return self.artifact, {'original_sha256': self.digest, 'candidate_sha256': self.digest,
                          'case_count': count, 'mismatches': []}

    def test_missing_or_nonarray_cases_cannot_support_a_declared_count(self):
        for name, count in self.suites().items():
            for cases in (None, {}, 'not a case list'):
                with self.subTest(suite=name, cases=cases):
                    artifact, report = self.report(count)
                    if cases is not None:
                        report['cases'] = cases
                    with self.assertRaises(AssertionError):
                        pump_validate_parallel.validate_result(name, report, artifact, artifact)

    def test_declared_count_must_equal_the_retained_case_list(self):
        for name, count in self.suites().items():
            for length in (0, count - 1, count + 1):
                with self.subTest(suite=name, length=length):
                    artifact, report = self.report(count)
                    report['cases'] = [{'case': index} for index in range(length)]
                    with self.assertRaises(AssertionError):
                        pump_validate_parallel.validate_result(name, report, artifact, artifact)

    def test_consistent_explicit_and_derived_counts_remain_accepted(self):
        # These are shape-validation fixtures, not newly executed VM cases.
        for name, count in self.suites().items():
            for explicit_count in (True, False):
                with self.subTest(suite=name, explicit_count=explicit_count):
                    artifact, report = self.report(count)
                    report['cases'] = [{'case': index, 'original': {}, 'candidate': {}, 'match': True}
                                       for index in range(count)]
                    if not explicit_count:
                        del report['case_count']
                    self.assertEqual(pump_validate_parallel.validate_result(name, report, artifact, artifact), count)

    def test_special_suite_count_protocols_are_unchanged(self):
        artifact = self.artifact
        reports = {
            'quote_control': {'bound_inputs_sha256': {str(artifact.relative_to(analyze.ROOT)): self.digest},
                              'cases': 507, 'results': [{'matches': True, 'different_fields': []} for _ in range(507)]},
            'multi_hop_curve_partial': {'candidate_sha256': self.digest, 'original_pump_sha256': self.digest,
                                        'passed': 56, 'case_count': 56, 'cases': [{'mismatches': []} for _ in range(56)]},
            'tokenkeg_two_curve': {'candidate_sha256': self.digest,
                                  'provenance': {'repository_inputs': {'evidence/original/pump/deployed.so': self.digest}},
                                  'inputs_unchanged': True, 'case_count': 20, 'original_successes': 16,
                                  'original_pump_cpi_cases': 18, 'verified_outer_signatures': 40,
                                  'cases': [{'candidate': {}, 'mismatches': []} for _ in range(20)]},
        }
        for name, special in reports.items():
            with self.subTest(suite=name):
                self.assertEqual(pump_validate_parallel.validate_result(name, special, artifact, artifact),
                                 pump_validate_parallel.base.EXPECTED_CASES[name])


import verify_evidence




from capture import b58


import local_validation
from compare import compare
from test_revalidation_output import RevalidationOutputTests




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
from test_build_quote_fees import QuoteFeesBuildLogTests
class ComparisonTests(unittest.TestCase):
    def test_equal(self): self.assertTrue(compare(b'abc\0\0',b'abc\0\0')['full_byte_equality'])
    def test_code_mutation(self): self.assertEqual(compare(b'abc\0\0',b'axc\0\0')['first_difference'],1)
    def test_padding_mutation(self): self.assertEqual(compare(b'abc\0\0',b'abc\0x')['first_difference'],4)
    def test_truncated_padding(self): self.assertFalse(compare(b'abc\0\0',b'abc\0')['full_byte_equality'])
    def test_extended_padding(self): self.assertFalse(compare(b'abc\0',b'abc\0\0')['full_byte_equality'])
    def test_empty(self): self.assertEqual(compare(b'a',b'')['first_difference'],0)


class SerializationBoundaryTests(unittest.TestCase):
    def detect(self, opcodes):
        raw = b''.join(struct.pack('<BBhi', opcode, 0, 0, 0) for opcode in opcodes)
        return bytecode_signatures.detect_serialization_patterns(SimpleNamespace(b=raw), 0, len(raw))

    def test_terminal_store_run_meets_the_existing_threshold(self):
        result = self.detect([0x63, 0x6b, 0x73, 0x7b])
        self.assertEqual(result['sequential_stores'], 4)
        self.assertEqual(result['max_store_run'], 4)
        self.assertTrue(result['likely_serialization'])

    def test_short_and_interrupted_runs_do_not_meet_threshold(self):
        for opcodes in ([0x63] * 3, [0x63, 0x63, 0xb7, 0x63, 0x63], []):
            with self.subTest(opcodes=opcodes):
                self.assertFalse(self.detect(opcodes)['likely_serialization'])

    def test_classification_does_not_depend_on_a_trailing_exit(self):
        for opcodes in ([0x63] * 4, [0x63] * 5, [0x63] * 2 + [0xb7] + [0x63] * 4):
            with self.subTest(opcodes=opcodes):
                self.assertEqual(self.detect(opcodes), self.detect([*opcodes, 0x95]))

    def test_retained_four_store_ranges(self):
        ranges = {'pump': 0x1788, 'pump_amm': 0xe50, 'pump_fees': 0x1bf0, 'mayhem': 0x5720}
        for name, start in ranges.items():
            with self.subTest(program=name):
                elf = Elf(analyze.ROOT / 'evidence/original' / name / 'deployed.so')
                self.assertTrue(all(elf.b[at] in (0x63, 0x6b, 0x73, 0x7b) for at in range(start, start + 32, 8)))
                result = bytecode_signatures.detect_serialization_patterns(elf, start, start + 32)
                self.assertEqual(result['max_store_run'], 4)
                self.assertTrue(result['likely_serialization'])


class PatternTailScanTests(unittest.TestCase):
    def test_error_branch_in_last_instruction_is_scanned(self):
        raw = struct.pack('<BBhi', 0xb7, 0, 0, 6000) + struct.pack('<BBhi', 0x15, 0, -2, 0)
        result = bytecode_signatures.detect_error_patterns(SimpleNamespace(b=raw), 0, len(raw))
        self.assertEqual(result, [{'offset': 8, 'branch_target_offset': 0, 'error_code': 6000, 'type': 'conditional_error'}])

    def test_account_pair_uses_only_its_two_instruction_extent(self):
        raw = struct.pack('<BBhi', 0x79, 1, 0, 0) + struct.pack('<BBhi', 0x55, 1, 0, 8)
        result = bytecode_signatures.detect_account_validation(SimpleNamespace(b=raw), 0, len(raw))
        self.assertEqual(result['discriminator_checks'], 1)
        self.assertTrue(result['likely_account_validation'])

    def test_single_owner_field_load_is_included(self):
        raw = struct.pack('<BBhi', 0x79, 1, 32, 0)
        result = bytecode_signatures.detect_account_validation(SimpleNamespace(b=raw), 0, len(raw))
        self.assertEqual(result['owner_field_accesses'], 1)
        self.assertFalse(result['likely_account_validation'])

    def test_empty_ranges_are_empty(self):
        elf = SimpleNamespace(b=b'')
        self.assertEqual(bytecode_signatures.detect_error_patterns(elf, 0, 0), [])
        self.assertEqual(bytecode_signatures.detect_account_validation(elf, 0, 0)['owner_field_accesses'], 0)

    def test_retained_pump_terminal_branch(self):
        elf = Elf(analyze.ROOT / 'evidence/original/pump/deployed.so')
        result = bytecode_signatures.detect_error_patterns(elf, 0xef40, 0xefc8)
        self.assertIn({'offset': 120, 'branch_target_offset': 24, 'error_code': 0, 'type': 'conditional_error'}, result)


class NegationDecodeTests(unittest.TestCase):
    def test_negation_has_only_a_destination_operand(self):
        for opcode, mnemonic in ((0x84, 'neg32'), (0x87, 'neg64')):
            for register in (0, 3, 10):
                with self.subTest(opcode=opcode, register=register):
                    raw = struct.pack('<BBhi', opcode, register, 0, 0)
                    result, size = deep_disassembly.decode_instruction(raw, 0, None)
                    self.assertEqual(result['mnemonic'], f'{mnemonic} r{register}')
                    self.assertEqual(result['hex'], raw.hex())
                    self.assertEqual(result['imm'], 0)
                    self.assertEqual(size, 8)

    def test_binary_alu_operands_are_unchanged(self):
        for raw, expected in (
            (struct.pack('<BBhi', 0x07, 3, 0, -2), 'add64 r3, -2'),
            (struct.pack('<BBhi', 0x0f, 0x23, 0, 0), 'add64 r3, r2'),
            (struct.pack('<BBhi', 0x17, 3, 0, 0), 'sub64 r3, 0'),
        ):
            self.assertEqual(deep_disassembly.decode_instruction(raw, 0, None)[0]['mnemonic'], expected)

    def test_captured_negations_have_no_invented_immediate(self):
        expected_counts = {'pump': 25, 'pump_amm': 24, 'pump_fees': 16, 'mayhem': 30}
        for name, expected_count in expected_counts.items():
            elf = Elf(analyze.ROOT / 'evidence/original' / name / 'deployed.so')
            count = 0
            offset = elf.lo
            while offset < elf.hi:
                opcode = elf.b[offset]
                if opcode in (0x84, 0x87):
                    result, size = deep_disassembly.decode_instruction(elf.b, offset, elf)
                    self.assertEqual(result['mnemonic'], f"neg{32 if opcode == 0x84 else 64} r{elf.b[offset + 1] & 15}")
                    self.assertEqual(size, 8)
                    count += 1
                offset += 16 if opcode == 0x18 else 8
            self.assertEqual(count, expected_count, name)


class EvidenceCheckOptimizeTests(unittest.TestCase):
    def test_check_survives_python_optimize(self):
        # `python -O` strips `assert`; verify_evidence must still fail closed.
        import subprocess, sys, pathlib
        here = pathlib.Path(__file__).resolve().parent
        code = 'import verify_evidence as v\ntry:\n    v.check(False, "x")\nexcept v.EvidenceError:\n    raise SystemExit(7)\n'
        r = subprocess.run([sys.executable, '-O', '-c', code], cwd=here)
        self.assertEqual(r.returncode, 7)


class SyscallFingerprintTests(unittest.TestCase):
    def test_mixed_calls_preserve_order_and_skip_lddw_data(self):
        call = lambda src, imm: struct.pack('<BBhI', 0x85, src, 0, imm)
        code = (call(0, 0x207559bd) + call(0x10, 0xffffffff)
                + call(0x10, 0xffffffff) + call(0, 0x12345678)
                + struct.pack('<BBhi', 0x18, 0, 0, 0) + call(0, 0x207559bd)
                + call(0x10, 0xffffffff) + call(0x10, 1))
        # Symbol 1 is imported, symbol 2 is a defined BPF function.
        dynsym = bytes(24) + struct.pack('<IBBHQQ', 0, 0, 0, 0, 0, 0)
        dynsym += struct.pack('<IBBHQQ', 0, 2, 0, 1, 16, 8)
        rel = b''.join(struct.pack('<QQ', at, (idx << 32) | 10)
                       for at, idx in ((8, 1), (16, 2), (48, 1)))
        elf = SimpleNamespace(b=code + dynsym + rel, symbols={1: 'abort', 2: 'helper'},
            secs={'.dynsym': (0, 11, 0, 0, len(code), len(dynsym), 0, 0, 8, 24),
                  '.rel.dyn': (0, 9, 0, 0, len(code)+len(dynsym), len(rel), 0, 0, 8, 16)})
        fp = deep_disassembly.fingerprint_window(elf, 0, len(code))
        self.assertEqual(fp['syscall_sequence'],
                         ['sol_log_', 'abort', 'unknown_0x12345678', 'abort'])
        self.assertEqual(fp['opcode_count'], 7)

    def test_missing_invalid_and_noncall_relocations(self):
        code = struct.pack('<BBhI', 0x85, 0x10, 0, 0xffffffff)
        for typ, index, entry_size in ((8, 1, 24), (10, 5, 24), (10, 1, 0)):
            with self.subTest(typ=typ, index=index, entry_size=entry_size):
                sym = bytes(48)
                rel = struct.pack('<QQ', 0, (index << 32) | typ)
                elf = SimpleNamespace(b=code + sym + rel, symbols={1: 'abort'},
                    secs={'.dynsym': (0, 11, 0, 0, 8, 48, 0, 0, 8, entry_size),
                          '.rel.dyn': (0, 9, 0, 0, 56, 16, 0, 0, 8, 16)})
                self.assertEqual(deep_disassembly.fingerprint_window(
                    elf, 0, 8)['syscall_sequence'], [])
        elf.secs = {}
        self.assertEqual(deep_disassembly.fingerprint_window(elf, 0, 8)['syscall_sequence'], [])

    def test_unresolved_relocation_does_not_become_literal_syscall(self):
        code = struct.pack('<BBhI', 0x85, 0, 0, 0x207559bd) * 2
        for sections in ({}, {'.dynsym': (0, 11, 0, 0, 16, 24, 0, 0, 8, 0),
                              '.rel.dyn': (0, 9, 0, 0, 16, 16, 0, 0, 8, 16)}):
            with self.subTest(sections=sections):
                elf = SimpleNamespace(b=code, secs=sections, symbols={},
                                      relocations={0: {'type': 10, 'symbol': 'unresolved'}})
                self.assertEqual(deep_disassembly.fingerprint_window(
                    elf, 0, len(code))['syscall_sequence'], ['sol_log_'])

    def test_captured_import_sequences(self):
        for name, count in (('pump', 269), ('pump_amm', 173),
                            ('pump_fees', 154), ('mayhem', 133)):
            with self.subTest(program=name):
                elf = deep_disassembly.Elf(analyze.ROOT / 'evidence/original' / name / 'deployed.so')
                sym = elf.secs['.dynsym']
                rel = elf.secs['.rel.dyn']
                expected = []
                for pos in range(rel[4], rel[4] + rel[5], 16):
                    at, info = struct.unpack_from('<QQ', elf.b, pos)
                    if info & 0xffffffff != 10:
                        continue
                    index = info >> 32
                    fields = struct.unpack_from('<IBBHQQ', elf.b, sym[4] + index * 24)
                    if fields[3] == 0:
                        expected.append((at, elf.symbols[index]))
                expected = [label for _, label in sorted(expected)]
                self.assertEqual(len(expected), count)
                self.assertEqual(deep_disassembly.fingerprint_window(
                    elf, elf.lo, elf.hi)['syscall_sequence'], expected)
                self.assertNotIn('custom_panic', expected)


class InternalCallDecodeTests(unittest.TestCase):
    def test_forward_and_backward_internal_targets(self):
        for offset, immediate, target in ((8, 2, 32), (16, -2, 8)):
            with self.subTest(immediate=immediate):
                blob = bytes(offset) + struct.pack('<BBhi', 0x85, 0x10, 0, immediate)
                elf = SimpleNamespace(
                    funcs=[{'start': target, 'name': 'helper'}], relocations={})
                record, size = deep_disassembly.decode_instruction(blob, offset, elf)
                self.assertEqual(size, 8)
                self.assertEqual(record['call_target'], target)
                self.assertEqual(record['call_name'], 'helper')
                self.assertEqual(record['mnemonic'], 'call helper')
                self.assertNotIn('extern_symbol', record)

    def test_relocated_placeholder_stays_external(self):
        blob = struct.pack('<BBhi', 0x85, 0x10, 0, -1)
        elf = SimpleNamespace(funcs=[], relocations={
            0: {'type': 10, 'symbol': 'sol_log_'},
        })
        record, _ = deep_disassembly.decode_instruction(blob, 0, elf)
        self.assertEqual(record['extern_symbol'], 'sol_log_')
        self.assertEqual(record['mnemonic'], 'call_extern sol_log_')
        self.assertNotIn('call_target', record)

    def test_hashed_syscall_stays_syscall(self):
        blob = struct.pack('<BBhI', 0x85, 0, 0, 0x207559bd)
        elf = SimpleNamespace(funcs=[], relocations={})
        record, _ = deep_disassembly.decode_instruction(blob, 0, elf)
        self.assertEqual(record['syscall'], 'sol_log_')
        self.assertNotIn('call_target', record)

    def test_captured_call_targets_match_window_reader(self):
        for name in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
            with self.subTest(program=name):
                elf = deep_disassembly.Elf(
                    analyze.ROOT / 'evidence/original' / name / 'deployed.so')
                self.assertGreater(len(elf.calls), 0)
                for offset, target in elf.calls.items():
                    record, _ = deep_disassembly.decode_instruction(elf.b, offset, elf)
                    self.assertEqual(record['call_target'], target)
                    self.assertNotIn('extern_symbol', record)
                for offset, relocation in elf.relocations.items():
                    if relocation['type'] == 10:
                        record, _ = deep_disassembly.decode_instruction(elf.b, offset, elf)
                        self.assertEqual(record['extern_symbol'], relocation['symbol'])
                        self.assertNotIn('call_target', record)


class RelocationTypeTests(unittest.TestCase):
    def test_sbpf_relocation_names(self):
        types = (0, 1, 8, 10, 2, 255)
        blob = b''.join(struct.pack('<QQ', 0, typ) for typ in types)
        elf = SimpleNamespace(
            b=blob, symbols={}, lo=0x1000, hi=0x2000,
            secs={'.rel.dyn': (0, 9, 0, 0, 0, len(blob), 0, 0, 8, 16)},
        )
        report = deep_section_analysis.analyze_relocations(elf)
        self.assertEqual(
            [entry['type'] for entry in report['entries']],
            ['R_BPF_NONE', 'R_BPF_64_64', 'R_BPF_64_RELATIVE',
             'R_BPF_64_32', 'UNKNOWN_2', 'UNKNOWN_255'],
        )
        self.assertEqual([entry['type_id'] for entry in report['entries']], list(types))

    def test_captured_relative_and_call_relocations(self):
        for name in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
            with self.subTest(program=name):
                elf = deep_section_analysis.Elf(
                    analyze.ROOT / 'evidence/original' / name / 'deployed.so')
                report = deep_section_analysis.analyze_relocations(elf)
                self.assertEqual(set(report['type_distribution']),
                                 {'R_BPF_64_RELATIVE', 'R_BPF_64_32'})
                for entry in report['entries']:
                    self.assertEqual(entry['type'], {
                        8: 'R_BPF_64_RELATIVE', 10: 'R_BPF_64_32',
                    }[entry['type_id']])


class AllocationSizeRegisterTests(unittest.TestCase):
    def sizes(self, instructions):
        blob = bytes(64) + b''.join(struct.pack('<BBhi', *ix) for ix in instructions)
        elf = SimpleNamespace(b=blob, lo=64, hi=len(blob), entries=[64], funcs=[])
        return deep_section_analysis.recover_anchor_idl(elf)['unique_allocation_sizes']

    def test_size_comes_from_r1_not_nearer_r2(self):
        self.assertEqual(self.sizes([
            (0xb7, 1, 0, 64), (0xb7, 2, 0, 0),
            (0x85, 0, 0, -2081419633),
        ]), [64])

    def test_other_register_does_not_supply_size(self):
        self.assertEqual(self.sizes([
            (0xb7, 2, 0, 64), (0x85, 0, 0, -2081419633),
        ]), [])


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


@unittest.skipUnless(sys.version_info >= (3, 11), 'pump_dependency_cache needs tomllib')
class DependencyCacheArchiveTests(unittest.TestCase):
    def import_seed(self, extra=None):
        import pump_dependency_cache as m
        sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            crate = root / 'repo/prog'
            crate.mkdir(parents=True)
            (crate / 'Cargo.toml').write_text('[package]\nname="prog"\nversion="0.1.0"\n[workspace]\n')
            files = {'Cargo.toml': b'[package]\nname="dep"\nversion="1.0.0"\n', 'src/lib.rs': b'pub fn f() {}\n'}
            data = io.BytesIO()
            with tarfile.open(fileobj=data, mode='w:gz') as tar:
                for name, body in files.items():
                    info = tarfile.TarInfo('dep-1.0.0/' + name)
                    info.size = len(body)
                    tar.addfile(info, io.BytesIO(body))
            home = root / 'cargo'
            namespace = 'index.crates.io-1949cf8c6b5b557f'
            archive = home / 'registry/cache' / namespace / 'dep-1.0.0.crate'
            archive.parent.mkdir(parents=True)
            archive.write_bytes(data.getvalue())
            (crate / 'Cargo.lock').write_text(
                'version = 3\n[[package]]\nname="dep"\nversion="1.0.0"\nchecksum="%s"\n'
                '[[package]]\nname="prog"\nversion="0.1.0"\n' % sha(archive))
            source = home / 'registry/src' / namespace / 'dep-1.0.0'
            for name, body in {**files, '.cargo-ok': b'{"v":1}', **({extra: b'fn main() {}\n'} if extra and extra != 'linked' else {})}.items():
                (source / name).parent.mkdir(parents=True, exist_ok=True)
                (source / name).write_bytes(body)
            if extra == 'linked':
                os.symlink(source / 'src', source / 'linked')
            build = root / 'build'
            (build / 'target/release/deps').mkdir(parents=True)
            (build / 'target/release/deps/libdep-0123456789abcdef.rlib').write_bytes(b'rlib')
            for name in ['candidate.so', 'unstripped.so']:
                (build / name).write_bytes(name.encode())
            wrapper = root / 'wrapper'
            wrapper.write_text('w')
            (build / 'build-comparison.json').write_text(json.dumps({
                'returncode': 0, 'source_unchanged': True, 'source_sha256': {},
                'comparison': {'candidate_sha256': sha(build / 'candidate.so')},
                'unstripped_sha256': sha(build / 'unstripped.so'),
                'tool_sha256': {'rustc': 'r', 'cargo': 'c'}, 'source_wrapper_sha256': sha(wrapper),
                'environment': {'CARGO_HOME': str(home)},
                'command': ['cargo', '--manifest-path', str(crate / 'Cargo.toml')]}))
            cache = object.__new__(m.DependencyCache)
            cache.repo, cache.crate, cache.workspace, cache.direct = root / 'repo', crate, crate, False
            cache.env = {'CARGO_HOME': str(home)}
            cache.target = 'sbf-solana-solana'
            cache.target_flags_key = 'CARGO_TARGET_SBF_SOLANA_SOLANA_RUSTFLAGS'
            cache.tools = {'rust/bin/rustc': 'r', 'rust/bin/cargo': 'c'}
            cache.sources = {str(source): m.tree(source)}
            cache.packages = cache.crates = {'dep'}
            cache.main_names = {'prog'}
            cache.context = {'wrapper_sha256': sha(wrapper), 'external_sources': cache.sources}
            cache.root, cache.key, cache.record = root / 'cache', 'k', {}
            cache.entry = cache.root / 'k'
            try:
                cache.import_clean_build(build)
            finally:
                published = cache.entry.exists()
            return cache.record, published

    def test_locked_source_tree_is_imported(self):
        record, published = self.import_seed()
        self.assertEqual(record['imported_clean_build']['archive_files_verified'], 2)
        self.assertTrue(published)

    def test_files_absent_from_locked_archive_are_rejected(self):
        for extra in ['build.rs', 'src/evil.rs', 'linked']:
            with self.subTest(extra=extra), self.assertRaisesRegex(AssertionError, 'absent from locked archive'):
                self.import_seed(extra)


class ProgramDataPdaTests(unittest.TestCase):
    def record(self, name):
        return json.loads((analyze.ROOT / 'evidence' / name / 'capture.json').read_text())

    def test_upgradeable_captures_bind_to_loader_pda(self):
        for f in sorted((analyze.ROOT / 'evidence').glob('**/capture.json')):
            m = json.loads(f.read_text())
            if m.get('loader') != 'legacy-v2':
                verify_evidence.check_programdata_pda(m)

    def test_other_programs_bytes_under_this_program_id_are_rejected(self):
        m = self.record('original/pump')
        m['programdata'] = self.record('original/pump_amm')['programdata']
        with self.assertRaises(AssertionError):
            verify_evidence.check_programdata_pda(m)

    def test_gate_checks_every_upgradeable_capture(self):
        seen = []
        check = verify_evidence.check_programdata_pda
        verify_evidence.check_programdata_pda = lambda m: (seen.append(m['program']), check(m))
        self.addCleanup(setattr, verify_evidence, 'check_programdata_pda', check)
        with contextlib.redirect_stdout(io.StringIO()):
            verify_evidence.main()
        self.assertEqual(len(seen), 8)


class SourceManifestLinkedDirectoryTests(unittest.TestCase):
    def crate(self, root):
        root = root.resolve()
        crate = root / 'repo/crate'
        crate.mkdir(parents=True)
        (crate / 'Cargo.toml').write_text('[package]\nname = "probe"\n')
        outside = root / 'outside'
        outside.mkdir()
        (outside / 'lib.rs').write_text('pub fn external() {}\n')
        return crate, outside

    def test_plain_source_directory_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            crate, _ = self.crate(Path(temporary))
            (crate / 'src').mkdir()
            (crate / 'src/lib.rs').write_text('pub fn local() {}\n')
            self.assertEqual(set(strict_manifest(crate, crate, crate.parent)), {'crate/Cargo.toml', 'crate/src/lib.rs'})

    def test_symlinked_source_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            crate, outside = self.crate(Path(temporary))
            os.symlink(outside, crate / 'src')
            with self.assertRaisesRegex(ValueError, 'symlinked directory'):
                strict_manifest(crate, crate, crate.parent)

    def test_symlinked_directory_named_target_below_the_crate_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            crate, outside = self.crate(Path(temporary))
            (crate / 'src').mkdir()
            os.symlink(outside, crate / 'src/target')
            with self.assertRaisesRegex(ValueError, 'symlinked directory'):
                strict_manifest(crate, crate, crate.parent)

    def test_symlinked_directory_in_extra_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            crate, outside = self.crate(Path(temporary))
            assets = crate.parent / 'assets'
            assets.mkdir()
            os.symlink(outside, assets / 'tables')
            with self.assertRaisesRegex(ValueError, 'symlinked directory'):
                strict_manifest(crate, crate, crate.parent, [assets])


class RelocatedCallTargetTests(unittest.TestCase):
    """Call targets live in .rel.dyn, so detectors cannot read the immediate."""

    def setUp(self):
        from pathlib import Path
        from window_elf_reader import Elf
        import bytecode_signatures
        self.signatures = bytecode_signatures
        self.elf = Elf(Path(analyze.ROOT) / 'evidence/original/pump_amm/deployed.so')

    def test_cpi_detection_resolves_relocated_call_targets(self):
        patterns = self.signatures.detect_cpi_patterns(self.elf, self.elf.lo, self.elf.hi)
        self.assertEqual(
            [pattern['syscall'] for pattern in patterns],
            ['sol_invoke_signed_rust'],
        )

    def test_serialization_counts_relocated_memcpy_calls(self):
        report = self.signatures.detect_serialization_patterns(
            self.elf, self.elf.lo, self.elf.hi
        )
        self.assertEqual(report['memcpy_calls'], 2)


class EvidenceCommitmentTests(unittest.TestCase):
    """The saved-evidence gate must reject a capture that is not finalized."""
    FOLDER = 'evidence/original/pump'

    def run_gate(self, **changes):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            shutil.copytree(analyze.ROOT / self.FOLDER, root / self.FOLDER)
            shutil.copytree(analyze.ROOT / 'evidence/upstream', root / 'evidence/upstream')
            path = root / self.FOLDER / 'capture.json'
            record = json.loads(path.read_text())
            record.update(changes)
            path.write_text(json.dumps(record))
            old_root, old_expected = verify_evidence.ROOT, verify_evidence.EXPECTED_CAPTURES
            verify_evidence.ROOT = root
            verify_evidence.EXPECTED_CAPTURES = frozenset({self.FOLDER})
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    verify_evidence.main()
            finally:
                verify_evidence.ROOT, verify_evidence.EXPECTED_CAPTURES = old_root, old_expected

    def test_finalized_capture_passes(self):
        self.run_gate()

    def test_weaker_commitment_is_rejected(self):
        with self.assertRaises(AssertionError) as raised:
            self.run_gate(commitment='processed')
        self.assertIn(self.FOLDER, str(raised.exception))
        self.assertIn('commitment', str(raised.exception))


class EvidenceProgramBindingTests(unittest.TestCase):
    """A capture must carry the address of the folder that publishes it."""
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        shutil.copytree(verify_evidence.ROOT / 'evidence', self.tmp / 'evidence')
        self.root = verify_evidence.ROOT
        self.expected = verify_evidence.EXPECTED_CAPTURES
        verify_evidence.ROOT = self.tmp
        verify_evidence.EXPECTED_CAPTURES = frozenset(
            p.parent.relative_to(self.tmp).as_posix()
            for p in (self.tmp / 'evidence').glob('**/capture.json'))
        self.addCleanup(setattr, verify_evidence, 'ROOT', self.root)
        self.addCleanup(setattr, verify_evidence, 'EXPECTED_CAPTURES', self.expected)

    def run_gate(self):
        with contextlib.redirect_stdout(io.StringIO()):
            verify_evidence.main()

    def test_control_pair_passes(self):
        self.run_gate()

    def test_swapped_captures_are_rejected(self):
        # Swap the whole folders: payloads and hashes stay self-consistent, so only
        # the program/folder binding can catch the exchange.
        original = self.tmp / 'evidence/original'
        (original / 'pump').rename(original / 'swap')
        (original / 'pump_amm').rename(original / 'pump')
        (original / 'swap').rename(original / 'pump_amm')
        with self.assertRaisesRegex(AssertionError, 'evidence/original/pump: capture program'):
            self.run_gate()


class ProgramDataAuthorityTagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workspace = tempfile.TemporaryDirectory()
        cls.addClassCleanup(workspace.cleanup)
        cls.root = pathlib.Path(workspace.name)
        (cls.root / 'scripts').mkdir()
        for name in ('verify_evidence.py', 'capture.py', 'analyze.py'):
            shutil.copyfile(analyze.ROOT / 'scripts' / name, cls.root / 'scripts' / name)
        shutil.copytree(analyze.ROOT / 'evidence/upstream', cls.root / 'evidence/upstream')
        for relative in verify_evidence.EXPECTED_CAPTURES:
            shutil.copytree(analyze.ROOT / relative, cls.root / relative)
        cls.folder = cls.root / 'evidence/original/pump_fees'
        cls.original_data = (cls.folder / 'programdata-account.bin').read_bytes()
        cls.original_record = json.loads((cls.folder / 'capture.json').read_text())

    def verify_tag(self, tag, optimized):
        data = bytearray(self.original_data)
        data[12] = tag
        record = dict(self.original_record)
        # Keep hashes and declared authority consistent so the tag itself is tested.
        record['programdata_sha256'] = hashlib.sha256(data).hexdigest()
        record['upgrade_authority'] = b58(data[13:45]) if tag else None
        (self.folder / 'programdata-account.bin').write_bytes(data)
        (self.folder / 'capture.json').write_text(json.dumps(record))
        command = [sys.executable, *(['-O'] if optimized else []), 'scripts/verify_evidence.py']
        return subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=30)

    def test_valid_authority_option_tags(self):
        for tag in (0, 1):
            for optimized in (False, True):
                with self.subTest(tag=tag, optimized=optimized):
                    result = self.verify_tag(tag, optimized)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('9 captures verified', result.stdout)

    def test_invalid_authority_option_tags(self):
        for tag in (2, 255):
            for optimized in (False, True):
                with self.subTest(tag=tag, optimized=optimized):
                    result = self.verify_tag(tag, optimized)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn('invalid ProgramData upgrade authority option tag', result.stderr)
                    self.assertIn('evidence/original/pump_fees', result.stderr)


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
        baseline = scorer.load_baseline(scorer.SC / 'pump-main/baseline/score.json')
        lost = {address: dict(window) for address, window in baseline.items()}
        lost[0x120] = {'normalized': False, 'raw': False, 'symbols': [], 'bytes': 176}
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


class UpstreamEvidenceSetTests(unittest.TestCase):
    """verify_evidence.py must not take the upstream IDL set from the data it checks."""

    def run_gate(self, root):
        import contextlib
        import io
        import verify_evidence
        with patch.object(verify_evidence, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
            verify_evidence.main()

    def copy_evidence(self, temporary):
        import shutil
        import verify_evidence
        root = Path(temporary)
        shutil.copytree(verify_evidence.ROOT / 'evidence', root / 'evidence')
        self.run_gate(root)  # control: the unmodified copy passes
        return root

    def rewrite_listing(self, root, change):
        import json
        provenance = root / 'evidence/upstream/provenance.json'
        record = json.loads(provenance.read_bytes())
        change(record['file_sha256'])
        provenance.write_bytes((json.dumps(record, indent=2) + '\n').encode())

    def test_removed_idl_and_listing_entry_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_evidence(temporary)
            (root / 'evidence/upstream/pump_fees.json').unlink()
            self.rewrite_listing(root, lambda files: files.pop('pump_fees.json'))
            with self.assertRaisesRegex(AssertionError, r"missing .*'pump_fees\.json'"):
                self.run_gate(root)

    def test_unexpected_listing_entry_is_rejected(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_evidence(temporary)
            extra = root / 'evidence/upstream/pump_extra.json'
            extra.write_bytes(b'{}\n')
            digest = hashlib.sha256(extra.read_bytes()).hexdigest()
            self.rewrite_listing(root, lambda files: files.update({'pump_extra.json': digest}))
            with self.assertRaisesRegex(AssertionError, r"unexpected .*'pump_extra\.json'"):
                self.run_gate(root)


class EndianDecodeTests(unittest.TestCase):
    def test_conversion_direction_and_width(self):
        for opcode, direction in ((0xd4, 'le'), (0xdc, 'be')):
            for width in (16, 32, 64):
                with self.subTest(direction=direction, width=width):
                    blob = struct.pack('<BBhi', opcode, 5, 0, width)
                    record, size = deep_disassembly.decode_instruction(blob, 0, None)
                    self.assertEqual(record['mnemonic'], f'{direction}{width} r5')
                    self.assertEqual(record['imm'], width)
                    self.assertEqual(record['hex'], blob.hex())
                    self.assertEqual(size, 8)

    def test_other_alu_operand_forms_are_unchanged(self):
        for opcode, regs, immediate, mnemonic in (
            (0x04, 5, 16, 'add32 r5, 16'),
            (0x0c, 0x35, 0, 'add32 r5, r3'),
        ):
            with self.subTest(opcode=opcode):
                blob = struct.pack('<BBhi', opcode, regs, 0, immediate)
                record, _ = deep_disassembly.decode_instruction(blob, 0, None)
                self.assertEqual(record['mnemonic'], mnemonic)

    def test_captured_big_endian_conversions(self):
        for relative in ('original/mayhem', 'dependencies/spl_token_2022'):
            with self.subTest(capture=relative):
                elf = deep_disassembly.Elf(
                    analyze.ROOT / 'evidence' / relative / 'deployed.so')
                offset = elf.lo
                widths = []
                while offset < elf.hi:
                    record, size = deep_disassembly.decode_instruction(elf.b, offset, elf)
                    if elf.b[offset] == 0xdc:
                        widths.append(record['imm'])
                        self.assertEqual(record['mnemonic'],
                                         f"be{record['imm']} r{record['dst']}")
                    offset += size
                self.assertEqual(sorted(widths), [16] + [32] * 7)


class MemoryWidthDecodeTests(unittest.TestCase):
    # Explicit instruction spellings from SBPF's LD/ST/STX definitions,
    # including word operations whose spelling was already correct.
    FORMS = {
        0x61: 'ldxw', 0x69: 'ldxh', 0x71: 'ldxb', 0x79: 'ldxdw',
        0x62: 'stw', 0x6a: 'sth', 0x72: 'stb', 0x7a: 'stdw',
        0x63: 'stxw', 0x6b: 'stxh', 0x73: 'stxb', 0x7b: 'stxdw',
    }

    def test_all_load_and_store_widths_preserve_operands(self):
        for opcode, operation in self.FORMS.items():
            with self.subTest(opcode=hex(opcode)):
                cls = opcode & 7
                regs = 5 if cls == 2 else 0x35
                blob = struct.pack('<BBhi', opcode, regs, -16, 7)
                record, size = deep_disassembly.decode_instruction(blob, 0, None)
                if cls == 1:
                    expected = f'{operation} r5, [r3-16]'
                elif cls == 2:
                    expected = f'{operation} [r5-16], 7'
                else:
                    expected = f'{operation} [r5-16], r3'
                self.assertEqual(record['mnemonic'], expected)
                self.assertTrue(record['memory_access'])
                self.assertEqual((record['dst'], record['src'], record['off'], record['imm']),
                                 (5, regs >> 4, -16, 7))
                self.assertEqual(record['hex'], blob.hex())
                self.assertEqual(size, 8)

    def test_memory_widths_in_all_four_captured_programs(self):
        for name in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
            with self.subTest(program=name):
                elf = deep_disassembly.Elf(
                    analyze.ROOT / 'evidence/original' / name / 'deployed.so')
                offset = elf.lo
                seen = set()
                mismatches = 0
                while offset < elf.hi:
                    record, size = deep_disassembly.decode_instruction(elf.b, offset, elf)
                    opcode = elf.b[offset]
                    if opcode in self.FORMS:
                        seen.add(opcode)
                        mismatches += record['mnemonic'].split()[0] != self.FORMS[opcode]
                    offset += size
                self.assertEqual(seen, set(self.FORMS))
                self.assertEqual(mismatches, 0)


if __name__=='__main__': unittest.main()
