"""Exercise the actual CLI with stale and colliding staging directories."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parent / 'disassemble.py'
FAKE_OBJDUMP = """#!{python}
import os, sys
print('fake objdump 1.0' if sys.argv[1] == '--version' else
      'disassembly of ' + os.path.basename(os.getcwd()) + ' from ' + sys.argv[-1])
"""


@unittest.skipIf(os.name == 'nt', 'POSIX executable fixture')
class DisassembleStagingUniquenessTests(unittest.TestCase):
    def run_fixture(self, collisions=0):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            objdump = root / 'objdump'
            objdump.write_text(FAKE_OBJDUMP.format(python=sys.executable))
            objdump.chmod(0o755)
            output = root / 'asm'
            stale = root / '.asm.4242'
            stale.mkdir()
            (stale / 'sentinel').write_bytes(b'previous run')
            occupied = []
            for index in range(collisions):
                path = root / ('.asm.4242-' + format(index, '016x'))
                path.mkdir(); (path / 'sentinel').write_bytes(b'other run')
                occupied.append(path)
            # Execute the real entry point with deterministic identity and tokens.
            # No FIFO rendezvous can hang if the child fails before startup.
            code = """import itertools, os, pathlib, runpy, secrets, sys
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).parent))
os.getpid = lambda: 4242
counter = itertools.count()
secrets.token_hex = lambda size: format(next(counter), '016x')
sys.argv = [sys.argv[1], '--objdump', sys.argv[2], '--output', sys.argv[3]]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
            result = subprocess.run([sys.executable, '-B', '-c', code,
                                     str(SCRIPT), str(objdump), str(output)],
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual((stale / 'sentinel').read_bytes(), b'previous run')
            for path in occupied:
                self.assertEqual((path / 'sentinel').read_bytes(), b'other run')
            expected = {path.name for path in occupied} | {stale.name}
            self.assertEqual({path.name for path in root.glob('.asm.*')}, expected)
            if collisions < 100:
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((output / 'manifest.json').is_file())
            else:
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('could not create a unique', result.stderr)
                self.assertFalse(output.exists())

    def test_stale_pid_directory_does_not_block_rerun(self):
        self.run_fixture()

    def test_random_name_collisions_preserve_other_runs(self):
        self.run_fixture(collisions=2)

    def test_exhaustion_fails_without_removing_other_runs(self):
        self.run_fixture(collisions=100)


if __name__ == '__main__':
    unittest.main()
