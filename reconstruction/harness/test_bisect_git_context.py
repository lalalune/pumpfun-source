"""The selected bisection repository must win over enclosing Git routing."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent


class GitContextTests(unittest.TestCase):
    def git(self, repo, *args):
        return subprocess.check_output([
            'git', '-C', str(repo), '-c', 'user.name=isolated fixture',
            '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
            '-c', 'core.hooksPath=/dev/null', '-c', 'core.autocrlf=false', *args],
            stderr=subprocess.PIPE).decode().strip()

    def history(self, repo, label):
        repo.mkdir()
        self.git(repo, 'init', '-q')
        revisions = []
        for tag, value in (('good', 'one\n'), ('bad', 'two\n')):
            (repo / 'value').write_text(value)
            self.git(repo, 'add', 'value')
            self.git(repo, 'commit', '-qm', label+' '+tag)
            self.git(repo, 'tag', tag)
            revisions.append(self.git(repo, 'rev-parse', 'HEAD'))
        return revisions

    def test_bisect_reads_the_explicit_repository_under_ambient_git_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            intended, ambient = root/'intended', root/'ambient'
            expected = self.history(intended, 'intended')
            other = self.history(ambient, 'ambient')
            self.assertNotEqual(expected, other)
            oracle = root/'oracle.json'
            oracle.write_text(json.dumps({'command':[
                sys.executable, '-c', 'from pathlib import Path; import sys; '
                'sys.exit(0 if (Path(sys.argv[1])/"value").read_text()=="one\\n" else 1)', '{source}']}))
            contexts = {
                'normal': {},
                'git-dir': {'GIT_DIR':str(ambient/'.git'), 'GIT_WORK_TREE':str(ambient)},
                'common-dir': {'GIT_COMMON_DIR':str(ambient/'.git')},
                'object-dir': {'GIT_OBJECT_DIRECTORY':str(ambient/'.git/objects')},
            }
            for name, routing in contexts.items():
                with self.subTest(context=name):
                    output = root/('out-'+name)
                    env = dict(os.environ, **routing)
                    result = subprocess.run([sys.executable, str(H/'bisect_membership.py'),
                        '--repo', str(intended), '--good', 'good', '--bad', 'bad',
                        '--source-subdir', '.', '--oracle', str(oracle), '--out', str(output)],
                        env=env, capture_output=True)
                    self.assertEqual(result.returncode, 0, 'could not read explicit repository: '+name)
                    report = json.loads((output/'bisect.json').read_text())
                    self.assertEqual(report['first_failing_bound'], expected[-1])
                    self.assertEqual(set(report['tested']), set(expected))


if __name__ == '__main__':
    unittest.main()
