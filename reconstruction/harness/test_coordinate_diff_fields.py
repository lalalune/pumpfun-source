"""Check attribution classification on real captured Source-store bytes."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class CoordinateFieldTests(unittest.TestCase):
    def test_only_immediate_changes_are_coordinate_only(self):
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix='pump-coordinate-fields-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-coordinate-fields-'))
            harness = root / 'harness'
            harness.mkdir()
            base = root / 'base'
            base.mkdir()
            for name in ['score.py', 'score_admission.py', 'coords.py', 'llvm_tools.py', 'elf_symbols.py']:
                shutil.copyfile(repo / 'reconstruction/harness' / name, harness / name)
            shutil.copyfile(repo / 'evidence/original/pump/deployed.so', base / 'original.so')
            shutil.copyfile(repo / 'reconstruction/base/functions.tsv', base / 'functions.tsv')
            program = '''
import json, struct
import coords
w = next(w for w in coords.original_windows() if w['start'] == 0x18678)
raw = w['raw']
source = coords.sites(coords.ORIG, coords.OS, w['start'], raw)
site = next(s for s in source if s['len_slot'] == 4296)
assert site['path'] == 'programs/pump/src/create_v2.rs'
assert site['line_slot'] == 4288 and site['line'] == 466
original = coords.normalize(raw, w['start'], coords.OS)
results = {}
results['same'] = coords.non_coordinate_slots(original, original, source)
for label, at, relative in [('line', 4288, 4), ('length', 4296, 4),
                            ('opcode', 4296, 0), ('register', 4296, 1),
                            ('stack_offset', 4296, 2), ('ordinary', 0, 4)]:
    candidate = bytearray(original)
    candidate[at + relative] ^= 1
    results[label] = coords.non_coordinate_slots(original, bytes(candidate), source)
print(json.dumps(results))
'''
            result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', program],
                                    cwd=harness, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            actual = json.loads(result.stdout)
            self.assertEqual(actual['same'], [])
            self.assertEqual(actual['line'], [])
            self.assertEqual(actual['length'], [])
            for kind in ['opcode', 'register', 'stack_offset']:
                self.assertEqual(actual[kind], [4296], kind)
            self.assertEqual(actual['ordinary'], [0])


if __name__ == '__main__':
    unittest.main()
