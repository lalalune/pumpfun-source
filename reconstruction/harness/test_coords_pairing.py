"""Retained-input regression; no captured code executes."""
import unittest
from test_support import copy_harness_modules

class SourceCoordinatePairingTests(unittest.TestCase):
    def test_cli_keeps_reused_source_descriptors_at_their_own_lines(self):
        import json
        from pathlib import Path
        import shutil
        import subprocess
        import sys
        import tempfile

        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix='pump-coordinate-pairing-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-coordinate-pairing-'))
            (root / 'harness').mkdir()
            (root / 'base').mkdir()
            copy_harness_modules(root / 'harness')
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

    def test_unresolved_nearest_pointer_store_does_not_fall_back_to_an_older_one(self):
        """Synthetic instruction bytes; no captured code executes."""
        import struct
        from coords import sites

        path = b'programs/pump/src/stale.rs'
        blob = path
        secs = {'.rodata': {'addr': 0x1000, 'offset': 0, 'size': len(path), 'type': 1}}
        X = -16

        def lddw(reg, immediate):
            return (struct.pack('<BBHI', 0x18, reg, 0, immediate & 0xffffffff)
                    + struct.pack('<I', 0) + struct.pack('<I', immediate >> 32))

        def insn(opcode, regs, offset, immediate):
            return struct.pack('<BBhi', opcode, regs, offset, immediate)

        raw = b''.join([
            lddw(3, 0x1000),                       # older pointer immediate
            insn(0x7b, (3 << 4) | 10, X - 8, 0),   # *(u64 *)(r10 + X - 8) = r3
            insn(0xb7, 4, 0, 0),                   # r4 = 0: not resolvable from an lddw
            insn(0x7b, (4 << 4) | 10, X - 8, 0),   # nearest store overwrites that slot
            insn(0x7a, 10, X, len(path)),          # *(u64 *)(r10 + X) = length
            insn(0x62, 10, X + 8, 466),            # *(u32 *)(r10 + X + 8) = line
        ])

        # The nearest pointer store sits one instruction before the length store;
        # the older, resolvable store sits three instructions before it. Pairing
        # must stop at the nearer store instead of reporting the overwritten path.
        self.assertEqual(sites(blob, secs, 0, raw), [],
                         'an overwritten stack slot must not report the older source path')


if __name__ == '__main__': unittest.main()
