"""Matrix admission must refuse argv the kernel interface cannot carry."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().with_name('experiment_runner.py')


class ArgvAdmissionTests(unittest.TestCase):
    def run_matrix(self, argument):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / 'source').mkdir()
        (root / 'source/input.txt').write_text('x', encoding='utf-8')
        good = {'name': 'first', 'source': str(root / 'source'), 'command': [sys.executable, '-c', 'pass']}
        second = dict(good, name='second', command=[sys.executable, '-c', 'pass', argument])
        (root / 'matrix.json').write_text(json.dumps([good, second]), encoding='utf-8')
        result = subprocess.run([sys.executable, '-B', str(TOOL), str(root / 'matrix.json'),
                                 '--out', str(root / 'out')], capture_output=True, text=True)
        return result, root / 'out'

    def test_unencodable_arguments_are_refused_before_the_first_trial(self):
        for argument in ('a\0b', 'a\ud800b'):
            with self.subTest(argument=argument):
                result, out = self.run_matrix(argument)
                self.assertFalse(out.exists(), 'a trial ran before the matrix was admitted')
                self.assertEqual(result.returncode, 2, result.stderr[-300:])
                self.assertIn('invalid experiment matrix', result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_placeholders_and_non_ascii_arguments_stay_admitted(self):
        for argument in ('café', '{work}/report.json'):
            with self.subTest(argument=argument):
                result, out = self.run_matrix(argument)
                self.assertEqual(result.returncode, 0, result.stderr[-300:])
                self.assertEqual(sorted(json.loads(result.stdout)), ['first', 'second'])


if __name__ == '__main__':
    unittest.main()
