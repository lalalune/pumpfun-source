import importlib.util
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
SPEC = importlib.util.spec_from_file_location('late_census', PACKAGE / 'run.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class LateOutputTests(unittest.TestCase):
    def test_output_created_after_preflight_is_preserved(self):
        lane = ROOT / runner.LANE
        for flag in ('--json', '--j', '--md', '--m'):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'late-report'
                original_load = runner.load_harness
                def occupy_after_admission(name, root):
                    module = original_load(name, root)
                    if name == 'coords':
                        output.write_bytes(b'late retained evidence\n')
                    return module
                argv = ['run.py', 'hotness', '--remarks', str(lane / 'NOTES.md'),
                        '--census', str(lane / 'CENSUS.json'), flag, str(output)]
                with patch.dict(sys.modules), patch.object(sys, 'argv', argv), \
                        patch.object(runner, 'load_harness', side_effect=occupy_after_admission), \
                        contextlib.redirect_stderr(io.StringIO()) as errors:
                    with self.assertRaises(SystemExit) as raised:
                        runner.main()
                    self.assertEqual(raised.exception.code, 2)
                    self.assertIn('output appeared during diagnostics', errors.getvalue())
                self.assertEqual(output.read_bytes(), b'late retained evidence\n')


if __name__ == '__main__':
    unittest.main()
