"""Real bisections must not publish their result over an input file."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent
SEED = b'{"marker":"preserve-me"}\n'


class BisectInputPreservationTests(unittest.TestCase):
    def exercise(self, collision):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / 'repo'; repo.mkdir()
            env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
            env.update(GIT_AUTHOR_NAME='Local Test', GIT_COMMITTER_NAME='Local Test',
                       GIT_AUTHOR_EMAIL='test@example.invalid', GIT_COMMITTER_EMAIL='test@example.invalid')
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo),
                    '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null', *args], env=env)
            git('init', '-q')
            revisions = []
            (repo / 'crate').mkdir()
            for value in ('good', 'bad'):
                (repo / 'crate/value').write_text(value, encoding='utf-8')
                git('add', '-A'); git('commit', '-qm', value)
                revisions.append(git('rev-parse', 'HEAD').decode().strip())
            # Preserve both a dirty worktree and independently staged bytes.
            (repo / 'crate/value').write_bytes(b'uncommitted work\n')
            (repo / 'staged.txt').write_bytes(b'staged work\n'); git('add', 'staged.txt')
            original = (git('rev-parse', 'HEAD'), git('status', '--porcelain'), git('diff', '--cached', '--binary'))
            out = root / 'out'; out.mkdir()
            report = out / 'bisect.json'
            config_path = root / 'oracle.json'
            if collision == 'oracle-case-alias':
                config_path = out / 'BISECT.JSON'
            input_path = root / 'input.json'
            if collision in ('oracle', 'oracle-alias'):
                config_path = report
            if collision in ('declared', 'declared-alias'):
                input_path = report
            input_path.write_bytes(SEED)
            if collision == 'declared-alias':
                input_path = self.alias(root / 'input-alias.json', report)
            launched = root / 'launched'
            command = [sys.executable, '-c',
                       'import json,sys; from pathlib import Path; '
                       'assert json.loads(Path(sys.argv[3]).read_text())["marker"]=="preserve-me"; '
                       'Path(sys.argv[2]).write_text("launched"); '
                       'sys.exit(0 if (Path(sys.argv[1])/"value").read_text()=="good" else 1)',
                       '{source}', str(launched), str(input_path)]
            config_path.write_text(json.dumps({'command': command, 'inputs': [str(input_path)]}), encoding='utf-8')
            if collision == 'oracle-case-alias' and (not report.exists()
                    or not report.samefile(config_path)):
                self.skipTest('requires a case-insensitive filesystem')
            if collision == 'oracle-alias':
                config_path = self.alias(root / 'oracle-alias.json', report)
            inputs = {p: p.read_bytes() for p in (config_path, input_path)}
            result = subprocess.run([sys.executable, '-B', str(H / 'bisect_membership.py'),
                '--repo', str(repo), '--good', revisions[0], '--bad', revisions[1],
                '--source-subdir', 'crate', '--oracle', str(config_path), '--out', str(out)],
                env=env, capture_output=True, timeout=30)
            for path, before in inputs.items():
                self.assertEqual(path.read_bytes(), before, 'bisection report overwrote an input')
            self.assertEqual(original, (git('rev-parse', 'HEAD'), git('status', '--porcelain'),
                                        git('diff', '--cached', '--binary')))
            self.assertEqual((repo / 'crate/value').read_bytes(), b'uncommitted work\n')
            if collision:
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(b'report overlaps an input', result.stderr)
                self.assertFalse(launched.exists())
                self.assertFalse((out / 'trials').exists())
            else:
                self.assertEqual(result.returncode, 0, result.stderr)
                saved = json.loads(report.read_bytes())
                self.assertEqual(saved['status'], 'boundary-found')
                self.assertEqual(saved['first_failing_bound'], revisions[1])
                self.assertEqual(saved['tested'], {revisions[0]: 'pass', revisions[1]: 'fail'})

    def alias(self, path, target):
        try:
            path.symlink_to(target)
        except OSError as error:
            if sys.platform == 'win32' and error.winerror == 1314:
                self.skipTest('Windows symlink privilege unavailable')
            raise
        return path

    def test_report_cannot_replace_oracle_or_declared_input(self):
        for collision in ('oracle', 'declared'):
            with self.subTest(collision=collision):
                self.exercise(collision)

    def test_resolved_input_aliases_are_protected(self):
        for collision in ('oracle-alias', 'declared-alias'):
            with self.subTest(collision=collision):
                self.exercise(collision)

    def test_separate_inputs_still_find_the_real_boundary(self):
        self.exercise(None)

    def test_physical_case_alias_of_oracle_is_protected(self):
        self.exercise('oracle-case-alias')


if __name__ == '__main__':
    unittest.main()
