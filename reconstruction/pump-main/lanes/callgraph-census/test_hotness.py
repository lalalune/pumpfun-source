"""hotness.py must resolve the harness from its own checkout."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).with_name('hotness.py')


class HotnessCheckoutTests(unittest.TestCase):
    def test_maps_remarks_from_an_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remarks = root / 'build.log'
            remarks.write_text(
                "note: src/create_v2.rs:10:5 inline (success): "
                "'<T as alloc::string::ToString>::to_string' inlined into 'create_v2::execute' "
                "with (cost=130, threshold=325)\n", encoding='utf-8')
            census = root / 'CENSUS.json'
            census.write_text(json.dumps({'targets': []}), encoding='utf-8')
            env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
            result = subprocess.run(
                [sys.executable, '-B', str(TOOL), '--remarks', str(remarks), '--census', str(census)],
                cwd=root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['0x1e7c0'], 1)


if __name__ == '__main__':
    unittest.main()
