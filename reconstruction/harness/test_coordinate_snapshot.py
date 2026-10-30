import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from test_elf_symbols import fixture


class CoordinateSnapshotTests(unittest.TestCase):
    def exercise(self, mode, replace):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            harness,base = root/'harness',root/'base'
            harness.mkdir();base.mkdir()
            for name in ('coords.py','score.py','original_input.py','score_admission.py','llvm_tools.py','elf_symbols.py'):
                shutil.copyfile(Path(__file__).with_name(name),harness/name)
            first = bytes(fixture()); second = bytearray(first)
            for offset in (504+8,504+48+8): struct.pack_into('<Q',second,offset,0x1008)
            candidate, replacement = root/'candidate.so',root/'replacement.so'
            candidate.write_bytes(first);replacement.write_bytes(second)
            (base/'original.so').write_bytes(first)
            (base/'functions.tsv').write_text('program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n',encoding='utf-8')
            output = root/'coordinates.json'
            wrapper = """import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import coords
target=Path(sys.argv[2]); replacement=Path(sys.argv[3]); mode=sys.argv[4]; swap=sys.argv[5]=='yes'
original=Path.read_bytes
done=False
def read(path):
    global done
    result=original(path)
    if path==target and swap and not done:
        done=True
        target.write_bytes(original(replacement))
    return result
Path.read_bytes=read
sys.argv=['coords.py',mode]+(['0x1000'] if mode=='fn' else ['--json',sys.argv[6]])+['--cand',str(target)]
coords.main()
"""
            result = subprocess.run([sys.executable,'-c',wrapper,str(harness),str(candidate),str(replacement),mode,'yes' if replace else 'no',str(output)],capture_output=True)
            self.assertEqual(candidate.read_bytes(),second if replace else first)
            if mode=='fn':
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                self.assertEqual(json.loads(result.stdout),[])
            elif replace:
                self.assertEqual(result.returncode,2,result.stderr.decode('utf-8',errors='replace'))
                self.assertIn(b'candidate changed',result.stderr)
                self.assertFalse(output.exists())
            else:
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                self.assertEqual(json.loads(output.read_text(encoding='utf-8')),[])

    def test_function_symbols_belong_to_the_original_byte_snapshot(self):
        self.exercise('fn',True)

    def test_unmatched_report_rejects_a_different_scored_snapshot(self):
        self.exercise('unmatched',True)

    def test_unchanged_candidates_keep_both_cli_modes_working(self):
        self.exercise('fn',False)
        self.exercise('unmatched',False)


if __name__ == '__main__': unittest.main()
