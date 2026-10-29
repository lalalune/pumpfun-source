"""Regression controls for the roadmap call/syscall classification correction."""
from pathlib import Path
import gzip
import hashlib
import json
import struct
import types
import unittest

import proof

P = Path(__file__).resolve().parent


def slot(opcode, regs=0, offset=0, immediate=0):
    return struct.pack('<BBhi', opcode, regs, offset, immediate)


class RoadmapCallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archived = proof._load_archived(proof.REPO)
        cls.corrected = staticmethod(proof.corrected_classify(cls.archived))
        cls.report = proof.check(proof.REPO)

    def fake(self, data, relocations=None):
        return types.SimpleNamespace(b=data, relocations=relocations or {})

    def test_internal_relative_call(self):
        data = slot(0x85, 0x10, 0, 2) + slot(0x95)
        self.assertEqual(self.archived.classify_instruction(data, 0, self.fake(data)), 'call_other')
        self.assertEqual(self.corrected(data, 0, self.fake(data)), 'call_internal')

    def test_relocated_external_call_is_not_relative(self):
        data = slot(0x85, 0x10, 0, -1)
        elf = self.fake(data, {0: {'type': 10, 'symbol': 'sol_log_'}})
        self.assertEqual(self.corrected(data, 0, elf), 'syscall_sol_log_')
        self.assertNotEqual(self.corrected(data, 0, elf), 'call_internal')

    def test_legacy_direct_syscall_form_is_preserved(self):
        data = slot(0x85, 0x00, 0, 0x1234)
        self.assertEqual(self.corrected(data, 0, self.fake(data)), 'syscall_4660')

    def test_non_call_instructions_are_unchanged(self):
        for opcode in (0x05, 0x18, 0x95, 0x79, 0xb7):
            data = slot(opcode) + (slot(0x00) if opcode == 0x18 else b'')
            self.assertEqual(
                self.corrected(data, 0, self.fake(data)),
                self.archived.classify_instruction(data, 0, self.fake(data)),
            )

    def test_real_corpus_counts_are_complete(self):
        totals = self.report['totals']
        self.assertEqual(totals['call_sites'], 23160)
        self.assertEqual(totals['internal_calls'], 22582)
        self.assertEqual(totals['external_calls'], 578)
        self.assertEqual(totals['changed_windows'], 476)
        for name, row in self.report['programs'].items():
            self.assertEqual(row['syscall_terms_before'], {}, name)
            self.assertEqual(sum(row['syscall_terms_after'].values()), row['external_calls'], name)
            self.assertEqual(row['call_internal_before'], 0, name)
            self.assertEqual(row['call_internal_after'], row['internal_calls'], name)
            self.assertEqual(row['call_other_before'], row['call_sites'], name)

    def test_calls_are_not_lost_when_syscalls_are_split_out(self):
        from window_elf_reader import Elf
        elf = Elf(proof.REPO / 'evidence/original/pump/deployed.so')
        before = self.archived.analyze_window_patterns(elf, elf.entries[0], elf.entries[1])
        after = proof.window_patterns(self.archived, elf, elf.entries[0], elf.entries[1], self.corrected)
        self.assertEqual(before['calls'], after['calls'])
        self.assertEqual(before['complexity_score'], after['complexity_score'])

    def test_saved_observations_match(self):
        saved = json.loads(gzip.decompress((P / 'observations.json.gz').read_bytes()))
        self.assertEqual(saved, self.report)

    def test_manifest_inventory(self):
        saved = json.loads((P / 'manifest.json').read_text())
        actual = {
            str(path.relative_to(P)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(P.rglob('*'))
            if path.is_file() and path.name != 'manifest.json'
            and '__pycache__' not in path.parts and path.suffix != '.pyc'
        }
        self.assertEqual(saved, actual)


if __name__ == '__main__':
    unittest.main(verbosity=2)
