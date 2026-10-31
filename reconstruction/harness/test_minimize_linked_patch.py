"""A valid Git patch may yield source the experiment runner cannot admit."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent


@unittest.skipUnless(os.name == 'posix' and shutil.which('git'), 'requires POSIX Git symlinks')
class LinkedPatchTests(unittest.TestCase):
    def test_linked_initial_and_reduced_subsets_keep_reports(self):
        for repaired in (False, True):
            with self.subTest(repaired=repaired), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / 'source'
                source.mkdir()
                (source / 'value').write_text('one\n')
                repo = root / 'patch-author'
                shutil.copytree(source, repo)
                env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
                env.update(GIT_AUTHOR_NAME='Local Test', GIT_COMMITTER_NAME='Local Test',
                           GIT_AUTHOR_EMAIL='test@example.invalid',
                           GIT_COMMITTER_EMAIL='test@example.invalid')
                def git(*args):
                    return subprocess.check_output(['git', '-C', str(repo), '-c',
                        'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null', *args], env=env)
                git('init', '-q'); git('add', '-A'); git('commit', '-qm', 'base')
                (repo / 'alias').symlink_to('value')
                git('add', '-A')
                first = root / 'add-link.patch'
                first.write_bytes(git('diff', '--cached', '--binary'))
                git('commit', '-qm', 'link')
                patches = [first]
                if repaired:
                    (repo / 'alias').unlink()
                    (repo / 'value').write_text('two\n')
                    git('add', '-A')
                    second = root / 'remove-link.patch'
                    second.write_bytes(git('diff', '--cached', '--binary'))
                    patches.append(second)
                hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in patches]
                listing = root / 'patches.json'
                listing.write_text(json.dumps([str(p) for p in patches]))
                oracle = root / 'oracle.json'
                oracle.write_text(json.dumps({'command': [sys.executable, '-c',
                    'from pathlib import Path;import sys;'
                    'sys.exit(0 if Path(sys.argv[1],"value").read_text()=="two\\n" else 1)', '{source}']}))
                out = root / 'out'
                result = subprocess.run([sys.executable, '-B', str(H / 'minimize_experiment.py'),
                    '--source', str(source), '--patches', str(listing), '--oracle', str(oracle),
                    '--out', str(out)], env=env, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 2, result.stderr)
                report = json.loads((out / 'minimized.json').read_bytes())
                self.assertFalse(report['one_minimal'])
                self.assertEqual(report['status'], 'bounded-result' if repaired else 'initial-predicate-not-met')
                self.assertIn({'selected': [0], 'status': 'error'}, report['tested'])
                if repaired:
                    self.assertIn({'selected': [0, 1], 'status': 'pass'}, report['tested'])
                    self.assertIn({'selected': [], 'status': 'fail'}, report['tested'])
                self.assertEqual(report['source_errors'], [{'selected': [0],
                    'detail': 'linked source inputs are unsupported'}])
                # Rejected linked source never receives a trial directory.
                rejected_key = hashlib.sha256(json.dumps([0]).encode()).hexdigest()[:16]
                self.assertFalse((out / 'trials' / rejected_key).exists())
                self.assertEqual(list(p.name for p in source.iterdir()), ['value'])
                self.assertEqual((source / 'value').read_bytes(), b'one\n')
                self.assertEqual([hashlib.sha256(p.read_bytes()).hexdigest() for p in patches], hashes)


if __name__ == '__main__':
    unittest.main()
