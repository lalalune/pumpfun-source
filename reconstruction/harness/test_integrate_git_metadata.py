"""Compose real Git clones/worktrees without treating repository metadata as source."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

MODULES = ('integrate.py', 'treediff.py', 'source_inputs.py')
HERE = Path(__file__).resolve().parent


class IntegrationGitMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='compose-git-metadata-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.harness = self.root / 'harness'
        self.harness.mkdir()
        for name in MODULES:
            shutil.copyfile(HERE / name, self.harness / name)
        self.repo = self.root / 'repository'
        (self.repo / 'src').mkdir(parents=True)
        (self.repo / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n')
        (self.repo / 'Cargo.lock').write_text('version=3\n')
        (self.repo / 'src/lib.rs').write_text('pub const VALUE:u8=1;\n')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'base')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              capture_output=True, text=True)

    def worktree(self, name):
        path = self.root / name
        self.git('worktree', 'add', '--detach', '-q', str(path), 'HEAD')
        return path

    def compose(self, base, part):
        result = subprocess.run([sys.executable, '-B', str(self.harness / 'integrate.py'),
                                 '--name', 'composition', '--base-src', str(base),
                                 '--part', 'part=' + str(part), '--no-build'],
                                capture_output=True, text=True, timeout=20)
        output = self.root / 'integ/composition'
        report = json.loads((output / 'report.json').read_bytes())
        self.assertEqual(result.returncode, 0, result.stderr + json.dumps(report['parts']))
        self.assertFalse((output / 'src/.git').exists())
        self.assertNotIn('gitdir:', (output / 'parts/part.patch').read_text())
        return output, report

    def test_clone_to_linked_worktree_applies_the_rust_change(self):
        part = self.worktree('part')
        expected = b'pub const VALUE:u8=2;\n'
        (part / 'src/lib.rs').write_bytes(expected)
        output, report = self.compose(self.repo, part)
        self.assertEqual(report['parts'][0]['status'], 'applied')
        self.assertEqual(report['parts'][0]['files'], ['src/lib.rs'])
        self.assertEqual((output / 'src/src/lib.rs').read_bytes(), expected)
        self.assertEqual((self.repo / 'src/lib.rs').read_text(), 'pub const VALUE:u8=1;\n')

    def test_identical_linked_worktrees_are_an_empty_part(self):
        output, report = self.compose(self.worktree('base'), self.worktree('part'))
        self.assertEqual(report['parts'][0]['status'], 'empty')
        self.assertEqual((output / 'parts/part.patch').read_bytes(), b'')

    def test_ordinary_crate_snapshots_still_apply(self):
        base, part = self.root / 'base', self.root / 'part'
        for destination in (base, part):
            shutil.copytree(self.repo, destination, ignore=shutil.ignore_patterns('.git'))
        (part / 'src/lib.rs').write_text('pub const VALUE:u8=3;\n')
        output, report = self.compose(base, part)
        self.assertEqual(report['parts'][0]['files'], ['src/lib.rs'])
        self.assertEqual((output / 'src/src/lib.rs').read_text(), 'pub const VALUE:u8=3;\n')


if __name__ == '__main__':
    unittest.main()
