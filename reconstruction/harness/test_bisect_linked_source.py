"""A source link in real Git history is an unknown revision, not a culprit."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent


class LinkedSourceBisectTests(unittest.TestCase):
    def test_linked_middle_and_endpoint_keep_bounded_reports(self):
        for linked_index in (1, 2):
            with self.subTest(linked_index=linked_index), tempfile.TemporaryDirectory() as temporary:
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
                crate = repo / 'crate'
                crate.mkdir()
                value = crate / 'value'
                revisions = []
                for index in range(3):
                    value.unlink(missing_ok=True)
                    (crate / 'backing').unlink(missing_ok=True)
                    text = 'good' if index == 0 else f'bad-{index}'
                    if index == linked_index:
                        (crate / 'backing').write_text(text)
                        try:
                            value.symlink_to('backing')
                        except OSError as error:
                            self.skipTest(f'symlinks unavailable: {error}')
                    else:
                        value.write_text(text)
                    git('add', '-A')
                    git('commit', '-qm', str(index))
                    revisions.append(git('rev-parse', 'HEAD'))
                oracle = root / 'oracle.json'
                oracle.write_text(json.dumps({'command': [sys.executable, '-c',
                    'from pathlib import Path; import sys; '
                    'sys.exit(0 if (Path(sys.argv[1])/"value").read_text()=="good" else 1)', '{source}']}))
                run = subprocess.run([sys.executable, '-B', str(H / 'bisect_membership.py'),
                    '--repo', str(repo), '--good', revisions[0], '--bad', revisions[-1],
                    '--source-subdir', 'crate', '--oracle', str(oracle), '--out', str(root / 'out')],
                    capture_output=True, text=True)
                self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                report = json.loads((root / 'out/bisect.json').read_text())
                self.assertEqual(report['tested'][revisions[linked_index]], 'error')
                self.assertEqual(report['archive_errors'], [
                    {'revision': revisions[linked_index], 'reason': 'source links unsupported'}])
                if linked_index == 1:
                    self.assertEqual(report['status'], 'unresolved')
                    self.assertEqual(report['possible_first_failures'], revisions[1:])
                else:
                    self.assertEqual(report['status'], 'invalid-endpoints')
                    self.assertEqual(report['tested'][revisions[0]], 'pass')
                # Rejected source never reaches the oracle or creates a trial.
                self.assertFalse((root / 'out/trials' / revisions[linked_index]).exists())
                self.assertEqual(git('rev-parse', 'HEAD'), revisions[-1])
                self.assertEqual(git('status', '--porcelain'), '')


if __name__ == '__main__':
    unittest.main()
