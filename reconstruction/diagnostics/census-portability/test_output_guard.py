"""Occupied outputs stay refused under every spelling argparse accepts."""
from pathlib import Path
import importlib.util
import os
import stat
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

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX file-size limits')
    def test_actual_report_write_failures_leave_a_retryable_destination(self):
        path = ROOT / 'research/census-report-publication-20261101/probe.py'
        spec = importlib.util.spec_from_file_location('census_publication_probe', path)
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        # Real retained analysis and OS write failures; no report function mock.
        probe.validate(probe.run(ROOT), 'fixed')

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX umask')
    def test_long_report_names_keep_the_callers_umask(self):
        for name in ('a' * 240, '\uacb0' * 80):
            path = self.root / name
            try:
                path.touch(); path.unlink()
            except OSError as error:
                self.skipTest(f'filesystem rejects the requested name: {error}')
            lane = ROOT / 'reconstruction/pump-main/lanes/callgraph-census'
            result = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8',
                str(PACKAGE / 'run.py'), 'hotness', '--remarks', str(lane / 'NOTES.md'),
                '--census', str(lane / 'CENSUS.json'), '--json', str(path)],
                capture_output=True, text=True, timeout=90, preexec_fn=lambda: os.umask(0o027))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
            self.assertFalse(list(self.root.glob('.census-*')))

    def test_fresh_outputs_are_still_written(self):
        for flag in ['--json', '--js']:
            fresh = self.root / f'fresh{flag}.json'
            result = self.invoke(flag, fresh)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(fresh.is_file())


if __name__ == '__main__':
    unittest.main()
