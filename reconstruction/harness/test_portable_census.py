import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1] / 'pump-main/lanes/callgraph-census'


class PortableCensusTests(unittest.TestCase):
    def test_entrypoints_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
            for name in ['census.py', 'blocksim.py', 'callid_audit.py', 'dataref_audit.py', 'capture_inline.py']:
                with self.subTest(name=name):
                    result = subprocess.run([sys.executable, str(LANE / name), '--help'], cwd=directory, env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('usage:', result.stdout)

    def test_pair_admission(self):
        spec = importlib.util.spec_from_file_location('portable_census', LANE / 'census.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'pairs.json'
            path.write_text('{"0x1000": "foo$"}')
            self.assertEqual(module.load_pairs(path), {4096: 'foo$'})
            for invalid in ['[]', '{}', '{"0x10":"a","16":"b"}', '{"1":"a","1":"b"}', '{"1":"["}', '{"1":3}']:
                path.write_text(invalid)
                with self.subTest(invalid=invalid), self.assertRaises((ValueError, TypeError)):
                    module.load_pairs(path)


if __name__ == '__main__': unittest.main()
