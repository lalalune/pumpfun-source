"""Admit alternate case spellings of the same real Git worktree root."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent


@unittest.skipUnless(shutil.which('git'), 'requires Git')
class PairCaseAliasTests(unittest.TestCase):
    def test_physical_root_alias_and_nested_directory_control(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / 'case-source'
            crate = repo / 'programs/pump'
            (crate / 'src').mkdir(parents=True)
            alias = root / 'CASE-SOURCE'
            if not alias.exists() or not alias.samefile(repo):
                self.skipTest('requires a case-insensitive filesystem')
            for name, raw in [('Cargo.toml', b'[package]\nname="fixture"\nversion="0.1.0"\n'),
                              ('Cargo.lock', b'version=3\n'), ('src/lib.rs', b'pub fn f(){}\n')]:
                (crate / name).write_bytes(raw)
            env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), '-c', 'user.name=Local Test',
                    '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
                    '-c', 'core.hooksPath=/dev/null', *args], env=env)
            git('init', '-q'); git('add', '-A'); git('commit', '-qm', 'fixture')
            command = [sys.executable, '-B', '-c',
                       'import json,sys;sys.path.insert(0,sys.argv[1]);import build_score_pair as p;'
                       'print(json.dumps(p.source_receipt(sys.argv[2])))', str(H)]
            def receipt(path):
                return subprocess.run([*command, str(path)], env=env, capture_output=True)
            before_index = (repo / '.git/index').read_bytes()
            canonical = receipt(repo)
            self.assertEqual(canonical.returncode, 0, canonical.stderr)
            alternate = receipt(alias)
            self.assertEqual(alternate.returncode, 0, alternate.stderr)
            self.assertEqual(json.loads(alternate.stdout), json.loads(canonical.stdout))
            # A real subdirectory must still be rejected even if its spelling changes.
            for subdirectory in (repo / 'programs', alias / 'programs'):
                result = receipt(subdirectory)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'must be a Git worktree root', result.stderr)
            self.assertEqual((repo / '.git/index').read_bytes(), before_index)
            self.assertEqual(git('status', '--porcelain'), b'')


if __name__ == '__main__':
    unittest.main()
