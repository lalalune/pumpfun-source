"""Regression controls for the token-program constant detector."""
from pathlib import Path
import gzip
import hashlib
import json
import struct
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
