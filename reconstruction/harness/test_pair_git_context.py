"""Paired-build source receipts must describe the explicitly selected checkout."""
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
class PairGitContextTests(unittest.TestCase):
    def test_source_receipt_ignores_foreign_repository_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            clean = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
            def git(repo, *args):
                return subprocess.check_output(['git', '-C', str(repo), '-c', 'user.name=Local Test',
                    '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
                    '-c', 'core.hooksPath=/dev/null', *args], env=clean)
            for name in ('source', 'foreign'):
                repo = root / name
                (repo / 'programs/pump/src').mkdir(parents=True)
                for file, data in [('Cargo.toml', b'[package]\nname="fixture"\nversion="0.1.0"\n'),
                                   ('Cargo.lock', b'version=3\n'), ('src/lib.rs', name.encode())]:
                    (repo / 'programs/pump' / file).write_bytes(data)
                git(repo, 'init', '-q'); git(repo, 'add', '-A'); git(repo, 'commit', '-qm', name)
            source, foreign = root / 'source', root / 'foreign'
            code = ('import json,sys;sys.path.insert(0,sys.argv[1]);'
                    'import build_score_pair as p;print(json.dumps(p.source_receipt(sys.argv[2])))')
            command = [sys.executable, '-B', '-c', code, str(H), str(source)]
            control = subprocess.run(command, env=clean, capture_output=True)
            self.assertEqual(control.returncode, 0, control.stderr)
            expected = json.loads(control.stdout)
            self.assertEqual(expected['revision'], git(source, 'rev-parse', 'HEAD').decode().strip())
            before_index = (foreign / '.git/index').read_bytes()
            before_tree = git(foreign, 'status', '--porcelain')
            env = dict(clean, GIT_DIR=str(foreign / '.git'), GIT_WORK_TREE=str(foreign),
                       GIT_INDEX_FILE=str(foreign / '.git/index'))
            result = subprocess.run(command, env=env, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), expected)
            self.assertEqual((foreign / '.git/index').read_bytes(), before_index)
            self.assertEqual(git(foreign, 'status', '--porcelain'), before_tree)
            # Clean-check rejection still follows the selected source tree.
            (source / 'programs/pump/src/lib.rs').write_bytes(b'dirty')
            dirty = subprocess.run(command, env=env, capture_output=True)
            self.assertNotEqual(dirty.returncode, 0)
            self.assertIn(b'Pump source checkout must be clean', dirty.stderr)


if __name__ == '__main__':
    unittest.main()
