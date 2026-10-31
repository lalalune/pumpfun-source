"""Source-receipt boundary regressions for reconstruction/harness/build_score_pair.py."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HARNESS = Path(__file__).resolve().parents[1] / 'reconstruction/harness'
sys.path.insert(0, str(HARNESS))

import build_score_pair as pair  # noqa: E402


def symlink_directories_available():
    try:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            os.symlink(root, root / 'link', target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        return False
    return True


SYMLINK_DIRECTORIES = symlink_directories_available()


class BuildScorePairSourceReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='pair-source-receipt-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.env = dict(
            os.environ,
            GIT_CONFIG_NOSYSTEM='1',
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_ALLOW_PROTOCOL='file',
            GIT_NO_LAZY_FETCH='1',
            PYTHONDONTWRITEBYTECODE='1',
        )

    def git(self, repo, *args):
        return subprocess.run(
            ['git', '-C', str(repo), *args],
            check=True,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def commit_all(self, repo, message='fixture'):
        self.git(repo, 'add', '-A')
        self.git(
            repo,
            '-c', 'user.name=fixture',
            '-c', 'user.email=fixture@example.invalid',
            '-c', 'commit.gpgsign=false',
            'commit', '-qm', message,
        )

    def make_repo(self, name='repo', gitignore='**/target/\n*.bk\n/work/\n'):
        repo = self.root / name
        crate = repo / 'programs/pump'
        (crate / 'src/target').mkdir(parents=True)
        (crate / 'target/build').mkdir(parents=True)
        (repo / '.gitignore').write_text(gitignore, encoding='utf-8')
        (crate / 'Cargo.toml').write_text(
            '[package]\nname = "pump-fixture"\nversion = "0.1.0"\nedition = "2021"\n',
            encoding='utf-8',
        )
        (crate / 'Cargo.lock').write_text('version = 3\n', encoding='utf-8')
        (crate / 'src/lib.rs').write_text('pub mod target;\n', encoding='utf-8')
        (crate / 'src/target/mod.rs').write_text('pub const VALUE: u8 = 1;\n', encoding='utf-8')
        (crate / 'target/build/generated.bin').write_bytes(b'ignored root build output')
        subprocess.run(['git', 'init', '-q', str(repo)], check=True, env=self.env)
        self.git(repo, 'add', '-f', 'programs/pump/src/target/mod.rs')
        self.commit_all(repo)
        return repo, crate

    def test_enclosing_repository_subdirectory_cannot_impersonate_head(self):
        outer, _ = self.make_repo('outer')
        nested = outer / 'work/untracked-checkout'
        fake_crate = nested / 'programs/pump/src'
        fake_crate.mkdir(parents=True)
        (nested / 'programs/pump/Cargo.toml').write_text(
            '[package]\nname = "imposter"\nversion = "0.1.0"\n', encoding='utf-8'
        )
        (nested / 'programs/pump/Cargo.lock').write_text('version = 3\n', encoding='utf-8')
        (fake_crate / 'lib.rs').write_text('pub fn injected() {}\n', encoding='utf-8')

        with self.assertRaisesRegex(ValueError, 'worktree root'):
            pair.source_receipt(nested)

    def test_linked_git_worktree_root_is_admitted(self):
        repo, _ = self.make_repo('primary')
        linked = self.root / 'linked-worktree'
        self.git(repo, 'worktree', 'add', '--detach', '-q', str(linked), 'HEAD')
        self.assertTrue((linked / '.git').is_file())
        receipt = pair.source_receipt(linked)
        self.assertEqual(receipt['revision'], pair.source_receipt(repo)['revision'])
        self.assertEqual(receipt['sha256'], pair.source_receipt(repo)['sha256'])

    def test_gitignored_non_root_inputs_are_rejected_while_root_target_stays_excluded(self):
        repo, crate = self.make_repo('ignored-inputs')
        baseline = pair.source_receipt(repo)
        (crate / 'target/build/another.bin').write_bytes(b'still ignored under root target/')
        self.assertEqual(pair.source_receipt(repo), baseline)

        cases = (
            ('tracked_nested_target', crate / 'src/target/injected.rs', b'pub const BAD: u8 = 9;\n'),
            ('untracked_nested_target', crate / 'assets/target/blob.bin', b'untracked asset'),
            ('ignored_extension', crate / 'src/extra.bk', b'ignored backup input'),
        )
        for label, injected, payload in cases:
            with self.subTest(case=label):
                injected.parent.mkdir(parents=True, exist_ok=True)
                injected.write_bytes(payload)
                try:
                    with self.assertRaisesRegex(ValueError, 'clean'):
                        pair.source_receipt(repo)
                finally:
                    injected.unlink()

    def test_ignored_regular_file_at_root_target_path_is_rejected(self):
        repo, crate = self.make_repo('target-file', gitignore='/programs/pump/target\n')
        shutil.rmtree(crate / 'target')
        (crate / 'target').write_bytes(b'regular file named target')
        with self.assertRaisesRegex(ValueError, 'clean'):
            pair.source_receipt(repo)

    @unittest.skipUnless(SYMLINK_DIRECTORIES, 'creating a directory symlink is not permitted')
    def test_symlinked_checkout_and_crate_ancestors_are_rejected(self):
        outside = self.root / 'outside-pump'
        (outside / 'src').mkdir(parents=True)
        (outside / 'Cargo.toml').write_text('[package]\nname = "out"\nversion = "0.1.0"\n', encoding='utf-8')
        (outside / 'Cargo.lock').write_text('version = 3\n', encoding='utf-8')
        (outside / 'src/lib.rs').write_text('pub fn outside() {}\n', encoding='utf-8')

        repo, crate = self.make_repo('symlink-crate')
        shutil.rmtree(crate)
        crate.symlink_to(outside, target_is_directory=True)
        self.commit_all(repo, 'replace crate with symlink')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            pair.source_receipt(repo)

        repo_programs, _ = self.make_repo('symlink-programs')
        outside_programs = self.root / 'outside-programs'
        (outside_programs / 'pump').mkdir(parents=True)
        shutil.copytree(outside, outside_programs / 'pump', dirs_exist_ok=True)
        shutil.rmtree(repo_programs / 'programs')
        (repo_programs / 'programs').symlink_to(outside_programs, target_is_directory=True)
        self.commit_all(repo_programs, 'replace programs with symlink')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            pair.source_receipt(repo_programs)

        clean_repo, _ = self.make_repo('clean-repo')
        checkout_link = self.root / 'checkout-link'
        checkout_link.symlink_to(clean_repo, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            pair.source_receipt(checkout_link)

        out = self.root / 'cli-out'
        result = subprocess.run(
            [
                sys.executable, '-B', str(Path(pair.__file__).resolve()),
                '--base', str(checkout_link),
                '--candidate', str(clean_repo),
                '--out', str(out),
                '--sdk', str(self.root / 'missing-sdk'),
                '--hybrid', str(self.root / 'missing-hybrid'),
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('symlink', result.stderr)
        self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
