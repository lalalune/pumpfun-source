"""A shard outside 1..shards is a usage error, not an assertion failure."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    (ROOT / 'scripts' / 'pump_validate_parallel.py',
     ('--candidate', 'candidate', '--source-directory', 'source',
      '--build-comparison', 'comparison')),
    (ROOT / 'scripts' / 'pump_replay_main_checkpoint.py', ()),
)
MESSAGE = '--shard must be between 1 and --shards'


def run(script, required, output, shard, shards):
    arguments = []
    for flag, _ in zip(required[::2], required[1::2]):
        arguments += [flag, flag.lstrip('-')]
    arguments += ['--output', str(output), '--shard', str(shard), '--shards', str(shards)]
    environment = dict(os.environ)
    environment.pop('PYTHONOPTIMIZE', None)
    return subprocess.run(
        [sys.executable, '-B', str(script), *arguments],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=120,
    )


class ShardAdmissionTests(unittest.TestCase):
    def test_a_shard_outside_the_range_is_a_usage_error(self):
        with tempfile.TemporaryDirectory(prefix='shard-admission-') as directory:
            for script, required in SCRIPTS:
                for shard, shards in ((0, 1), (9, 1), (5, 2), (-1, 2), (3, 1)):
                    with self.subTest(script=script.name, shard=shard, shards=shards):
                        output = Path(directory) / f'{script.stem}-{shard}-{shards}.json'
                        result = run(script, required, output, shard, shards)
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn(MESSAGE, result.stderr)
                        self.assertNotIn('Traceback', result.stderr)
                        self.assertNotIn('AssertionError', result.stderr)
                        self.assertFalse(output.exists())

    def test_a_shard_inside_the_range_reaches_the_runner(self):
        with tempfile.TemporaryDirectory(prefix='shard-admission-') as directory:
            for script, required in SCRIPTS:
                for shard, shards in ((1, 1), (1, 4), (2, 2), (4, 4)):
                    with self.subTest(script=script.name, shard=shard, shards=shards):
                        output = Path(directory) / f'{script.stem}-{shard}-{shards}.json'
                        result = run(script, required, output, shard, shards)
                        self.assertNotIn(MESSAGE, result.stderr)


if __name__ == '__main__':
    unittest.main()
