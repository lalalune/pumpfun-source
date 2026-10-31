"""A build must not supply the scorer code that judges it.

score.py imports elf_symbols inside candidate_functions, so an oracle process
first loaded that module while scoring, after the crate build had finished. A
build script that rewrote the module therefore ran its own symbol reader in the
oracle and could publish a pass verdict for a candidate that matches nothing.

The harness is copied so the build stub can rewrite a module for real, and the
oracle runs in a child process so that module is not already imported.
"""

from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest


HARNESS = Path(__file__).resolve().parent
DRIVER = r'''
import sys
from pathlib import Path
from unittest.mock import patch

harness, root = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(harness))
import match_oracle as oracle

FORGED = """
from pathlib import Path
Path({marker!r}).write_text('ran')
def function_symbols(blob):
    return [(8, 8, 'forged')]
""".format(marker=str(root / 'forged-reader-ran'))


def build(source, work, output, quiet=True, recipe=None):
    (harness / 'elf_symbols.py').write_text(FORGED)
    (output / 'unstripped.so').write_bytes(b'not an ELF image')
    return {'ok': True, 'runtime_valid': True, 'stack_warnings': []}


window = {'start': 8, 'bytes': 8, 'raw': b'\0' * 8, 'norm': b'\0' * 8}
with patch.object(oracle.score, 'BASE', root), \
        patch.object(oracle.score, 'original_windows', return_value=[window]), \
        patch.object(oracle.score, 'sections', return_value={}), \
        patch.object(oracle.score, 'body', return_value=b'\0' * 8), \
        patch.object(oracle.score, 'normalize', return_value=b'\0' * 8), \
        patch.object(oracle.fastbuild, 'build', side_effect=build):
    try:
        code = oracle.evaluate(root, root / 'work', root / 'out', 8, 'normalized', 'identity')
    except ValueError as error:
        print(f'refused: {error}')
        code = 2
raise SystemExit(code)
'''


class MatchOracleScorerModuleTests(unittest.TestCase):
    def test_build_cannot_replace_the_symbol_reader_it_is_scored_with(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            harness = root / 'harness'
            harness.mkdir()
            for path in HARNESS.glob('*.py'):
                if not path.name.startswith('test_'):
                    shutil.copy2(path, harness / path.name)
            for name in ('original.so', 'functions.tsv'):
                (root / name).write_bytes(b'fixture')
            (root / 'out').mkdir()
            driver = root / 'driver.py'
            driver.write_text(DRIVER)

            run = subprocess.run([sys.executable, '-B', str(driver), str(harness), str(root)],
                                 capture_output=True, text=True, timeout=60)

            self.assertIn(run.returncode, (0, 1, 2), run.stderr)
            self.assertFalse((root / 'forged-reader-ran').exists(),
                             'the module a build rewrote ran inside the oracle')
            verdict = root / 'out/verdict.json'
            if verdict.exists():
                self.assertNotEqual(json.loads(verdict.read_text())['status'], 'pass')
            self.assertNotEqual(run.returncode, 0)


if __name__ == '__main__':
    unittest.main()
