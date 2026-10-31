"""A result path must not replace a patch or configuration supplied as input."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent
PATCH = b'''diff --git a/value b/value
--- a/value
+++ b/value
@@ -1 +1 @@
-old
+new
'''


class MinimizeInputPreservationTests(unittest.TestCase):
    def exercise(self, collision):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'; source.mkdir()
            (source / 'value').write_bytes(b'old\n')
            out = root / 'out'; out.mkdir()
            result_path = out / 'minimized.json'
            paths = {kind: root / name for kind, name in
                     [('patch', 'unit.patch'), ('manifest', 'patches.json'), ('oracle', 'oracle.json')]}
            if collision == 'oracle-case-alias':
                paths['oracle'] = out / 'MINIMIZED.JSON'
            if collision in paths:
                paths[collision] = result_path
            paths['patch'].write_bytes(PATCH)
            if collision == 'patch-alias':
                paths['patch'].rename(result_path)
                try:
                    paths['patch'].symlink_to(result_path)
                except OSError as error:
                    if sys.platform == 'win32' and error.winerror == 1314:
                        self.skipTest('Windows symlink privilege unavailable')
                    raise
            paths['manifest'].write_text(json.dumps([str(paths['patch'])]), encoding='utf-8')
            config = {'command': [sys.executable, '-c',
                'from pathlib import Path; import sys; '
                'sys.exit(0 if (Path(sys.argv[1])/"value").read_text()=="new\\n" else 1)',
                '{source}']}
            if collision == 'declared-input':
                result_path.write_bytes(b'declared experiment input\n')
                paths['declared-input'] = result_path
                config['inputs'] = [str(result_path)]
            paths['oracle'].write_text(json.dumps(config), encoding='utf-8')
            if collision == 'oracle-case-alias' and (not result_path.exists()
                    or not result_path.samefile(paths['oracle'])):
                self.skipTest('requires a case-insensitive filesystem')
            before = {kind: path.read_bytes() for kind, path in paths.items()}
            env = {name: value for name, value in os.environ.items() if not name.startswith('GIT_')}
            result = subprocess.run([sys.executable, '-B', str(H / 'minimize_experiment.py'),
                '--source', str(source), '--patches', str(paths['manifest']),
                '--oracle', str(paths['oracle']), '--out', str(out)],
                env=env, capture_output=True, timeout=30)
            for kind, path in paths.items():
                self.assertEqual(path.read_bytes(), before[kind], f'{kind} input was overwritten')
            self.assertEqual((source / 'value').read_bytes(), b'old\n')
            if collision:
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(b'result overlaps an input', result.stderr)
                self.assertFalse((out / 'trials').exists())
            else:
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result_path.read_bytes())['selected'], [0])

    def test_result_cannot_replace_patch_or_configuration(self):
        for kind in ('patch', 'manifest', 'oracle'):
            with self.subTest(kind=kind):
                self.exercise(kind)

    def test_separate_inputs_still_minimize_a_real_patch(self):
        self.exercise(None)

    def test_result_cannot_replace_a_declared_input(self):
        self.exercise('declared-input')

    def test_result_cannot_replace_an_aliased_patch(self):
        self.exercise('patch-alias')

    def test_result_cannot_replace_case_alias_of_oracle(self):
        self.exercise('oracle-case-alias')


if __name__ == '__main__':
    unittest.main()
