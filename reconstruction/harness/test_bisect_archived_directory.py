"""Successful Git archives can omit the requested source directory."""
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
class ArchivedDirectoryTests(unittest.TestCase):
    def test_non_directory_revisions_remain_unknown(self):
        for kind in ('export-ignore', 'regular-file', 'normal'):
            for index in (1, 2):
                with self.subTest(kind=kind, index=index), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    repo = root / 'repo'
                    repo.mkdir()
                    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
                    env.update(GIT_AUTHOR_NAME='Local Test', GIT_COMMITTER_NAME='Local Test',
                               GIT_AUTHOR_EMAIL='test@example.invalid',
                               GIT_COMMITTER_EMAIL='test@example.invalid')
                    def git(*args):
                        return subprocess.check_output(
                            ['git', '-C', str(repo), '-c', 'commit.gpgsign=false',
                             '-c', 'core.hooksPath=/dev/null', *args], env=env).decode().strip()
                    git('init', '-q')
                    revisions = []
                    crate = repo / 'crate'
                    for current in range(3):
                        if crate.is_dir(): shutil.rmtree(crate)
                        else: crate.unlink(missing_ok=True)
                        (repo / '.gitattributes').unlink(missing_ok=True)
                        if current == index and kind == 'regular-file':
                            crate.write_text('no source directory\n')
                        else:
                            crate.mkdir()
                            (crate / 'value').write_text('good' if current == 0 else f'bad-{current}')
                            if current == index and kind == 'export-ignore':
                                (repo / '.gitattributes').write_text('crate export-ignore\n')
                        git('add', '-A'); git('commit', '-qm', str(current))
                        revisions.append(git('rev-parse', 'HEAD'))
                    oracle = root / 'oracle.json'
                    oracle.write_text(json.dumps({'command': [sys.executable, '-c',
                        'from pathlib import Path; import sys; '
                        'sys.exit(0 if (Path(sys.argv[1])/"value").read_text()=="good" else 1)',
                        '{source}']}))
                    result = subprocess.run([sys.executable, '-B', str(H / 'bisect_membership.py'),
                        '--repo', str(repo), '--good', revisions[0], '--bad', revisions[2],
                        '--source-subdir', 'crate', '--oracle', str(oracle), '--out', str(root / 'out')],
                        env=env, capture_output=True, timeout=30)
                    self.assertEqual(result.returncode, 0 if kind == 'normal' else 2, result.stderr)
                    report = json.loads((root / 'out/bisect.json').read_bytes())
                    if kind == 'normal':
                        self.assertEqual(report['status'], 'boundary-found')
                        self.assertEqual(report['first_failing_bound'], revisions[1])
                        self.assertNotIn('archive_errors', report)
                    else:
                        self.assertEqual(report['tested'][revisions[index]], 'error')
                        self.assertEqual(len(report['archive_errors']), 1)
                        error = report['archive_errors'][0]
                        self.assertEqual(error['revision'], revisions[index])
                        # Python versions differ in accepting a Git tar containing
                        # only the global PAX header and no exported members.
                        allowed = {'archive does not contain the source directory'}
                        if kind == 'export-ignore':
                            allowed.add('source archive could not be extracted')
                        self.assertIn(error['reason'], allowed)
                        if 'detail' in error:
                            self.assertTrue(error['detail'])
                        self.assertEqual(report['status'], 'unresolved' if index == 1 else 'invalid-endpoints')
                        if index == 1:
                            self.assertEqual(report['possible_first_failures'], revisions[1:])
                        self.assertFalse((root / 'out/trials' / revisions[index]).exists())
                    self.assertEqual(git('rev-parse', 'HEAD'), revisions[-1])
                    self.assertEqual(git('status', '--porcelain'), '')


if __name__ == '__main__':
    unittest.main()
