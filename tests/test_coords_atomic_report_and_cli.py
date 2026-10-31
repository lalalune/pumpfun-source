"""Regression tests for atomic report publication and CLI error handling in coords.py."""

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'reconstruction/harness'
sys.path.insert(0, str(HARNESS))

import coords
import score
from test_elf_symbols import fixture


ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'


def _run_coords_cli(arguments):
    return subprocess.run(
        [sys.executable, '-B', str(HARNESS / 'coords.py'), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )


class CoordsAtomicReportAndCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.base = self.root / 'base'
        self.base.mkdir()
        self.image = bytes(fixture())
        (self.base / 'original.so').write_bytes(self.image)
        (self.base / 'functions.tsv').write_text(
            'program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n',
            encoding='utf-8',
        )
        self.candidate = self.root / 'candidate.so'
        self.candidate.write_bytes(self.image)
        self.output = self.root / 'report.json'

    def _run_in_process_unmatched(self, after_admission=None):
        real_score = coords.score_with_hash

        def wrapped_score(path):
            if after_admission is not None:
                after_admission()
            return real_score(path)

        argv = ['coords.py', 'unmatched', '--cand', str(self.candidate), '--json', str(self.output)]
        with patch.object(score, 'BASE', self.base), \
                patch.object(coords, 'BASE', self.base), \
                patch.object(coords, 'ORIG', self.image), \
                patch.object(coords, 'OS', coords.sections(self.image)), \
                patch.object(coords, 'original_windows', score.original_windows), \
                patch.object(coords, 'score_with_hash', side_effect=wrapped_score), \
                patch.object(sys, 'argv', argv), \
                contextlib.redirect_stdout(io.StringIO()):
            coords.main()

    def test_late_link_to_candidate_after_admission_cannot_truncate_input(self):
        with self.subTest(link_kind='hardlink'):
            self.candidate.write_bytes(self.image)
            self.output.unlink(missing_ok=True)
            self._run_in_process_unmatched(lambda: self.output.hardlink_to(self.candidate))
            self.assertEqual(self.candidate.read_bytes(), self.image)
            self.assertEqual(json.loads(self.output.read_text(encoding='utf-8')), [])
            self.assertFalse(self.output.samefile(self.candidate))
            self.assertEqual(list(self.root.glob('.score-*')), [])

        with self.subTest(link_kind='symlink'):
            self.candidate.write_bytes(self.image)
            self.output.unlink(missing_ok=True)

            def make_symlink():
                try:
                    os.symlink(self.candidate, self.output)
                except (OSError, NotImplementedError) as error:
                    self.skipTest(f'creating symlinks unavailable: {error}')

            self._run_in_process_unmatched(make_symlink)
            self.assertEqual(self.candidate.read_bytes(), self.image)
            self.assertFalse(self.output.is_symlink())
            self.assertEqual(json.loads(self.output.read_text(encoding='utf-8')), [])
            self.assertEqual(list(self.root.glob('.score-*')), [])

    def test_failed_publication_preserves_prior_report_and_cleans_staging(self):
        self.output.write_bytes(b'prior coords report')
        with patch.object(Path, 'replace', side_effect=PermissionError('publication denied')):
            with self.assertRaises(PermissionError):
                self._run_in_process_unmatched()
        self.assertEqual(self.output.read_bytes(), b'prior coords report')
        self.assertEqual(self.candidate.read_bytes(), self.image)
        self.assertEqual(list(self.root.glob('.score-*')), [])

    def test_fn_rejects_nonnumeric_address_before_reading_missing_candidate(self):
        missing = self.root / 'missing-candidate.so'
        result = _run_coords_cli(['fn', 'not-an-address', '--cand', str(missing)])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('is not a numeric address', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_cli_reports_stripped_corrupt_or_missing_candidate_without_traceback(self):
        stripped = self.root / 'stripped.so'
        shutil.copyfile(ORIGINAL, stripped)
        corrupt = self.root / 'corrupt.so'
        corrupt.write_bytes(b'not-an-elf')
        missing = self.root / 'does-not-exist.so'

        cases = [
            (['unmatched', '--cand', str(stripped)], 'candidate has no function symbols'),
            (['unmatched', '--cand', str(corrupt)], 'error:'),
            (['unmatched', '--cand', str(missing)], 'error:'),
            (['fn', '0x1000', '--cand', str(corrupt)], 'error:'),
            (['fn', '0x1000', '--cand', str(missing)], 'error:'),
        ]
        for args, expected_substring in cases:
            with self.subTest(args=args):
                result = _run_coords_cli(args)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(expected_substring, result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_sites_rejects_truncated_lddw_or_unaligned_tail_with_value_error(self):
        with self.assertRaises(ValueError):
            coords.sites(b'', {}, 0, b'\x18' + b'\x00' * 7)
        with self.assertRaises(ValueError):
            coords.sites(b'', {}, 0, b'\x95\x00\x00\x00')


if __name__ == '__main__':
    unittest.main()
