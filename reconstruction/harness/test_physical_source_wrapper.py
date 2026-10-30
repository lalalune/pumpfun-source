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


    def _compiler(self, root):
        compiler = root / 'compiler'
        compiler.write_text(
            '#!/usr/bin/env python3\nimport sys\n'
            'print("compiler-invoked")\nprint(" ".join(sys.argv[1:]))\n'
        )
        compiler.chmod(0o755)
        return compiler

    def test_optimized_python_is_refused(self):
        # The byte-equality assert in the wrapper is its only check that the
        # resolved physical file carries the same text as the registry path,
        # and `python -O` strips asserts. The wrapper must therefore refuse
        # optimized interpreters before any import, instead of silently
        # compiling through the unchecked path.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            compiler = self._compiler(root)
            registry = root / 'registry' / 'src'
            registry.mkdir(parents=True)
            source = registry / 'foo.rs'
            source.write_text('fn main() {}\n')
            for wrapper in WRAPPERS:
                for label, extra_argv, extra_env in (
                    ('-O', ['-O'], {}),
                    ('-OO', ['-OO'], {}),
                    ('PYTHONOPTIMIZE', [], {'PYTHONOPTIMIZE': '1'}),
                ):
                    with self.subTest(wrapper=wrapper.name, mode=label):
                        env = dict(
                            os.environ,
                            PUMP_LOGICAL_REGISTRY_SRC=str(root / 'registry'),
                            **extra_env,
                        )
                        result = subprocess.run(
                            [sys.executable, *extra_argv, str(wrapper),
                             str(compiler), str(source)],
                            env=env, text=True, capture_output=True,
                        )
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('Normal Python is required', result.stderr)
                        self.assertNotIn('compiler-invoked', result.stdout)

    def test_normal_python_still_canonicalizes_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            compiler = self._compiler(root)
            target = root / 'elsewhere.rs'
            target.write_text('fn main() {}\n')
            registry = root / 'registry' / 'src'
            registry.mkdir(parents=True)
            link = registry / 'foo.rs'
            link.symlink_to(target)
            for wrapper in WRAPPERS:
                with self.subTest(wrapper=wrapper.name):
                    env = dict(os.environ,
                               PUMP_LOGICAL_REGISTRY_SRC=str(root / 'registry'))
                    result = subprocess.run(
                        [sys.executable, str(wrapper), sys.executable, str(compiler), str(link)],
                        env=env, text=True, capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('compiler-invoked', result.stdout)
                    self.assertIn(str(target), result.stdout)


if __name__ == '__main__':
    unittest.main()
