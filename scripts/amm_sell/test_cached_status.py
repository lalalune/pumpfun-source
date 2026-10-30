"""Actual CLI cache-replay status tests; no compiler or VM runs."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location('cache_status_score', HERE / 'sell_score.py')
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)
cache_spec = importlib.util.spec_from_file_location('cache_admission_fixture', HERE / 'cache_inputs.py')
cache_inputs = importlib.util.module_from_spec(cache_spec)
cache_spec.loader.exec_module(cache_inputs)

# Windows lacks fcntl. Only provide its import name; any attempt to use locking
# fails. The actual cache-hit CLI must never call a lock or a native build.
WINDOWS_ENTRY = """
import runpy, sys, types
sys.modules['fcntl'] = types.ModuleType('fcntl')
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""


class CachedAttemptStatusTests(unittest.TestCase):
    def replay(self, status, goal, expected):
        parent = ROOT / 'work'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='cached-status-', dir=parent) as folder:
            swarm = Path(folder)
            source = swarm / 'baselines/pristine-ws/programs/pump-amm/src/instructions/swap/sell.rs'
            source.parent.mkdir(parents=True)
            source_bytes = b'// Synthetic source identity for cache replay only.\n'
            source.write_bytes(source_bytes)
            original = swarm / 'infra/original/deployed.so'
            original.parent.mkdir(parents=True)
            original.write_bytes(b'Synthetic cache status fixture; never loaded or compiled.')
            key_doc = {'score_version': score.SCORE_VERSION,
                       'sell': hashlib.sha256(source_bytes).hexdigest(),
                       'patch': None, 'flags': '', 'link': None,
                       'context': cache_inputs.context(swarm, HERE, swarm / 'baselines/pristine-ws',
                                                      Path(score.elf_reader.__file__), False)}
            key = hashlib.sha256(json.dumps(key_doc, sort_keys=True).encode()).hexdigest()
            cache = swarm / 'cache'
            cache.mkdir()
            out = swarm / 'lanes/fixture/build0/out/synthetic-status-only'
            out.mkdir(parents=True)
            for name in ('sell.rs', 'build.log', 'build-record.json', 'candidate.so', 'symbols.so'):
                (out / name).write_bytes(b'Synthetic status fixture, not compiler/ELF evidence.\n')
            entry = {'key': key, 'inputs': key_doc, 'status': status, 'out_dir': str(out),
                     'candidate_sha256': cache_inputs.sha(out / 'candidate.so'),
                     'unstripped_sha256': cache_inputs.sha(out / 'symbols.so'),
                     'metrics': {'sell_raw_equal': goal} if status != 'build_failed' else None}
            entry['output_sha256'] = cache_inputs.outputs(entry, swarm)
            raw = (json.dumps(entry) + '\n').encode()
            cached = cache / (key + '.json')
            cached.write_bytes(raw)
            args = [str(HERE / 'try_sell.py'), '--lane', 'fixture', '--approach', 'cached-status',
                    '--hypothesis', 'Synthetic cache replay only', '--baseline']
            command = [sys.executable, '-c', WINDOWS_ENTRY, *args] if os.name == 'nt' else [sys.executable, *args]
            result = subprocess.run(command, env={**os.environ, 'AMM_SELL_SWARM': str(swarm)},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output, {**entry, 'duplicate': True})
            self.assertEqual(cached.read_bytes(), raw)
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(cache_inputs.outputs(entry, swarm), entry['output_sha256'])
            self.assertFalse((swarm / 'ATTEMPTS.jsonl').exists())
            self.assertFalse((swarm / 'BEST.json').exists())

    def test_cached_build_failure_stays_a_build_failure(self):
        self.replay('build_failed', False, 2)

    def test_cached_scored_attempt_stays_successful(self):
        self.replay('scored', False, 0)

    def test_cached_goal_keeps_its_distinct_status(self):
        self.replay('GOAL_SELL_RAW_EQUAL', True, 3)


if __name__ == '__main__':
    unittest.main()
