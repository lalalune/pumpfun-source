"""The physical-source compiler wrapper must reject hidden response-file inputs."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPERS = (
    ROOT / 'reconstruction/harness/pump_physical_source_wrapper.py',
    ROOT / 'scripts/pump_physical_source_wrapper.py',
)


class PhysicalSourceWrapperTests(unittest.TestCase):
    def test_response_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            compiler = root / 'compiler'
            compiler.write_text('#!/usr/bin/env python3\nprint("compiler-invoked")\n')
            compiler.chmod(0o755)
            env = dict(os.environ, PUMP_LOGICAL_REGISTRY_SRC=str(root / 'registry'))
            for wrapper in WRAPPERS:
                for response in ('@args.rsp', '@'):
                    with self.subTest(wrapper=wrapper.name, response=response):
                        result = subprocess.run(
                            [sys.executable, str(wrapper), str(compiler), response],
                            env=env, text=True, capture_output=True,
                        )
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(
                            'response-file compiler input unsupported: ' + response,
                            result.stderr,
                        )
                        self.assertNotIn('compiler-invoked', result.stdout)


if __name__ == '__main__':
    unittest.main()
