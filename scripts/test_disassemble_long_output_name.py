"""The disassembly CLI must accept valid long output basenames."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parent / 'disassemble.py'
FAKE_OBJDUMP = """#!{python}
import sys
print('fake objdump 1.0' if sys.argv[1] == '--version' else 'disassembly of ' + sys.argv[-1])
"""


@unittest.skipIf(os.name == 'nt', 'POSIX executable fixture')
class DisassembleLongOutputNameTests(unittest.TestCase):
    def run_cli(self, name):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            objdump = root / 'objdump'
            objdump.write_text(FAKE_OBJDUMP.format(python=sys.executable))
            objdump.chmod(0o755)
            parent = root / 'outputs'
            parent.mkdir()
            output = parent / name
            try:
                output.mkdir()
                output.rmdir()
            except OSError as error:
                self.skipTest(f'filesystem does not accept the requested basename: {error}')
            result = subprocess.run(
                [sys.executable, '-B', str(SCRIPT), '--objdump', str(objdump), '--output', str(output)],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(parent.iterdir()), [output])
            manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
            self.assertTrue(manifest['outputs'])
            for program in manifest['outputs']:
                self.assertTrue((output / f'{program}.asm').is_file())

    def test_long_ascii_basename(self):
        self.run_cli('p' * 240)

    def test_long_multibyte_basename(self):
        self.run_cli('측' * 80)

    def test_short_basename(self):
        self.run_cli('asm')


if __name__ == '__main__':
    unittest.main()
