"""Candidate rebuilds must not change the disassembly shown beside old tokens."""
import os
import io
import contextlib
from types import SimpleNamespace
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from test_elf_symbols import fixture
import win

class DisassemblySnapshotTests(unittest.TestCase):
    def test_replaced_or_removed_candidate_uses_loaded_bytes_and_cleans_up(self):
        original = bytes(fixture())
        for remove in (False, True):
            with self.subTest(remove=remove), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'build.so'
                path.write_bytes(original)
                candidate = win.Cand(path)
                if remove: path.unlink()
                else: path.write_bytes(b'rebuilt')
                paths = []
                def observe(snapshot, start, end):
                    paths.append(snapshot)
                    self.assertEqual(snapshot.read_bytes(), original)
                    self.assertEqual((start, end), (0x1000, 0x1008))
                    return {start: 'snapshot instruction'}
                with patch.object(win, 'objdump_text', observe):
                    self.assertEqual(candidate.disassembly(0x1000, 8), {0x1000: 'snapshot instruction'})
                self.assertFalse(paths[0].exists())

    def test_disassembler_failure_removes_temporary_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'candidate.so'
            path.write_bytes(fixture())
            candidate = win.Cand(path)
            paths = []
            def fail(snapshot, start, end):
                paths.append(snapshot)
                raise RuntimeError('disassembler failed')
            with patch.object(win, 'objdump_text', fail), self.assertRaisesRegex(RuntimeError, 'disassembler failed'):
                candidate.disassembly(0x1000, 8)
            self.assertFalse(paths[0].exists())

    @unittest.skipUnless(os.environ.get('PUMP_OBJDUMP'), 'requires an explicit SBF llvm-objdump')
    def test_real_objdump_reads_old_instruction_after_rebuild(self):
        first = fixture()
        first[424:432] = struct.pack('<BBhi', 0xb7, 0, 0, 111)
        second = bytearray(first)
        second[424:432] = struct.pack('<BBhi', 0xb7, 0, 0, 222)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'candidate.so'
            path.write_bytes(first)
            candidate = win.Cand(path)
            expected = win.objdump_text(path, 0x1000, 0x1008)
            self.assertTrue(expected)
            path.write_bytes(second)
            self.assertNotEqual(expected, win.objdump_text(path, 0x1000, 0x1008))
            # Exercise the actual show command with a retained original window,
            # real ELF parsing and real LLVM. Only rebuild timing is injected.
            path.write_bytes(first)
            load = win.Cand
            disassemble = win.objdump_text
            observed = []
            def rebuild_after_load(value):
                loaded = load(value)
                path.write_bytes(second)
                return loaded
            def observe(value, start, end):
                result = disassemble(value, start, end)
                if start == 0x1000: observed.append(result)
                return result
            args = SimpleNamespace(start=hex(win.original_windows()[0]['start']),
                                   cand=path, sym='^local$', context=0, full=True)
            with patch.object(win, 'Cand', rebuild_after_load), patch.object(win, 'objdump_text', observe), contextlib.redirect_stdout(io.StringIO()):
                win.cmd_show(args)
            self.assertEqual(observed, [expected])


if __name__ == '__main__': unittest.main()
