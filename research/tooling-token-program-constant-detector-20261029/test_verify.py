"""Regression controls for the token-program constant detector."""
from pathlib import Path
import gzip
import hashlib
import json
import struct
import shutil
import sys
import tempfile
from unittest.mock import patch
import types
import unittest

import proof

P = Path(__file__).resolve().parent


def lddw(value):
    low = value & 0xFFFFFFFF
    high = value >> 32
    return struct.pack('<BBhI', 0x18, 0, 0, low) + struct.pack('<II', 0, high)


def store():
    return struct.pack('<BBhi', 0x7b, 0x1a, -8, 0)


def image(*chunks):
    return b''.join(lddw(chunk) + store() for chunk in (
        int.from_bytes(chunk, 'little') for chunk in chunks
    ))


class TokenDetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archived = proof._reviewed()
        cls.report = proof.check(proof.REPO)

    def test_real_corpus_is_zero_for_the_small_constant_heuristic(self):
        for name, row in self.report['programs'].items():
            self.assertEqual(row['old_rows'], 0, name)
            self.assertEqual(row['old_windows'], 0, name)
            self.assertGreater(row['new_rows'], 0, name)

    def test_real_counts(self):
        totals = self.report['totals']
        self.assertEqual(totals['new_rows'], 29)
        self.assertEqual(totals['new_windows'], 19)
        self.assertEqual((totals['Tokenkeg'], totals['Tokenz']), (23, 6))

    def test_four_chunks_form_a_token_program_constant(self):
        token = proof.TOKEN_PROGRAMS['Tokenkeg']
        chunks = [token[index:index + 8] for index in range(0, 32, 8)]
        elf = types.SimpleNamespace(b=image(*chunks))
        rows = proof.token_constants(elf, 0, len(elf.b))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['token_program'], 'Tokenkeg')
        self.assertEqual(rows[0]['lddw_slots'], 4)

    def test_three_chunks_are_not_a_program_constant(self):
        token = proof.TOKEN_PROGRAMS['Tokenkeg']
        chunks = [token[index:index + 8] for index in range(0, 24, 8)]
        elf = types.SimpleNamespace(b=image(*chunks))
        self.assertEqual(proof.token_constants(elf, 0, len(elf.b)), [])

    def test_wrong_fourth_chunk_is_not_a_program_constant(self):
        token = proof.TOKEN_PROGRAMS['Tokenkeg']
        chunks = [token[index:index + 8] for index in range(0, 32, 8)]
        chunks[-1] = bytes(8)
        elf = types.SimpleNamespace(b=image(*chunks))
        self.assertEqual(proof.token_constants(elf, 0, len(elf.b)), [])

    def test_small_numeric_constants_are_not_token_programs(self):
        elf = types.SimpleNamespace(b=image(*([struct.pack('<Q', 3)] * 4)))
        self.assertEqual(proof.token_constants(elf, 0, len(elf.b)), [])

    def test_saved_observations_match(self):
        saved = json.loads(gzip.decompress((P / 'observations.json.gz').read_bytes()))
        self.assertEqual(saved, self.report)

    def test_manifest_inventory(self):
        saved = json.loads((P / 'manifest.json').read_text(encoding='utf-8'))
        actual = {
            path.relative_to(P).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(P.rglob('*'))
            if path.is_file() and path.name != 'manifest.json'
            and '__pycache__' not in path.parts and path.suffix != '.pyc'
        }
        self.assertEqual(saved, actual)

    def test_publisher_refuses_optimized_python(self):
        # The corpus-count gates in check() are bare asserts, so seal() used
        # to re-publish the packet under python -O with every check stripped;
        # verify.py already refused, the publisher must too.
        import os
        import subprocess
        import sys
        for argv, environment in (
            ([sys.executable, '-O', str(P / 'proof.py')], None),
            ([sys.executable, str(P / 'proof.py')],
             dict(os.environ, PYTHONOPTIMIZE='1')),
        ):
            with self.subTest(argv=argv[1:], env=bool(environment)):
                completed = subprocess.run(argv, cwd=P, env=environment,
                                           capture_output=True, text=True)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn('Normal Python is required', completed.stderr)


    def test_packet_io_pins_utf8(self):
        # #1731 discipline: the sibling packet pins encoding='utf-8' on every
        # text read and write; a bare call inherits the host locale.
        verify = (P / 'verify.py').read_text(encoding='utf-8')
        proof = (P / 'proof.py').read_text(encoding='utf-8')
        for name in ('manifest.json', 'inputs.json', 'coverage-delta.json'):
            self.assertIn("(P / '%s').read_text(encoding='utf-8')" % name, verify)
        self.assertNotIn('read_text()', verify)
        self.assertEqual(proof.count("encoding='utf-8'"), 2)


    def retained_root(self, with_images=False):
        temporary = tempfile.TemporaryDirectory(prefix='token-detector-root-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative in (proof.ARCHIVED, proof.READER):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(proof.REPO / relative, target)
        if with_images:
            for name in proof.PROGRAMS:
                relative = Path('evidence/original') / name / 'deployed.so'
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(proof.REPO / relative, target)
        return root

    def test_both_archived_sources_are_checked_before_execution(self):
        for relative, message in [(proof.ARCHIVED, 'bytecode-pattern source'),
                                  (proof.READER, 'ELF reader source')]:
            with self.subTest(source=relative):
                root = self.retained_root()
                path = root / relative
                path.write_bytes(path.read_bytes() + b'\nraise RuntimeError("must not execute")\n')
                with self.assertRaisesRegex(ValueError, message):
                    proof._reviewed(root)

    def test_explicit_root_uses_its_archives_and_ignores_live_reader_module(self):
        root = self.retained_root(with_images=True)
        fake = types.ModuleType('window_elf_reader')
        fake.Elf = lambda path: self.fail('live reader was used')
        with patch.object(proof, 'REPO', root / 'missing-global-root'), \
                patch.dict(sys.modules, {'window_elf_reader': fake}):
            report = proof.check(root)
            self.assertIs(sys.modules['window_elf_reader'], fake)
        self.assertEqual(report, self.report)

    def test_report_hash_identifies_executed_source_after_path_changes(self):
        root = self.retained_root(with_images=True)
        load = proof._reviewed

        def load_then_change(path):
            module = load(path)
            source = path / proof.ARCHIVED
            source.write_bytes(source.read_bytes() + b'\n# changed after capture\n')
            return module

        with patch.object(proof, '_reviewed', side_effect=load_then_change):
            report = proof.check(root)
        self.assertEqual(report, self.report)
        self.assertNotEqual(hashlib.sha256((root / proof.ARCHIVED).read_bytes()).hexdigest(),
                            report['script_sha256'])

    def test_bound_helper_is_pinned_in_the_packet(self):
        # The live scripts/ copy evolved after sealing and broke the inputs
        # binding on main; the packet now pins the exact revision it measured.
        for name, digest in [('bytecode_signatures.py', proof.LF_SHA256),
                             ('window_elf_reader.py', proof.READER_SHA256)]:
            archived = P / 'archived' / name
            self.assertTrue(archived.is_file())
            self.assertEqual(hashlib.sha256(archived.read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main(verbosity=2)
