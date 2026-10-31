"""Unusable trial budgets and empty inputs are CLI errors before any output exists."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent


def run(script, *args):
    return subprocess.run([sys.executable, '-B', str(H / script), *args],
                          capture_output=True, text=True, encoding='utf-8')


class TrialBudgetAdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.oracle = self.root / 'oracle.json'
        self.oracle.write_text(json.dumps({'command': [sys.executable, '-c', 'pass']}), encoding='utf-8')

    def assert_rejected(self, result, out, message):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(message, result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(out.exists(), 'rejected options must not create the output directory')

    def test_minimizer_rejects_nonpositive_budget_and_empty_patch_list(self):
        source = self.root / 'source'
        source.mkdir()
        (source / 'lib.rs').write_text('fn main() {}\n', encoding='utf-8')
        unit = self.root / 'unit.patch'
        unit.write_text('', encoding='utf-8')
        cases = {'zero-budget': ([str(unit)], '0', '--max-trials must be positive'),
                 'negative-budget': ([str(unit)], '-1', '--max-trials must be positive'),
                 'empty-patches': ([], '5', 'patch list must name at least one patch')}
        for name, (paths, budget, message) in cases.items():
            with self.subTest(name):
                patches = self.root / (name + '.json')
                patches.write_text(json.dumps(paths), encoding='utf-8')
                out = self.root / ('out-' + name)
                result = run('minimize_experiment.py', '--source', str(source), '--patches', str(patches),
                             '--oracle', str(self.oracle), '--out', str(out), '--max-trials', budget)
                self.assert_rejected(result, out, message)

    def test_bisect_rejects_small_budget_and_single_revision(self):
        repo = self.root / 'repo'
        repo.mkdir()
        env = dict(os.environ, GIT_AUTHOR_NAME='Local Test', GIT_COMMITTER_NAME='Local Test',
                   GIT_AUTHOR_EMAIL='test@example.invalid', GIT_COMMITTER_EMAIL='test@example.invalid')
        def git(*args):
            return subprocess.check_output(['git', '-C', str(repo), '-c', 'commit.gpgsign=false',
                                            '-c', 'core.hooksPath=/dev/null', *args], env=env).decode().strip()
        git('init', '-q')
        revisions = []
        for value in ('good', 'bad'):
            (repo / 'crate').mkdir(exist_ok=True)
            (repo / 'crate/value').write_text(value, encoding='utf-8')
            git('add', '-A')
            git('commit', '-qm', value)
            revisions.append(git('rev-parse', 'HEAD'))
        cases = {'budget-one': (revisions[0], revisions[1], '1', '--max-trials must be at least 2'),
                 'same-revision': (revisions[1], revisions[1], '5', 'good and bad must be different revisions')}
        for name, (good, bad, budget, message) in cases.items():
            with self.subTest(name):
                out = self.root / ('out-' + name)
                result = run('bisect_membership.py', '--repo', str(repo), '--good', good, '--bad', bad,
                             '--source-subdir', 'crate', '--oracle', str(self.oracle), '--out', str(out),
                             '--max-trials', budget)
                self.assert_rejected(result, out, message)


if __name__ == '__main__':
    unittest.main()
