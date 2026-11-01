"""The trial process group must not outlive a killed experiment runner."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


H = Path(__file__).resolve().parent

RUNNER = r"""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from experiment_runner import run_trial

source, destination, marker = map(Path, sys.argv[2:])
command = [sys.executable, '-c', '''
import os
from pathlib import Path
import sys
import time
Path(sys.argv[1]).write_text(str(os.getpid()), encoding="ascii")
Path(sys.argv[2], "partial.log").write_text("started\\n", encoding="ascii")
time.sleep(30)
''', str(marker), '{out}']
run_trial(source, command, destination, timeout=60)
"""


@unittest.skipUnless(os.name == 'posix', 'requires POSIX process groups and signals')
class RunnerParentDeathTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'input').write_text('fixture\n', encoding='ascii')

    def process_exists(self, pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def wait_for(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(.02)
        return predicate()

    def run_parent_death(self, sig):
        marker = self.root / f'child-{sig}.pid'
        destination = self.root / f'result-{sig}'
        runner = subprocess.Popen(
            [sys.executable, '-I', '-B', '-c', RUNNER, str(H), str(self.source),
             str(destination), str(marker)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        self.addCleanup(runner.kill)
        self.addCleanup(runner.stderr.close)
        self.assertTrue(self.wait_for(marker.exists, 10), 'trial child did not start')
        child = int(marker.read_text(encoding='ascii'))

        def stop_leaked_group():
            try:
                if os.getpgid(child) == child:
                    os.killpg(child, signal.SIGKILL)
                else:
                    os.kill(child, signal.SIGKILL)
            except ProcessLookupError:
                pass

        self.addCleanup(stop_leaked_group)
        os.kill(runner.pid, sig)
        runner.wait(timeout=5)
        self.assertTrue(self.wait_for(lambda: not self.process_exists(child)),
                        f'trial child {child} survived runner signal {sig}')

        attempts = sorted(destination.glob('attempt-*'))
        self.assertEqual(len(attempts), 1)
        metadata = json.loads((attempts[0] / 'attempt.json').read_text(encoding='utf-8'))
        self.assertEqual(metadata['schema'], 'experiment-attempt-v1')
        self.assertIn(metadata['state'], ('staging', 'running'))
        self.assertEqual(metadata['attempt'], attempts[0].name)
        self.assertEqual(metadata['key'], __import__('hashlib').sha256(
            json.dumps(metadata['inputs'], sort_keys=True).encode()).hexdigest())
        self.assertEqual((attempts[0] / 'output/partial.log').read_text(encoding='ascii'),
                         'started\n')
        self.assertFalse((destination / 'latest.json').exists())

    def test_sigterm_stops_owned_trial_group(self):
        self.run_parent_death(signal.SIGTERM)

    def test_sigkill_stops_owned_trial_group(self):
        self.run_parent_death(signal.SIGKILL)


if __name__ == '__main__':
    unittest.main()
