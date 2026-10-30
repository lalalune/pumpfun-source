"""LLVM's BPF/SBF decimal instruction indices are not hex byte addresses."""
import os
import io
import contextlib
from types import SimpleNamespace
from pathlib import Path
import unittest
from unittest.mock import patch
import win

class ObjdumpAddressTests(unittest.TestCase):
    def test_sbf_and_bpf_instruction_indices_become_byte_addresses(self):
        for target in ('sbf', 'bpf'):
            output = f'candidate.so: file format elf64-{target}\n  36: lddw r0, 0x100\n  38: exit\n'
            with patch.object(win, 'objdump', return_value='llvm-objdump'), patch.object(win.subprocess, 'check_output', return_value=output):
                self.assertEqual(win.objdump_text(Path('candidate.so'), 0x120, 0x138), {0x120: 'lddw r0, 0x100', 0x130: 'exit'})

    def test_legacy_hex_byte_address_output_is_preserved(self):
        with patch.object(win, 'objdump', return_value='llvm-objdump'), patch.object(win.subprocess, 'check_output', return_value='  120: exit\n'):
            self.assertEqual(win.objdump_text(Path('candidate.so'), 0x120, 0x128), {0x120: 'exit'})

    def test_sbf_hex_byte_address_output_is_preserved(self):
        # platform-tools v1.52 llvm-objdump reports elf64-sbf with hex byte-address labels.
        output = 'candidate.so: file format elf64-sbf\n     198: mov64 r1, r2\n     1a0: exit\n'
        with patch.object(win, 'objdump', return_value='llvm-objdump'), patch.object(win.subprocess, 'check_output', return_value=output):
            self.assertEqual(win.objdump_text(Path('candidate.so'), 0x198, 0x1a8), {0x198: 'mov64 r1, r2', 0x1a0: 'exit'})

    def test_zero_start_disambiguates_the_next_instruction(self):
        for labels in (('0', '2', '3'), ('0', '10', '18')):
            output = ('candidate.so: file format elf64-sbf\n'
                      f' {labels[0]}: lddw r0, 0x100\n'
                      f' {labels[1]}: mov64 r1, r2\n'
                      f' {labels[2]}: exit\n')
            with self.subTest(labels=labels), patch.object(win, 'objdump', return_value='llvm-objdump'), patch.object(win.subprocess, 'check_output', return_value=output):
                self.assertEqual(win.objdump_text(Path('candidate.so'), 0, 0x20),
                                 {0: 'lddw r0, 0x100', 0x10: 'mov64 r1, r2', 0x18: 'exit'})

    @unittest.skipUnless(os.environ.get('PUMP_OBJDUMP'), 'requires explicit SBF llvm-objdump')
    def test_real_retained_pump_instructions_join_the_comparison_addresses(self):
        original = win.resolve_original(win.BASE / 'original.so')
        windows = win.original_windows()
        lddw = next(w for w in windows if any(raw[0] == 0x18 for _, raw, _ in win.insns(w['raw'], w['start'], win.ORIG_SECS)))
        for window in (windows[0], lddw):
            start = window['start']
            end = start + window['bytes']
            assembly = win.objdump_text(original, start, end)
            tokens = win.insns(window['raw'], start, win.ORIG_SECS)
            self.assertEqual(set(assembly), {address for address, _, _ in tokens})
            self.assertTrue(all(assembly[address] for address, _, _ in tokens))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            win.cmd_orig(SimpleNamespace(start=hex(windows[0]['start'])))
        self.assertIn(f"{windows[0]['start']:#07x}  ldxdw", output.getvalue())

if __name__ == '__main__': unittest.main()
