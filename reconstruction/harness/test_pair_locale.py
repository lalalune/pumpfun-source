"""Receipt admission must read Unicode checkout paths under an ASCII locale."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent


@unittest.skipIf(sys.platform == 'win32', 'requires a POSIX ASCII text locale')
@unittest.skipUnless(shutil.which('git'), 'requires Git')
class PairLocaleTests(unittest.TestCase):
    def test_unicode_checkout_receipt_matches_utf8_control(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'caf\N{LATIN SMALL LETTER E WITH ACUTE}'
            crate = repo / 'programs/pump'
            (crate / 'src').mkdir(parents=True)
            for name, data in [('Cargo.toml', b'[package]\nname="fixture"\nversion="0.1.0"\n'),
                               ('Cargo.lock', b'version=3\n'), ('src/lib.rs', b'pub fn value()->u64{1}\n')]:
                (crate / name).write_bytes(data)
            env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), '-c', 'user.name=Local Test',
                    '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
                    '-c', 'core.hooksPath=/dev/null', *args], env=env)
            git('init', '-q'); git('add', '-A'); git('commit', '-qm', 'fixture')
            before = (repo / '.git/index').read_bytes()
            command = [sys.executable, '-B', '-c',
                       'import json,sys;sys.path.insert(0,sys.argv[1]);import build_score_pair as p;'
                       'print(json.dumps(p.source_receipt(sys.argv[2])))', str(H), str(repo)]
            control = subprocess.run(command, env=dict(env, PYTHONUTF8='1'), capture_output=True)
            self.assertEqual(control.returncode, 0, control.stderr)
            result = subprocess.run(command, env=dict(env, LC_ALL='C', LANG='C', PYTHONUTF8='0',
                                    PYTHONCOERCECLOCALE='0'), capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), json.loads(control.stdout))
            self.assertEqual((repo / '.git/index').read_bytes(), before)
            self.assertEqual(git('status', '--porcelain'), b'')


if __name__ == '__main__':
    unittest.main()
