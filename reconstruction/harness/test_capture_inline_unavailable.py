"""Production parse-only CLI on authentic quoted and unquoted v1.44 remarks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'reconstruction/pump-main/lanes/callgraph-census/capture_inline.py'
FIXTURE = Path(__file__).with_name('fixtures') / 'inline-remarks-v144.json'


class InlineUnavailableTests(unittest.TestCase):
    def test_actual_compiler_remarks_and_filter_controls(self):
        remarks = json.loads(FIXTURE.read_text(encoding='utf-8'))['remarks']
        cases = [('ToString', 2, 'missed'), ('^pump_recovered::trade::buy$', 1, 'success'),
                 ('not_present_in_this_build', 0, None)]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, (caller, count, kind) in enumerate(cases):
                with self.subTest(caller=caller):
                    out = root / str(index)
                    out.mkdir()
                    log = '\n'.join(remarks) + '\n'
                    (out / 'build.log').write_text(log, encoding='utf-8')
                    result = subprocess.run([sys.executable, '-B', str(TOOL), '--parse-only',
                        '--src', str(ROOT / 'programs/pump'), '--work', str(root / 'work'),
                        '--out', str(out), '--caller', caller], cwd=root,
                        capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    rows = json.loads((out / 'inline-remarks.json').read_text(encoding='utf-8'))
                    self.assertEqual(len(rows), count)
                    self.assertEqual(json.loads(result.stdout)['remarks'], count)
                    self.assertEqual((out / 'build.log').read_text(encoding='utf-8'), log)
                    for row in rows:
                        self.assertEqual(row['kind'], kind)
                        self.assertIsNotNone(row['loc'])
                        if kind == 'missed':
                            self.assertIn('ToString>::to_string', row['caller'])
                            self.assertIn('definition is unavailable', row['text'])
                            self.assertIsNone(row['cost'])
                            self.assertIsNone(row['threshold'])
                        else:
                            self.assertEqual(row['threshold'], '325')


if __name__ == '__main__':
    unittest.main()
