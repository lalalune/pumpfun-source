"""A toolchain that reports the wrong sysroot must fail with or without -O."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Runs bootstrap in a child so the parent's flags cannot hide the -O behaviour.
DRIVER = '''
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
import bootstrap
root = Path(sys.argv[2])
with patch.multiple(bootstrap, HOST_PLATFORM='linux', HOST_MACHINE='x86_64', LINUX=root / 'linux',
                    HYBRID=root / 'hybrid', HOME_CACHE=root / 'cache',
                    check_sdk_linux=lambda mode: [], check_linux_libs=lambda path: [],
                    hybrid_ok_linux=lambda: True), patch.object(sys, 'argv', ['bootstrap.py']):
    sys.exit(bootstrap.main())
'''


class SysrootTests(unittest.TestCase):
    def run_bootstrap(self, root, sysroot, *flags):
        rustc = root / 'hybrid/rust/bin/rustc'
        rustc.parent.mkdir(parents=True, exist_ok=True)
        rustc.write_text(f'#!/bin/sh\necho "{sysroot}"\n', encoding='utf-8')
        rustc.chmod(0o755)
        return subprocess.run([sys.executable, '-B', *flags, '-c', DRIVER, str(HERE), str(root)],
                              capture_output=True, text=True, encoding='utf-8')

    def test_wrong_sysroot_stops_before_the_cache_is_prepared(self):
        for flags in ([], ['-O']):
            with self.subTest(flags=flags), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                result = self.run_bootstrap(root, root / 'elsewhere', *flags)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('sysroot', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertFalse((root / 'cache/locks').exists())

    def test_matching_sysroot_still_passes(self):
        for flags in ([], ['-O']):
            with self.subTest(flags=flags), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                result = self.run_bootstrap(root, root / 'hybrid/rust', *flags)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((root / 'cache/locks').is_dir())


if __name__ == '__main__':
    unittest.main()
