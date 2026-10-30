"""Candidate replacement must not mix bytes, symbols or report identity."""
import contextlib
import hashlib
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import score


def elf(value):
    blob = bytearray(512)
    blob[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<Q', blob, 0x28, 64)
    struct.pack_into('<HHH', blob, 0x3a, 64, 3, 2)
    struct.pack_into('<IIQQQQIIQQ', blob, 128, 1, 1, 6, 4096, 400, 8, 0, 0, 8, 0)
    names = b'\0.text\0.shstrtab\0'
    struct.pack_into('<IIQQQQIIQQ', blob, 192, 7, 3, 0, 0, 440, len(names), 0, 0, 1, 0)
    blob[440:440 + len(names)] = names
    struct.pack_into('<BBhi', blob, 400, 0xb7, 0, 0, value)
    return bytes(blob)


class SnapshotTests(unittest.TestCase):
    def exercise(self, cli=False, remove=False, tool_failure=False, replace=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / 'candidate.so'
            first, second = elf(1), elf(2)
            candidate.write_bytes(first)
            original = first[400:408]
            windows = [{'start': 4096, 'bytes': 8, 'raw': original, 'norm': original}]
            tool_paths = []

            def symbols(snapshot_path):
                # Simulate another build publishing after the scorer's first read.
                if remove:
                    candidate.unlink()
                elif replace:
                    replacement = root / 'replacement.so'
                    replacement.write_bytes(second)
                    replacement.replace(candidate)
                tool_path = Path(snapshot_path)
                tool_paths.append(tool_path)
                if tool_failure:
                    raise RuntimeError('symbol reader failed')
                symbol = 'first' if tool_path.read_bytes() == first else 'second'
                return [(4096, 8, symbol)]

            with patch.object(score, 'original_windows', return_value=windows), \
                 patch.object(score, 'candidate_functions', side_effect=symbols):
                if tool_failure:
                    with self.assertRaisesRegex(RuntimeError, 'symbol reader failed'):
                        score.score(candidate)
                elif cli:
                    report = root / 'score.json'
                    baseline = root / 'baseline.json'
                    baseline.write_text(json.dumps({'windows': {'4096': {'normalized': True, 'raw': True, 'bytes': 8}}}))
                    with patch.object(sys, 'argv', ['score.py', str(candidate), '--baseline',
                                                   str(baseline), '--json', str(report)]), \
                         contextlib.redirect_stdout(io.StringIO()):
                        score.main()
                    result = json.loads(report.read_text())
                    self.assertEqual(result['summary']['candidate_sha256'], hashlib.sha256(first).hexdigest())
                    self.assertEqual(result['windows']['4096']['symbols'], ['first'])
                    self.assertTrue(result['windows']['4096']['raw'])
                else:
                    result = score.score(candidate)
                    self.assertEqual(result[4096]['symbols'], ['first'])
                    self.assertTrue(result[4096]['raw'])
            self.assertEqual(len(tool_paths), 1)
            self.assertNotEqual(tool_paths[0], candidate)
            self.assertFalse(tool_paths[0].exists(), 'temporary candidate must be cleaned up')
            if not remove:
                self.assertEqual(candidate.read_bytes(), second if replace else first)

    def test_unchanged_candidate_keeps_memberships_and_hash(self):
        self.exercise(cli=True, replace=False)

    def test_replaced_candidate_keeps_original_symbols(self):
        self.exercise()

    def test_report_hash_matches_scored_snapshot(self):
        self.exercise(cli=True)

    def test_removed_candidate_can_finish_from_snapshot(self):
        self.exercise(cli=True, remove=True)

    def test_symbol_reader_failure_cleans_snapshot(self):
        self.exercise(tool_failure=True)


if __name__ == '__main__':
    unittest.main()
