"""End-to-end checks with real git histories/patches and actual child processes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent
IDENTITY = dict(os.environ, GIT_AUTHOR_NAME='Oz-0s', GIT_COMMITTER_NAME='Oz-0s',
                GIT_AUTHOR_EMAIL='199988715+Oz-0s@users.noreply.github.com',
                GIT_COMMITTER_EMAIL='199988715+Oz-0s@users.noreply.github.com')


class ExperimentCLI(unittest.TestCase):
    def test_real_history_bisection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); repo = root / 'repo'; repo.mkdir()
            def git(*args): return subprocess.check_output(['git', '-C', str(repo), '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null', *args], env=IDENTITY).decode().strip()
            git('init', '-q'); revisions = []
            for value in ['good', 'bad', 'bad-again']:
                (repo / 'value').write_text(value)
                git('add', 'value'); git('commit', '-qm', value)
                revisions.append(git('rev-parse', 'HEAD'))
            config = root / 'oracle.json'
            config.write_text(json.dumps({'command':[sys.executable, '-c', "from pathlib import Path; import sys; sys.exit(0 if Path(sys.argv[1], 'value').read_text() == 'good' else 1)", '{source}']}))
            result = subprocess.run([sys.executable, str(H/'bisect_membership.py'), '--repo', str(repo), '--good', revisions[0], '--bad', revisions[-1], '--source-subdir', '.', '--oracle', str(config), '--out', str(root/'out')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root/'out/bisect.json').read_text())
            self.assertEqual(report['first_failing_bound'], revisions[1])
            self.assertEqual(git('rev-parse', 'HEAD'), revisions[-1])
            self.assertEqual(git('status', '--porcelain'), '')

    def test_real_patch_reduction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source'; source.mkdir()
            (source/'value').write_text('old\n'); (source/'noise').write_text('old\n')
            paths = []
            for name in ['noise', 'value']:
                path = root/(name+'.patch')
                path.write_text(f'diff --git a/{name} b/{name}\n--- a/{name}\n+++ b/{name}\n@@ -1 +1 @@\n-old\n+new\n')
                paths.append(str(path))
            patches = root/'patches.json'; patches.write_text(json.dumps(paths))
            config = root/'oracle.json'; config.write_text(json.dumps({'command':[sys.executable, '-c', "from pathlib import Path; import sys; sys.exit(0 if Path(sys.argv[1], 'value').read_text() == 'new\\n' else 1)", '{source}']}))
            result = subprocess.run([sys.executable, str(H/'minimize_experiment.py'), '--source', str(source), '--patches', str(patches), '--oracle', str(config), '--out', str(root/'out')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root/'out/minimized.json').read_text())
            self.assertEqual(report['selected'], [1]); self.assertTrue(report['one_minimal'])
            self.assertEqual((source/'value').read_text(), 'old\n')
            self.assertFalse((source/'.git').exists())


if __name__ == '__main__': unittest.main()
