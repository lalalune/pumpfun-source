"""Actual LLVM remarks retain source locations containing spaces."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
LANE = ROOT / 'reconstruction/pump-main/lanes/callgraph-census'
FIXTURE = Path(__file__).with_name('fixtures') / 'inline-locations-v144.json'


class InlineLocations(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads(FIXTURE.read_text())['rows']

    def test_capture_keeps_the_compiler_location(self):
        for row in self.rows:
            with self.subTest(path=row['case']), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)
                (output / 'build.log').write_text(row['remark'] + '\n')
                result = subprocess.run(
                    [sys.executable, '-B', str(LANE / 'capture_inline.py'),
                     '--parse-only', '--src', temporary, '--work', temporary,
                     '--out', temporary, '--caller', 'trade::buy$'],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                captured = json.loads((output / 'inline-remarks.json').read_text())
                self.assertEqual(len(captured), 1)
                self.assertEqual(captured[0]['loc'], 'probe.rs:8')
                self.assertEqual(captured[0]['threshold'], '325')

    def test_hotness_keeps_the_same_compiler_site(self):
        for row in self.rows:
            with self.subTest(path=row['case']), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)
                remarks = output / 'build.log'
                remarks.write_text(row['remark'] + '\n')
                report, markdown = output / 'hotness.json', output / 'hotness.md'
                result = subprocess.run(
                    [sys.executable, '-B', str(LANE / 'hotness.py'), '--remarks', str(remarks),
                     '--json', str(report), '--md', str(markdown)],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                sites = json.loads(report.read_text())['0x147ba0']['ours']
                self.assertEqual(len(sites), 1)
                self.assertEqual(sites[0]['loc'], f"/build/{row['case']}/probe.rs:8:9")
                self.assertEqual((sites[0]['inlined'], sites[0]['threshold'], sites[0]['hot']),
                                 (True, 325, True))
                self.assertIn(sites[0]['loc'] + ' to_string hot', markdown.read_text())


if __name__ == '__main__':
    unittest.main()
