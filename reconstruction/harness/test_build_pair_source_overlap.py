"""Real paired-build CLI admission preserves both source trees before any SDK use."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

import build_score_pair as pair


class PairSourceOverlapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pair-source-overlap-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repos = []
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_ALLOW_PROTOCOL='file', GIT_NO_LAZY_FETCH='1',
                        PYTHONDONTWRITEBYTECODE='1')
        for name in ('base', 'candidate'):
            repo = self.root / name
            crate = repo / 'programs/pump'
            (crate / 'src').mkdir(parents=True)
            (crate / 'Cargo.toml').write_text('[package]\nname="isolated-fixture"\nversion="0.1.0"\n')
            (crate / 'Cargo.lock').write_text('version=3\n')
            (crate / 'src/lib.rs').write_text('pub fn preserved() {}\n')
            for command in (
                ['git', 'init', '-q', str(repo)],
                ['git', '-C', str(repo), 'add', 'programs/pump'],
                ['git', '-C', str(repo), '-c', 'user.name=isolated fixture',
                 '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
                 'commit', '-qm', 'isolated source fixture'],
            ):
                subprocess.run(command, check=True, env=self.env, capture_output=True)
            self.repos.append(repo)
        self.before = [pair.snapshot(repo / 'programs/pump') for repo in self.repos]

    def command(self, output):
        # Missing SDK paths stop the disjoint control at tool admission. No
        # compiler, SDK, build script, scorer or target program is executed.
        return [sys.executable, '-B', str(Path(pair.__file__).resolve()),
                '--base', str(self.repos[0]), '--candidate', str(self.repos[1]),
                '--out', str(output), '--sdk', str(self.root / 'missing-sdk'),
                '--hybrid', str(self.root / 'missing-hybrid')]

    def assert_sources_unchanged(self):
        self.assertEqual([pair.snapshot(repo / 'programs/pump') for repo in self.repos], self.before)

    def rejected(self, output):
        existed = output.exists()
        result = subprocess.run(self.command(output), capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(b'output must not overlap a Pump source tree', result.stderr)
        self.assertEqual(output.exists(), existed)
        self.assert_sources_unchanged()

    def test_output_inside_base_source_is_rejected_before_writes(self):
        self.rejected(self.repos[0] / 'programs/pump/new-evidence')

    def test_output_inside_candidate_source_is_rejected_before_writes(self):
        self.rejected(self.repos[1] / 'programs/pump/new-evidence')

    def test_symlink_alias_into_source_is_rejected_before_writes(self):
        alias = self.root / 'alias'
        try:
            alias.symlink_to(self.repos[1] / 'programs/pump', target_is_directory=True)
        except OSError as error:
            self.skipTest(f'directory symlinks unavailable: {error}')
        self.rejected(alias / 'new-evidence')

    def test_output_containing_source_is_rejected_before_setup(self):
        self.rejected(self.repos[0])

    def test_disjoint_output_reaches_tool_admission_without_changing_source(self):
        output = self.root / 'disjoint-output'
        result = subprocess.run(self.command(output), capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn(b'output must not overlap', result.stderr)
        self.assertIn(b'missing-hybrid', result.stderr)
        self.assertTrue((output / 'scoring-inputs/original.so').is_file())
        self.assert_sources_unchanged()


    def case_alias_output(self, repo):
        alias = repo.with_name(repo.name.upper())
        if not alias.exists() or not alias.samefile(repo):
            self.skipTest("requires a case-insensitive filesystem")
        return alias / "programs/pump/new-evidence"

    def test_case_alias_output_inside_base_source_is_rejected_before_writes(self):
        self.rejected(self.case_alias_output(self.repos[0]))

    def test_case_alias_output_inside_candidate_source_is_rejected_before_writes(self):
        self.rejected(self.case_alias_output(self.repos[1]))


if __name__ == '__main__':
    unittest.main()
