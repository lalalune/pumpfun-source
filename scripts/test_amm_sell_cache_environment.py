"""AMM attempt cache keys bind the Cargo incremental settings that reach the build."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent / 'amm_sell'
SCRIPT = HERE / 'cache_inputs.py'
BOUND = ('CARGO_INCREMENTAL', 'CARGO_BUILD_INCREMENTAL')


def load():
    spec = importlib.util.spec_from_file_location('amm_cache_inputs_under_test', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def key(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()


class IncrementalCacheKeyTests(unittest.TestCase):
    def test_incremental_settings_change_the_attempt_key(self):
        tool = load()
        with tempfile.TemporaryDirectory(prefix='amm-cache-') as directory:
            swarm = Path(directory)
            baseline = swarm / 'baseline'
            baseline.mkdir()
            (baseline / 'sell.rs').write_text('fn sell() {}\n')
            original = swarm / 'infra/original/deployed.so'
            original.parent.mkdir(parents=True)
            original.write_bytes(b'\x7fELF')

            def attempt_key():
                return key(tool.context(swarm, HERE, baseline, SCRIPT, False))

            clean = {name: value for name, value in os.environ.items() if name not in BOUND}
            with mock.patch.dict(os.environ, clean, clear=True):
                unset = attempt_key()
                self.assertEqual(attempt_key(), unset)
                for name in BOUND:
                    with self.subTest(name=name), mock.patch.dict(os.environ, {name: '1'}):
                        self.assertNotEqual(attempt_key(), unset)


if __name__ == '__main__':
    unittest.main()
