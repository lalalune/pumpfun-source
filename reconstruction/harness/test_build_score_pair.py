import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_score_pair as pair


class PairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / 'output'
        self.sdk = self.root / 'sdk'
        self.hybrid = self.root / 'hybrid'
        for path in (self.sdk / 'llvm/bin/llvm-objdump', self.hybrid / 'rust/bin/rustc'):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'tool fixture')
        self.sources = patch.object(pair, 'source_receipt', return_value={'revision': 'fixture', 'files': {}, 'sha256': 'fixture'})
        self.sources.start()
        self.addCleanup(self.sources.stop)
        self.addCleanup(setattr, pair.score, 'BASE', pair.score.BASE)
        self.addCleanup(setattr, pair.fastbuild, 'SDK', pair.fastbuild.SDK)
        self.addCleanup(setattr, pair.fastbuild, 'LOCKDIR', pair.fastbuild.LOCKDIR)
        original = pair.fastbuild.RECIPES['identity']
        self.addCleanup(pair.fastbuild.RECIPES.__setitem__, 'identity', original)

    def build(self, source, work, out, **kwargs):
        out.mkdir(parents=True)
        (out / 'unstripped.so').write_bytes(b'fixture, not a real ELF')
        return {'ok': True, 'runtime_valid': True, 'stack_warnings': []}

    def run_pair(self):
        return pair.run_pair(self.root / 'base', self.root / 'candidate', self.out, self.sdk, self.hybrid)

    def test_equal_counts_cannot_hide_a_lost_match(self):
        before = {0: {'bytes': 8, 'normalized': True, 'raw': True},
                  8: {'bytes': 8, 'normalized': False, 'raw': False}}
        after = {0: before[8], 8: before[0]}
        with patch.object(pair.fastbuild, 'build', side_effect=self.build), \
             patch.object(pair.score, 'score', side_effect=[before, after]):
            self.assertEqual(self.run_pair(), 1)
        receipt = json.loads((self.out / 'receipt.json').read_text())
        self.assertEqual(receipt['comparison']['raw_losses'], ['0x0'])
        self.assertFalse(receipt['comparison']['accepted'])

    def test_failed_or_stack_invalid_base_never_reaches_scoring(self):
        for result in ({'ok': False}, {'ok': True, 'runtime_valid': False},
                       {'ok': True, 'runtime_valid': True, 'stack_warnings': ['overflow']}):
            with self.subTest(result=result):
                self.out = self.root / str(len(list(self.root.iterdir())))
                with patch.object(pair.fastbuild, 'build', return_value=result), \
                     patch.object(pair.score, 'score') as scorer:
                    with self.assertRaises(ValueError):
                        self.run_pair()
                    scorer.assert_not_called()
                self.assertIn('error', json.loads((self.out / 'receipt.json').read_text()))

    def test_same_score_passes_and_outputs_cannot_be_overwritten(self):
        windows = {0: {'bytes': 8, 'normalized': True, 'raw': True}}
        with patch.object(pair.fastbuild, 'build', side_effect=self.build) as build, \
             patch.object(pair.score, 'score', return_value=windows):
            self.assertEqual(self.run_pair(), 0)
            self.assertNotEqual(build.call_args_list[0].args[1], build.call_args_list[1].args[1])
            with self.assertRaises(FileExistsError):
                self.run_pair()
        self.assertTrue((self.out / 'candidate-score.json').is_file())

    def test_source_receipt_rejects_dirty_inputs(self):
        self.sources.stop()
        self.addCleanup(self.sources.start)
        import subprocess
        repo = self.root / 'source'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        crate = repo / 'programs/pump'
        (crate / 'src').mkdir(parents=True)
        for name in ('Cargo.toml', 'Cargo.lock', 'src/lib.rs'):
            (crate / name).write_text('fixture')
        subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(repo), '-c', 'user.name=fixture',
                        '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
                        'commit', '-qm', 'fixture'], check=True)
        self.assertEqual(len(pair.source_receipt(repo)['files']), 3)
        (crate / 'src/lib.rs').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'clean'):
            pair.source_receipt(repo)

    def test_changed_sources_fail_before_scoring(self):
        with patch.object(pair, 'source_receipt', side_effect=[{}, {}, {'changed': True}]), \
             patch.object(pair.fastbuild, 'build', side_effect=self.build), \
             patch.object(pair.score, 'score') as scorer:
            with self.assertRaisesRegex(ValueError, 'source changed'):
                self.run_pair()
            scorer.assert_not_called()


if __name__ == '__main__':
    unittest.main()
