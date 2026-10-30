import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_elf_symbols import fixture
from test_window_cache import WindowCacheTests


class InventoryCSVTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        harness,base = self.root/'harness',self.root/'base'
        harness.mkdir();base.mkdir()
        for name in ('score.py','score_admission.py','llvm_tools.py','elf_symbols.py','original_input.py'):
            shutil.copyfile(Path(__file__).with_name(name),harness/name)
        self.image = bytes(fixture())
        self.candidate = self.root/'candidate.so';self.candidate.write_bytes(self.image)
        (base/'original.so').write_bytes(self.image)
        self.inventory = base/'functions.tsv';self.script = harness/'score.py'

    def score(self,tail,index):
        self.inventory.write_bytes(b'program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t'+tail)
        original = self.inventory.read_bytes()
        output = self.root/f'report-{index}.json'
        result = subprocess.run([sys.executable,str(self.script),str(self.candidate),'--no-baseline','--json',str(output)],capture_output=True)
        self.assertEqual(self.inventory.read_bytes(),original)
        self.assertEqual(self.candidate.read_bytes(),self.image)
        return result,output

    def test_unterminated_quoted_bounds_cannot_produce_successful_scores(self):
        for index,tail in enumerate((b'"4104',b'"4104\n',b'"4104\r\n')):
            with self.subTest(tail=tail):
                result,output = self.score(tail,index)
                self.assertNotEqual(result.returncode,0)
                self.assertIn(b'csv.Error',result.stderr)
                self.assertFalse(output.exists())

    def test_valid_unquoted_and_quoted_bounds_remain_supported(self):
        for index,tail in enumerate((b'4104\n',b'"4104"\n',b'"4104\n"\n')):
            with self.subTest(tail=tail):
                result,output = self.score(tail,index)
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                self.assertTrue(json.loads(output.read_text(encoding='utf-8'))['windows']['4096']['raw'])


if __name__ == '__main__': unittest.main()
