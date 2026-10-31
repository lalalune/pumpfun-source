"""Physical aliases must not bypass the minimizer's source/output separation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).parent


class MinimizePhysicalOverlapTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='minimize-tree-alias-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'CaseSource'
        self.source.mkdir()
        (self.source / 'input.txt').write_bytes(b'retained source\n')
        self.alias = self.root / 'casesource'
        patch = self.root / 'change.patch'
        patch.write_text('diff --git a/added.txt b/added.txt\nnew file mode 100644\n'
                         '--- /dev/null\n+++ b/added.txt\n@@ -0,0 +1 @@\n+added\n',
                         encoding='utf-8')
        self.patches = self.root / 'patches.json'
        self.patches.write_text(json.dumps([str(patch)]), encoding='utf-8')
        self.oracle = self.root / 'oracle.json'
        self.oracle.write_text(json.dumps({'command': [sys.executable, '-c', 'pass']}),
                               encoding='utf-8')

    def bind_alias(self):
        self.alias.mkdir()
        try:
            subprocess.run(['mount', '--bind', str(self.source), str(self.alias)],
                           check=True, capture_output=True, timeout=15)
        except (OSError, subprocess.SubprocessError):
            self.skipTest('requires bind-mount privileges')
        self.addCleanup(subprocess.run, ['umount', str(self.alias)],
                        capture_output=True, timeout=15)
        if not self.alias.samefile(self.source):
            self.skipTest('bind mount did not alias the source')

    def require_case_alias(self):
        if not self.alias.exists() or not self.alias.samefile(self.source):
            self.skipTest('requires a case-insensitive filesystem')

    def run_minimize(self, out):
        return subprocess.run(
            [sys.executable, '-B', str(H / 'minimize_experiment.py'),
             '--source', str(self.source), '--patches', str(self.patches),
             '--oracle', str(self.oracle), '--out', str(out)],
            text=True, capture_output=True, timeout=60)

    def assert_rejected_before_any_write(self, out):
        result = self.run_minimize(out)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('separate trees', result.stderr)
        self.assertEqual(list(self.source.iterdir()), [self.source / 'input.txt'])

    def test_bind_mount_alias_output_is_rejected(self):
        self.bind_alias()
        self.assert_rejected_before_any_write(self.alias / 'out')
        self.assert_rejected_before_any_write(self.alias)

    def test_case_alias_output_is_rejected(self):
        self.require_case_alias()
        self.assert_rejected_before_any_write(self.alias / 'target')
        self.assert_rejected_before_any_write(self.alias)

    def test_distinct_output_remains_admitted(self):
        result = self.run_minimize(self.root / 'out')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.root / 'out' / 'minimized.json').exists())
        self.assertEqual(list(self.source.iterdir()), [self.source / 'input.txt'])


if __name__ == '__main__':
    unittest.main()
