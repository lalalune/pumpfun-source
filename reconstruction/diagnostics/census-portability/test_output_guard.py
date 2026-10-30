"""Occupied outputs stay refused under every spelling argparse accepts."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
LANE = ROOT / 'reconstruction/pump-main/lanes/callgraph-census'
RETAINED = b'retained diagnostic\n'


class OutputGuardTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='pump-census-guard-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.output = self.root / 'retained.json'
        self.output.write_bytes(RETAINED)

    def invoke(self, *arguments):
        return subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', str(PACKAGE / 'run.py'), 'hotness',
                               '--remarks', str(LANE / 'NOTES.md'), '--census', str(LANE / 'CENSUS.json'),
                               *map(str, arguments)],
                              cwd=self.root, capture_output=True, text=True, encoding='utf-8')

    def assert_refused(self, *arguments):
        result = self.invoke(*arguments)
        self.assertEqual(self.output.read_bytes(), RETAINED, result.stdout + result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('output already exists', result.stderr)

    def test_abbreviated_flags_cannot_overwrite(self):
        self.assert_refused('--js', self.output)
        self.assert_refused('--j', self.output)
        self.assert_refused('--m', self.output)

    def test_abbreviated_inline_flags_cannot_overwrite(self):
        self.assert_refused(f'--jso={self.output}')
        self.assert_refused(f'--m={self.output}')

    def test_dangling_symlink_is_not_written_through(self):
        target = self.root / 'outside.json'
        link = self.root / 'link.json'
        link.symlink_to(target)
        result = self.invoke('--json', link)
        self.assertFalse(target.exists(), result.stdout + result.stderr)
        self.assertNotEqual(result.returncode, 0)

    def test_fresh_outputs_are_still_written(self):
        for flag in ['--json', '--js']:
            fresh = self.root / f'fresh{flag}.json'
            result = self.invoke(flag, fresh)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(fresh.is_file())


if __name__ == '__main__':
    unittest.main()
