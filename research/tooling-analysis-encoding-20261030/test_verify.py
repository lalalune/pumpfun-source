"""Exercise the actual retained-capture CLIs with controlled text defaults."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = r"""
import builtins, io, runpy, sys
codec = sys.argv.pop(1)
def adapt(original):
    def wrapped(file, mode='r', buffering=-1, encoding=None, *args, **kwargs):
        if 'b' not in mode and encoding in (None, 'locale'):
            encoding = codec
        return original(file, mode, buffering, encoding, *args, **kwargs)
    return wrapped
builtins.open = adapt(builtins.open)
io.open = adapt(io.open)
script = sys.argv.pop(1)
sys.argv[0] = script
runpy.run_path(script, run_name='__main__')
"""

class EncodingTests(unittest.TestCase):
    def run_cli(self, script, args, codec):
        command = [sys.executable, '-B']
        if codec is not None:
            command += ['-c', ADAPTER, codec]
        result = subprocess.run(command + [str(script), *args], cwd=ROOT,
                                env={**os.environ, 'PYTHONUTF8': '0', 'PYTHONIOENCODING': 'utf-8'},
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def check_generator(self, name, expected):
        with tempfile.TemporaryDirectory() as temp:
            packets = []
            for index, codec in enumerate(('cp949', 'utf-8', None)):
                packet = Path(temp) / str(index)
                self.run_cli(ROOT / 'scripts' / name,
                             ['--program', 'mayhem', '--output', str(packet)], codec)
                self.assertEqual(len(list(packet.iterdir())), expected)
                self.assertIn('mayhem \u2014', (packet / 'README.md').read_text(encoding='utf-8'))
                self.run_cli(packet / 'verify.py', [], codec)
                packets.append({p.name: json.loads(p.read_text(encoding='utf-8'))
                                for p in packet.glob('*.json')})
            self.assertEqual(packets[0], packets[1])
            self.assertEqual(packets[0], packets[2])

    def test_program_analysis(self):
        self.check_generator('analyze_program.py', 8)

    def test_section_analysis(self):
        self.check_generator('deep_section_analysis.py', 9)

if __name__ == '__main__':
    unittest.main()
