"""Offline file-identity regressions; no SDK, compiler, subprocess or VM."""
from pathlib import Path
import hashlib
import importlib.util
import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tested_sell_score', HERE / 'sell_score.py')
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)


class ImageIdentityTests(unittest.TestCase):
    def report(self, original, candidate, unstripped=None):
        if unstripped is None:
            unstripped = candidate + b'symbol table'
        images = iter(types.SimpleNamespace(b=b, entries=[0], hi=8, normalized=b)
                      for b in (original, candidate, unstripped))
        with patch.object(score.elf_reader, 'Elf', side_effect=lambda _: next(images)), \
                patch.object(score, 'ORIGINAL_SHA', hashlib.sha256(original).hexdigest()), \
                patch.object(score, 'SELL_START', 0), patch.object(score, 'SELL_SIZE', 8), \
                patch.object(score, 'find_sell', return_value={'start': 0, 'size': 8}), \
                patch.object(score, 'listing', return_value=[]):
            return score.score(Path('unused'))

    def test_shorter_zero_padded_image_is_not_a_whole_file_match(self):
        report = self.report(b'12345678' + bytes(24), b'12345678')
        self.assertFalse(report['whole_elf_equal'])
        self.assertTrue(report['allocation_image_equal'])
        self.assertFalse(report['unstripped_elf_equal'])
        self.assertEqual(report['allocation_padding_bytes'], 24)
        self.assertEqual((report['original_bytes'], report['candidate_bytes']), (32, 8))
        self.assertTrue(report['sell_raw_equal'])

    def test_exact_candidate_does_not_imply_exact_compiler_output(self):
        report = self.report(b'12345678', b'12345678')
        self.assertTrue(report['whole_elf_equal'])
        self.assertTrue(report['allocation_image_equal'])
        self.assertFalse(report['unstripped_elf_equal'])
        self.assertEqual(report['allocation_padding_bytes'], 0)
        self.assertEqual(report['candidate_sha256'], hashlib.sha256(b'12345678').hexdigest())
        self.assertEqual(report['unstripped_sha256'], hashlib.sha256(b'12345678symbol table').hexdigest())

    def test_exact_unstripped_output_is_measured_independently(self):
        original = b'12345678' + bytes(24)
        report = self.report(original, b'12345678', original)
        self.assertTrue(report['unstripped_elf_equal'])
        self.assertFalse(report['whole_elf_equal'])
        self.assertEqual(report['unstripped_bytes'], 32)

    def test_nonzero_missing_suffix_is_not_allocation_equal(self):
        report = self.report(b'12345678' + bytes(23) + b'x', b'12345678')
        self.assertFalse(report['whole_elf_equal'])
        self.assertFalse(report['allocation_image_equal'])
        self.assertIsNone(report['allocation_padding_bytes'])

    def test_nonzero_prefix_difference_is_not_masked(self):
        report = self.report(b'12345678' + bytes(24), b'1234567x')
        self.assertFalse(report['whole_elf_equal'])
        self.assertFalse(report['allocation_image_equal'])
        self.assertFalse(report['sell_raw_equal'])

    def test_longer_candidate_is_not_truncated(self):
        report = self.report(b'12345678', b'12345678' + bytes(8))
        self.assertFalse(report['whole_elf_equal'])
        self.assertFalse(report['allocation_image_equal'])
        self.assertIsNone(report['allocation_padding_bytes'])

    def test_exact_all_three_files(self):
        report = self.report(b'12345678', b'12345678', b'12345678')
        self.assertTrue(report['whole_elf_equal'])
        self.assertTrue(report['allocation_image_equal'])
        self.assertTrue(report['unstripped_elf_equal'])
        self.assertEqual(report['score_version'], 2)

    def test_attempt_cache_separates_old_meaning_and_preserves_new_metrics(self):
        # Native build and flock are never called. The stubs also let this
        # runner/cache regression execute on Windows without the macOS SDK.
        native = types.ModuleType('native_build')
        native.SELL_REL = Path('sell.rs')
        with patch.dict(sys.modules, {'native_build': native, 'sell_score': score,
                                     'fcntl': types.ModuleType('fcntl')}):
            runner_spec = importlib.util.spec_from_file_location('tested_try_sell', HERE / 'try_sell.py')
            runner = importlib.util.module_from_spec(runner_spec)
            runner_spec.loader.exec_module(runner)
        report = self.report(b'12345678' + bytes(24), b'12345678')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sell = root / 'sell.rs'
            sell.write_bytes(b'fixture source')
            cache = root / 'cache'
            cache.mkdir()
            old_inputs = {'sell': runner.sha(sell.read_bytes()), 'patch': None, 'flags': '', 'link': None}
            old_key = runner.sha(json.dumps(old_inputs, sort_keys=True).encode())
            old_path = cache / (old_key + '.json')
            old_bytes = b'{"metrics":{"whole_elf_equal":true,"sell_raw_equal":true}}'
            old_path.write_bytes(old_bytes)
            args = ['try_sell.py', '--lane', 'fixture', '--approach', 'identity',
                    '--hypothesis', 'cache version regression', '--baseline']
            with patch.multiple(runner, SWARM=root, CACHE=cache, SOURCES=root / 'sources',
                                PRISTINE_SELL=sell), \
                    patch.object(native, 'build', create=True, return_value={'returncode': 0, 'seconds': 0}) as build, \
                    patch.object(score, 'score', return_value=report) as scoring, \
                    patch.object(runner, 'locked_append') as append, \
                    patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(), 3)
                self.assertEqual(runner.main(), 3)
            self.assertEqual(build.call_count, 1)
            self.assertEqual(scoring.call_count, 1)
            self.assertEqual(append.call_count, 1)
            self.assertEqual(old_path.read_bytes(), old_bytes)
            new_paths = [p for p in cache.glob('*.json') if p != old_path]
            self.assertEqual(len(new_paths), 1)
            entry = json.loads(new_paths[0].read_bytes())
            self.assertEqual(entry['inputs']['score_version'], 2)
            self.assertFalse(entry['metrics']['whole_elf_equal'])
            self.assertTrue(entry['metrics']['allocation_image_equal'])
            self.assertFalse(entry['metrics']['unstripped_elf_equal'])
            self.assertEqual(entry['metrics']['allocation_padding_bytes'], 24)
            self.assertEqual(entry['unstripped_sha256'], report['unstripped_sha256'])


if __name__ == '__main__':
    unittest.main()
