"""Real histories: an absent intermediate source must remain an unknown revision."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent


class MissingSourceBisectTests(unittest.TestCase):
    def test_missing_middle_source_and_normal_history(self):
        for missing in (True, False):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                repo = root / 'repo'
                repo.mkdir()
                env = dict(os.environ, GIT_AUTHOR_NAME='Local Test', GIT_COMMITTER_NAME='Local Test',
                           GIT_AUTHOR_EMAIL='test@example.invalid', GIT_COMMITTER_EMAIL='test@example.invalid')
                def git(*args):
                    return subprocess.check_output(
                        ['git', '-C', str(repo), '-c', 'commit.gpgsign=false',
                         '-c', 'core.hooksPath=/dev/null', *args], env=env).decode().strip()
                git('init', '-q')
                revisions = []
                for value in ('good', None if missing else 'bad', 'bad-final'):
                    path = repo / 'crate/value'
                    if value is None:
                        path.unlink()
                        path.parent.rmdir()
                    else:
                        path.parent.mkdir(exist_ok=True)
                        path.write_text(value)
                    git('add', '-A')
                    git('commit', '-qm', str(value))
                    revisions.append(git('rev-parse', 'HEAD'))
                config = root / 'oracle.json'
                config.write_text(json.dumps({'command': [sys.executable, '-c',
                    'from pathlib import Path; import sys; '
                    'sys.exit(0 if Path(sys.argv[1], "value").read_text()=="good" else 1)', '{source}']}))
                run = subprocess.run([sys.executable, str(H / 'bisect_membership.py'),
                                      '--repo', str(repo), '--good', revisions[0], '--bad', revisions[-1],
                                      '--source-subdir', 'crate', '--oracle', str(config),
                                      '--out', str(root / 'out')], capture_output=True, text=True)
                self.assertEqual(run.returncode, 2 if missing else 0, run.stderr)
                report = json.loads((root / 'out/bisect.json').read_text())
                if missing:
                    self.assertEqual(report['status'], 'unresolved')
                    self.assertEqual(report['tested'][revisions[1]], 'error')
                    self.assertEqual(report['possible_first_failures'], revisions[1:])
                    self.assertEqual(report['archive_errors'][0]['revision'], revisions[1])
                    self.assertIn('pathspec', report['archive_errors'][0]['stderr'])
                else:
                    self.assertEqual(report['status'], 'boundary-found')
                    self.assertEqual(report['first_failing_bound'], revisions[1])
                self.assertEqual(git('rev-parse', 'HEAD'), revisions[-1])
                self.assertEqual(git('status', '--porcelain'), '')


if __name__ == '__main__':
    unittest.main()
