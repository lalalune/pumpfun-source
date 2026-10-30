"""Short windows must not lose actual exact matches to an empty 3-gram shortlist.

The subprocesses analyze the captured Pump ELF and an unchanged retained compiler
output; neither program executes. A separate byte-mutated copy is a negative control.
"""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

from elf_symbols import function_symbols
from score import body, normalize, sections


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CANDIDATE = REPO / 'reconstruction/pump-main/lanes/v3-sell-payment-layout/candidate.so.gz'
EXPECTED_SHA256 = '969811b0e0f673b693695ea651008cacd93eafa5a663dd8bec0e61d3b22d09a9'


class ShortWindowRankingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='pump-short-window-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.harness = self.root / 'harness'
        self.harness.mkdir()
        # Stage local helpers together, including new imports added to the maintained
        # harness; the Windows checkout may materialize original.so as symlink text.
        for path in HERE.glob('*.py'):
            shutil.copyfile(path, self.harness / path.name)
        base = self.root / 'base'
        base.mkdir()
        self.original = (REPO / 'evidence/original/pump/deployed.so').read_bytes()
        (base / 'original.so').write_bytes(self.original)
        shutil.copyfile(REPO / 'reconstruction/base/functions.tsv', base / 'functions.tsv')
        self.candidate = self.root / 'candidate.so'
        self.blob = gzip.decompress(CANDIDATE.read_bytes())
        self.assertEqual(hashlib.sha256(self.blob).hexdigest(), EXPECTED_SHA256)
        self.candidate.write_bytes(self.blob)

    def metric(self, *starts):
        result = subprocess.run(
            [sys.executable, '-E', '-B', '-X', 'utf8', str(self.harness / 'target_metric.py'),
             str(self.candidate), *starts, '--top', '1'],
            capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_real_one_and_two_instruction_windows_find_the_existing_exact_body(self):
        rows = self.metric('0xce38', '0x1a04f8', '0x1aac98')
        self.assertEqual([row['window'] for row in rows], ['0xce38', '0x1a04f8', '0x1aac98'])
        for row in rows:
            with self.subTest(window=row['window']):
                self.assertEqual(row['ratio'], 1.0)
                self.assertTrue(row['normalized_equal'])
                self.assertEqual(row['slots_diff'], 0)
        self.assertTrue(rows[0]['raw_equal'])
        self.assertTrue(rows[2]['raw_equal'])

    def test_mutating_each_exact_store_body_does_not_manufacture_a_match(self):
        original_sections = sections(self.original)
        raw = body(self.original, original_sections, 0xce38, 16)
        self.assertEqual(raw.hex(), '7a010000000000009500000000000000')
        candidate_sections = sections(self.blob)
        target = normalize(raw, 0xce38, original_sections)
        mutated = bytearray(self.blob)
        changed = set()
        for start, size, _name in function_symbols(self.blob):
            if size != 16 or normalize(body(self.blob, candidate_sections, start, size), start, candidate_sections) != target:
                continue
            changed.add(start)
            offset = candidate_sections['.text']['offset'] + start - candidate_sections['.text']['addr']
            struct.pack_into('<i', mutated, offset + 4, 1)
        self.assertTrue(changed)
        self.candidate.write_bytes(mutated)
        row, = self.metric('0xce38')
        self.assertFalse(row['normalized_equal'])
        self.assertFalse(row['raw_equal'])
        self.assertLess(row['ratio'], 1.0)


if __name__ == '__main__':
    unittest.main()
