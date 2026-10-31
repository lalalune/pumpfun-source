"""The multi-hop differential resolves relative paths against the caller's directory."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
import json, runpy, sys
root, destination = sys.argv[1:3]
sys.path.insert(0, root + '/scripts')
import pump_differential_output


class Stop(Exception):
    pass


class Recorder:
    def __init__(self, output, repo, candidate, *args, **kwargs):
        with open(destination, 'w', encoding='utf-8') as stream:
            json.dump({'output': str(output), 'candidate': str(candidate)}, stream)
        raise Stop


pump_differential_output.PumpReport = Recorder
sys.argv = ['pump_amm_multi_hop_differential.py', '--candidate', 'relative-candidate.so', '--output', 'relative-report.json']
try:
    runpy.run_path(root + '/scripts/pump_amm_multi_hop_differential.py', run_name='__main__')
except Stop:
    pass
'''


class MultiHopCallerPathTests(unittest.TestCase):
    def test_relative_paths_stay_in_the_caller_directory(self):
        with tempfile.TemporaryDirectory(prefix='multi-hop-caller-') as temporary:
            caller = Path(temporary).resolve()
            record = caller / 'record.json'
            environment = {key: value for key, value in os.environ.items() if key != 'PYTHONOPTIMIZE'}
            completed = subprocess.run([sys.executable, '-B', '-c', DRIVER, str(ROOT), str(record)], cwd=caller,
                                       env=environment, capture_output=True, text=True, timeout=120)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            paths = json.loads(record.read_text(encoding='utf-8'))
            self.assertEqual(paths['output'], str(caller / 'relative-report.json'))
            self.assertEqual(paths['candidate'], str(caller / 'relative-candidate.so'))


if __name__ == '__main__':
    unittest.main()
