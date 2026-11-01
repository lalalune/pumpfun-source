"""Paired ELF admission and residual tests for stack_register_provenance.py."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import types
import unittest

import stack_register_provenance as paired
from test_residual_analysis import elf_fixture


def instruction(opcode, dst=0, src=0, displacement=0, immediate=0):
    return struct.pack('<BBhi', opcode, dst | (src << 4), displacement, immediate)


EXIT = instruction(0x95)


def analyze_codes(original_code, candidate_code):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        original, candidate = root / 'original.so', root / 'candidate.so'
        original.write_bytes(elf_fixture(original_code))
        candidate.write_bytes(elf_fixture(candidate_code))
        return paired.analyze_pair(
            original, candidate,
            {'exact_window': (0x1000, len(original_code)), 'exact_symbol': None},
            {'exact_window': (0x1000, len(candidate_code)), 'exact_symbol': None})


class PairComparisonTests(unittest.TestCase):
    def test_moved_derived_frame_slot_is_reported_as_heuristic(self):
        original = b''.join([instruction(0xbf, 2, 10), instruction(0x07, 2, immediate=-16),
                             instruction(0x79, 1, 2, 8), EXIT])
        candidate = b''.join([instruction(0xbf, 2, 10), instruction(0x07, 2, immediate=-24),
                              instruction(0x79, 1, 2, 8), EXIT])
        report = analyze_codes(original, candidate)
        rows = report['heuristic_correspondences']['stack_frame_residuals']['rows']
        moved = next(row for row in rows if row['kind'] == 'moved_frame_slot')
        self.assertEqual((moved['original_stack_offset'], moved['candidate_stack_offset']), (-8, -16))
        self.assertEqual(moved['classification'], 'heuristic_correspondence')
        self.assertEqual(report['register_state_summaries']['original']['derived_stack_accesses'], 1)
        actionable = report['actionable_comparison_locations'][0]
        self.assertEqual(actionable['kind'], 'moved_frame_slot')
        self.assertEqual(actionable['original_address'], 0x1000 + moved['original_instruction_offset'])

    def test_access_width_difference_is_visible(self):
        prefix = instruction(0xbf, 2, 10) + instruction(0x07, 2, immediate=-16)
        report = analyze_codes(prefix + instruction(0x79, 1, 2) + EXIT,
                               prefix + instruction(0x61, 1, 2) + EXIT)
        rows = report['heuristic_correspondences']['stack_frame_residuals']['rows']
        width = next(row for row in rows if row['kind'] == 'access_width_difference')
        self.assertEqual((width['original_width'], width['candidate_width']), (8, 4))

    def test_original_only_operation_is_not_misrepresented_as_exact(self):
        prefix = instruction(0xbf, 2, 10)
        report = analyze_codes(prefix + instruction(0x79, 1, 2) + EXIT, prefix + EXIT)
        rows = report['heuristic_correspondences']['stack_frame_residuals']['rows']
        only = next(row for row in rows if row['kind'] == 'original_only_stack_operation')
        self.assertEqual(only['confidence'], 'low')
        self.assertIn('heuristic', only['note'])

    def test_identical_pair_has_exact_facts_without_frame_residuals(self):
        code = instruction(0xbf, 1, 10) + instruction(0x79, 2, 1, -8) + EXIT
        report = analyze_codes(code, code)
        self.assertTrue(report['identity']['raw_equal'])
        self.assertEqual(report['heuristic_correspondences']['stack_frame_residuals']['count'], 0)
        self.assertEqual(report['exact_facts']['original']['stack_accesses']['counts'], {'proven': 1})
        self.assertEqual(set(report['analyzer_source']['files']), set(paired.SOURCE_FILES))
        self.assertRegex(report['analyzer_source']['manifest_sha256'], r'^[0-9a-f]{64}$')

    def test_expected_hashes_bind_both_elf_snapshots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original, candidate = root / 'original.so', root / 'candidate.so'
            original.write_bytes(elf_fixture(EXIT)); candidate.write_bytes(elf_fixture(EXIT))
            digest = hashlib.sha256(original.read_bytes()).hexdigest()
            selectors = {'exact_window': (0x1000, 8), 'exact_symbol': None}
            report = paired.analyze_pair(original, candidate, selectors, selectors,
                                         expected_original_sha256=digest,
                                         expected_candidate_sha256=digest)
            self.assertEqual(report['inputs']['original']['sha256'], digest)
            with self.assertRaisesRegex(ValueError, 'candidate SHA-256'):
                paired.analyze_pair(original, candidate, selectors, selectors,
                                    expected_candidate_sha256='0' * 64)


class CliAdmissionTests(unittest.TestCase):
    def command(self, original, candidate, *extra):
        return [sys.executable, '-B', str(Path(__file__).with_name('stack_register_provenance.py')),
                str(original), str(candidate), '--original-window', '0x1000:8',
                '--candidate-window', '0x1000:8', *extra]

    def test_json_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original, candidate = root / 'original.so', root / 'candidate.so'
            original.write_bytes(elf_fixture(EXIT)); candidate.write_bytes(elf_fixture(EXIT))
            first = subprocess.run(self.command(original, candidate), capture_output=True, text=True, check=True)
            second = subprocess.run(self.command(original, candidate), capture_output=True, text=True, check=True)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(json.loads(first.stdout)['schema'], paired.SCHEMA)

    def test_output_cannot_alias_or_replace_an_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original, candidate = root / 'original.so', root / 'candidate.so'
            original.write_bytes(elf_fixture(EXIT)); candidate.write_bytes(elf_fixture(EXIT))
            retained = candidate.read_bytes()
            result = subprocess.run(self.command(original, candidate, '--json', str(candidate)),
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)


            self.assertEqual(candidate.read_bytes(), retained)
            output = root / 'report.json'
            output.write_text('retained\n')
            collision = subprocess.run(self.command(original, candidate, '--json', str(output)),
                                       capture_output=True, text=True)
            self.assertEqual(collision.returncode, 2)
            self.assertEqual(output.read_text(), 'retained\n')

    def test_malformed_elf_and_invalid_symbol_boundary_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original, candidate = root / 'original.so', root / 'candidate.so'
            original.write_bytes(b'not an elf'); candidate.write_bytes(elf_fixture(EXIT))
            result = subprocess.run(self.command(original, candidate), capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            original.write_bytes(elf_fixture(EXIT))
            malformed = bytearray(elf_fixture(instruction(0x18) + bytes(8)))
            # Force the selected symbol to split the two-slot LDDW.
            struct.pack_into('<Q', malformed, len(malformed) - 8, 8)
            candidate.write_bytes(malformed)
            result = subprocess.run(self.command(original, candidate), capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)



class ExecutedSourceAdmissionTests(unittest.TestCase):
    def private_copy(self, root):
        import shutil
        for name in paired.SOURCE_FILES:
            shutil.copyfile(Path(__file__).parent / name, root / name)
        return root / 'stack_register_provenance.py'

    def load(self, path):
        module = types.ModuleType('_private_stack_provenance_test')
        module.__file__ = str(path)
        raw = path.read_bytes()
        module.__dict__['_ADMITTED_SOURCE_BYTES'] = raw
        exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
        return module

    def test_preexisting_canonical_analyzer_alias_cannot_replace_raw_source(self):
        fake = types.ModuleType('sbpf_provenance')
        fake.analyze = lambda *args: {'forged': True}
        fake.public_analysis = lambda value: value
        prior = sys.modules.get('sbpf_provenance')
        sys.modules['sbpf_provenance'] = fake
        try:
            with tempfile.TemporaryDirectory() as temporary:
                path = self.private_copy(Path(temporary))
                loaded = self.load(path)
                self.assertIs(sys.modules['sbpf_provenance'], fake)
                self.assertEqual(loaded.analyze(EXIT)['instruction_count'], 1)
        finally:
            if prior is None:
                sys.modules.pop('sbpf_provenance', None)
            else:
                sys.modules['sbpf_provenance'] = prior

    def test_source_change_fails_before_opening_elf_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            loaded = self.load(self.private_copy(root))
            source = root / 'sbpf_provenance.py'
            source.write_bytes(source.read_bytes() + b'\n# changed after source admission\n')
            selector = {'exact_window': (0x1000, 8), 'exact_symbol': None}
            with self.assertRaisesRegex(ValueError, 'executed source input changed'):
                loaded.analyze_pair(root / 'missing-original', root / 'missing-candidate', selector, selector)

    def test_compiled_self_hash_is_captured_before_dependency_bootstrap(self):
        import builtins
        with tempfile.TemporaryDirectory() as temporary:
            path = self.private_copy(Path(temporary))
            raw = path.read_bytes()
            proxy = types.ModuleType('types')
            proxy.__dict__.update(vars(types))
            changed = []
            def make_module(*args, **kwargs):
                if not changed:
                    path.write_bytes(raw + b'\n# concurrent bootstrap edit\n')
                    changed.append(True)
                return types.ModuleType(*args, **kwargs)
            proxy.ModuleType = make_module
            def importing(name, globals=None, locals=None, fromlist=(), level=0):
                return proxy if name == 'types' and level == 0 else builtins.__import__(name, globals, locals, fromlist, level)
            namespace = {'__file__': str(path), '__name__': '_bootstrap_edit_control',
                         '_ADMITTED_SOURCE_BYTES': raw,
                         '__builtins__': dict(vars(builtins), __import__=importing)}
            with self.assertRaisesRegex(ValueError, 'executed source input changed: stack_register_provenance.py'):
                exec(compile(raw, str(path), 'exec', dont_inherit=True), namespace)
            self.assertTrue(changed)

    def test_actual_cli_ignores_proven_executable_caches_in_all_optimization_modes(self):
        import importlib.util
        import os
        import py_compile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.private_copy(root)
            code = instruction(0xbf, 1, 10) + instruction(0x79, 2, 1, -8) + EXIT
            original, candidate = root / 'original.so', root / 'candidate.so'
            original.write_bytes(elf_fixture(code)); candidate.write_bytes(elf_fixture(code))
            retained = None
            for level, flags in ((0, []), (1, ['-O']), (2, ['-OO'])):
                markers = []
                for name in ('sbpf_provenance', 'control_flow'):
                    source = root / (name + '.py')
                    clean = source.read_bytes()
                    marker = root / (name + '-cache-executed')
                    markers.append(marker)
                    malicious = ('from pathlib import Path\nPath(' + repr(str(marker)) + ").write_text('bad')\n").encode()
                    malicious += b'#' * (len(clean) - len(malicious))
                    self.assertEqual(len(malicious), len(clean))
                    source.write_bytes(malicious)
                    os.utime(source, (1700000000, 1700000000))
                    py_compile.compile(str(source), doraise=True, optimize=level)
                    source.write_bytes(clean)
                    os.utime(source, (1700000000, 1700000000))
                    control = ('import importlib.util; p=' + repr(str(source)) + '; '
                               "s=importlib.util.spec_from_file_location('_cache_control',p); "
                               'm=importlib.util.module_from_spec(s); s.loader.exec_module(m)')
                    subprocess.run([sys.executable, '-I', '-B', *flags, '-c', control], check=True)
                    self.assertTrue(marker.exists(), 'control did not execute timestamp cache')
                    marker.unlink()
                result = subprocess.run([sys.executable, '-I', '-B', *flags, str(path), str(original),
                                         str(candidate), '--original-window', '0x1000:24',
                                         '--candidate-window', '0x1000:24'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(any(marker.exists() for marker in markers))
                report = json.loads(result.stdout)
                self.assertEqual(report['register_state_summaries']['original']['proven_stack_accesses'], 1)
                if retained is not None:
                    self.assertEqual(result.stdout, retained)
                retained = result.stdout


if __name__ == '__main__':
    unittest.main()
