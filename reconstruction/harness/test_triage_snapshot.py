import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from test_elf_symbols import fixture


class TriageSnapshotTests(unittest.TestCase):
    def exercise(self, replace):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            harness, base = root/'harness', root/'base'
            harness.mkdir(); base.mkdir()
            for module in Path(__file__).parent.glob('*.py'):
                if not module.name.startswith('test_'):
                    shutil.copyfile(module, harness/module.name)
            first = bytes(fixture())
            second = bytearray(first)
            second[424:440] = struct.pack('<BBhi', 0xb7, 1, 0, 77)*2
            candidate, replacement = root/'candidate.so', root/'replacement.so'
            candidate.write_bytes(first); replacement.write_bytes(second)
            (base/'original.so').write_bytes(first)
            (base/'functions.tsv').write_bytes(b'program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n')
            output = root/'triage.json'
            wrapper = r"""import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import triage
candidate,replacement,output=map(Path,sys.argv[2:5])
swap=sys.argv[5]=='yes'
read_bytes=Path.read_bytes
done=False
def read(path):
    global done
    data=read_bytes(path)
    if path==candidate and swap and not done:
        done=True
        candidate.write_bytes(read_bytes(replacement))
    return data
Path.read_bytes=read
sys.argv=['triage.py','--cand',str(candidate),'--json',str(output)]
triage.main()
"""
            result = subprocess.run([sys.executable,'-c',wrapper,str(harness),str(candidate),str(replacement),str(output),'yes' if replace else 'no'],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
            self.assertEqual(candidate.read_bytes(),second if replace else first)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8')),[], 'original snapshot is an exact match; later candidate bytes must not create unmatched rows')

    def test_replaced_candidate_cannot_mix_scored_memberships_and_loaded_bytes(self):
        self.exercise(True)

    def test_stable_candidate_still_reports_exact_membership(self):
        self.exercise(False)


if __name__ == '__main__': unittest.main()
