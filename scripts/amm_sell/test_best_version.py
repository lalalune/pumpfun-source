"""Real locked bookkeeping I/O; no compiler or VM execution."""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent


@contextlib.contextmanager
def runner_at(root):
    previous_env = os.environ.get('AMM_SELL_SWARM')
    previous_lock = sys.modules.get('fcntl')
    os.environ['AMM_SELL_SWARM'] = str(root)
    if os.name == 'nt':
        import msvcrt
        lock = types.ModuleType('fcntl')
        lock.LOCK_EX, lock.LOCK_UN = 1, 2
        def flock(stream, operation):
            # Genuine Windows byte-range locking, not a no-op lock stub.
            os.lseek(stream.fileno(), 0, os.SEEK_SET)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK if operation == lock.LOCK_UN else msvcrt.LK_LOCK, 1)
        lock.flock = flock
        sys.modules['fcntl'] = lock
    try:
        spec = importlib.util.spec_from_file_location('versioned_best_runner', HERE / 'try_sell.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        yield runner
    finally:
        if previous_env is None:
            os.environ.pop('AMM_SELL_SWARM', None)
        else:
            os.environ['AMM_SELL_SWARM'] = previous_env
        if os.name == 'nt':
            if previous_lock is None:
                sys.modules.pop('fcntl', None)
            else:
                sys.modules['fcntl'] = previous_lock


class BestScoreVersionTests(unittest.TestCase):
    def entry(self, distance, lost=0):
        return {'status':'scored', 'metrics':{'score_version':3,
                'lost_windows_normalized_count':lost, 'sell_raw_equal':False,
                'sell_size':9024, 'align_distance':distance, 'slot_diffs':1}}

    def test_old_best_cannot_suppress_the_first_current_version_measurement(self):
        parent = HERE.parent.parent / 'work'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as folder:
            root = Path(folder)
            old = root / 'BEST.json'
            raw = b'{"rank":[1,0,0,0],"entry":{"metrics":{"score_version":2}}}\n'
            old.write_bytes(raw)
            with runner_at(root) as runner:
                entry = self.entry(1)
                runner.locked_append(entry)
                current = root / 'BEST-v3.json'
                self.assertTrue(current.exists())
                self.assertEqual(json.loads(current.read_bytes())['entry'], entry)
            self.assertEqual(old.read_bytes(), raw)
            self.assertEqual(len((root/'ATTEMPTS.jsonl').read_text().splitlines()), 1)

    def test_current_version_best_still_tracks_the_lower_rank(self):
        parent = HERE.parent.parent / 'work'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as folder:
            root = Path(folder)
            with runner_at(root) as runner:
                for distance in (5, 2, 4):
                    runner.locked_append(self.entry(distance))
                self.assertEqual(json.loads((root/'BEST-v3.json').read_bytes())['entry'], self.entry(2))
            self.assertFalse((root/'BEST.json').exists())
            self.assertEqual(len((root/'ATTEMPTS.jsonl').read_text().splitlines()), 3)

    def test_regressing_attempt_is_logged_without_a_best_record(self):
        parent = HERE.parent.parent / 'work'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as folder:
            root = Path(folder)
            with runner_at(root) as runner:
                runner.locked_append(self.entry(0, lost=1))
            self.assertFalse((root/'BEST-v3.json').exists())
            self.assertEqual(len((root/'ATTEMPTS.jsonl').read_text().splitlines()), 1)


if __name__ == '__main__':
    unittest.main()
