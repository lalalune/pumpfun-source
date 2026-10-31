"""Regression tests for input path confinement, row offset checks, and .text bounds in sbpf_disassembly_roundtrip."""

import gzip
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import sbpf_disassembly_inventory as inventory
import sbpf_disassembly_roundtrip as roundtrip


class SbpfRoundtripInputAdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / 'repo'
        self.root.mkdir()
        self.outside_dir = self.base / 'outside'
        self.outside_dir.mkdir()
        self.tool = self.root / 'tool/target/release/sbpf'
        self.tool.parent.mkdir(parents=True)
        self.tool.write_bytes(b'admitted executable')
        self.tool.chmod(0o700)
        self.elf_bytes = bytes(64) + struct.pack('<BBhi', 0x95, 0, 0, 0)
        self.original = self.root / 'original.so'
        self.original.write_bytes(self.elf_bytes)
        self.outside_elf = self.outside_dir / 'outside.so'
        self.outside_elf.write_bytes(self.elf_bytes)
        self.inputs = self.root / 'inventory'
        self.inputs.mkdir()

    def _save_entry(self, record, name='pump'):
        compressed = gzip.compress(
            __import__('json').dumps(record).encode('utf-8'),
            mtime=0,
        )
        (self.inputs / f'{name}.json.gz').write_bytes(compressed)
        return {'name': name, 'inventory_sha256': inventory.sha(compressed)}

    @staticmethod
    def _valid_sections(data):
        return {'.text': (0, 1, 6, 64, 64, len(data) - 64, 0, 0, 8, 0)}

    def _assembler_ok(self, command, **kwargs):
        folder = Path(command[command.index('--deploy-dir') + 1])
        folder.mkdir(parents=True)
        (folder / 'reference-derived.so').write_bytes(self.elf_bytes)
        return subprocess.CompletedProcess(command, 0, b'', b'')

    def test_outside_absolute_traversal_and_drive_inputs_are_rejected_before_assembler(self):
        cases = [
            ('absolute path', str(self.outside_elf)),
            ('dotdot traversal', '../outside/outside.so'),
            ('nested dotdot', 'sub/../../outside/outside.so'),
            ('windows drive path', 'C:\\outside\\outside.so'),
            ('empty path', ''),
            ('dot path', '.'),
        ]
        (self.root / 'sub').mkdir()
        for idx, (label, bad_input) in enumerate(cases):
            with self.subTest(label):
                record = {
                    'input': bad_input,
                    'input_sha256': inventory.sha(self.elf_bytes),
                    'instructions': [
                        {'file_offset': 64, 'opcode': 0x95, 'src': 0, 'immediate': 0, 'assembly': 'exit'},
                    ],
                }
                entry = self._save_entry(record)
                out = self.root / f'out-{idx}'
                out.mkdir()
                with patch.object(roundtrip, 'ROOT', self.root), \
                        patch.object(roundtrip, 'sections', self._valid_sections), \
                        patch.object(roundtrip.subprocess, 'run', side_effect=self._assembler_ok) as run_mock:
                    with self.assertRaises(ValueError):
                        roundtrip.roundtrip(self.tool, self.inputs, entry, out)
                    run_mock.assert_not_called()

    def test_symlinked_and_fifo_inputs_are_rejected_before_assembler(self):
        link_file = self.root / 'linked.so'
        try:
            link_file.symlink_to(self.original)
        except OSError as error:
            if getattr(error, 'winerror', None) == 1314:
                self.skipTest('symlink privilege unavailable')
            raise
        link_dir = self.root / 'linked_dir'
        link_dir.symlink_to(self.outside_dir, target_is_directory=True)

        for idx, bad_input in enumerate(['linked.so', 'linked_dir/outside.so']):
            with self.subTest(input=bad_input):
                record = {
                    'input': bad_input,
                    'input_sha256': inventory.sha(self.elf_bytes),
                    'instructions': [
                        {'file_offset': 64, 'opcode': 0x95, 'src': 0, 'immediate': 0, 'assembly': 'exit'},
                    ],
                }
                entry = self._save_entry(record)
                out = self.root / f'out-link-{idx}'
                out.mkdir()
                with patch.object(roundtrip, 'ROOT', self.root), \
                        patch.object(roundtrip, 'sections', self._valid_sections), \
                        patch.object(roundtrip.subprocess, 'run', side_effect=self._assembler_ok) as run_mock:
                    with self.assertRaises(ValueError):
                        roundtrip.roundtrip(self.tool, self.inputs, entry, out)
                    run_mock.assert_not_called()

        if hasattr(os, 'mkfifo'):
            fifo = self.root / 'pipe.so'
            os.mkfifo(fifo)
            record = {
                'input': 'pipe.so',
                'input_sha256': inventory.sha(self.elf_bytes),
                'instructions': [
                    {'file_offset': 64, 'opcode': 0x95, 'src': 0, 'immediate': 0, 'assembly': 'exit'},
                ],
            }
            entry = self._save_entry(record)
            out = self.root / 'out-fifo'
            out.mkdir()
            real_read_bytes = Path.read_bytes

            def safe_read_bytes(path_obj):
                if path_obj == fifo:
                    return self.elf_bytes
                return real_read_bytes(path_obj)

            with patch.object(roundtrip, 'ROOT', self.root), \
                    patch.object(Path, 'read_bytes', safe_read_bytes), \
                    patch.object(roundtrip, 'sections', self._valid_sections), \
                    patch.object(roundtrip.subprocess, 'run', side_effect=self._assembler_ok) as run_mock:
                with self.assertRaises(ValueError):
                    roundtrip.roundtrip(self.tool, self.inputs, entry, out)
                run_mock.assert_not_called()

    def test_negative_boolean_and_duplicate_file_offsets_are_rejected(self):
        bad_instruction_sets = [
            ('negative file_offset', [
                {'file_offset': -8, 'opcode': 0x85, 'src': 1, 'immediate': -1, 'assembly': 'call -0x1'},
            ]),
            ('duplicate file_offsets', [
                {'file_offset': 64, 'opcode': 0x95, 'src': 0, 'immediate': 0, 'assembly': 'exit'},
                {'file_offset': 64, 'opcode': 0x95, 'src': 0, 'immediate': 0, 'assembly': 'exit'},
            ]),
            ('boolean file_offset', [
                {'file_offset': True, 'opcode': 0x95, 'src': 0, 'immediate': 0, 'assembly': 'exit'},
            ]),
        ]
        for idx, (label, rows) in enumerate(bad_instruction_sets):
            with self.subTest(label):
                record = {
                    'input': 'original.so',
                    'input_sha256': inventory.sha(self.elf_bytes),
                    'instructions': rows,
                }
                entry = self._save_entry(record)
                out = self.root / f'out-rows-{idx}'
                out.mkdir()
                with patch.object(roundtrip, 'ROOT', self.root), \
                        patch.object(roundtrip, 'sections', self._valid_sections), \
                        patch.object(roundtrip.subprocess, 'run', side_effect=self._assembler_ok) as run_mock:
                    with self.assertRaises(ValueError):
                        roundtrip.roundtrip(self.tool, self.inputs, entry, out)
                    run_mock.assert_not_called()

    def test_nobits_missing_and_out_of_bounds_text_sections_raise_value_error(self):
        bad_sections = [
            ('SHT_NOBITS .text', lambda data: {'.text': (0, 8, 6, 64, 64, 8, 0, 0, 8, 0)}),
            ('out-of-bounds .text', lambda data: {'.text': (0, 1, 6, 64, 64, 9999, 0, 0, 8, 0)}),
            ('missing .text', lambda data: {}),
        ]
        for idx, (label, section_fn) in enumerate(bad_sections):
            with self.subTest(label):
                record = {
                    'input': 'original.so',
                    'input_sha256': inventory.sha(self.elf_bytes),
                    'instructions': [
                        {'file_offset': 64, 'opcode': 0x95, 'src': 0, 'immediate': 0, 'assembly': 'exit'},
                    ],
                }
                entry = self._save_entry(record)
                out = self.root / f'out-sec-{idx}'
                out.mkdir()
                with patch.object(roundtrip, 'ROOT', self.root), \
                        patch.object(roundtrip, 'sections', section_fn), \
                        patch.object(roundtrip.subprocess, 'run', side_effect=self._assembler_ok):
                    with self.assertRaises(ValueError):
                        roundtrip.roundtrip(self.tool, self.inputs, entry, out)

        short_elf = self.root / 'short.so'
        short_elf.write_bytes(b'\x7fELFshort')
        record = {
            'input': 'short.so',
            'input_sha256': inventory.sha(short_elf.read_bytes()),
            'instructions': [],
        }
        entry = self._save_entry(record)
        out = self.root / 'out-short'
        out.mkdir()
        with patch.object(roundtrip, 'ROOT', self.root), \
                patch.object(roundtrip.subprocess, 'run', side_effect=self._assembler_ok) as run_mock:
            with self.assertRaises(ValueError):
                roundtrip.roundtrip(self.tool, self.inputs, entry, out)
            run_mock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
