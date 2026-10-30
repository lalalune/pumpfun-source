import shutil
import struct
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from test_elf_symbols import fixture


class WindowCLIAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        harness, base = self.root/'harness', self.root/'base'
        harness.mkdir(); base.mkdir()
        for name in ('win.py','score.py', 'score_admission.py','elf_symbols.py','llvm_tools.py','instruction_stream.py'):
            shutil.copyfile(Path(__file__).with_name(name),harness/name)
        image = bytes(fixture())
        (base/'original.so').write_bytes(image)
        (base/'functions.tsv').write_text('program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n',encoding='utf-8')
        self.candidate = self.root/'candidate.so'
        self.candidate.write_bytes(image)
        self.script = harness/'win.py'

    def cli(self,*args):
        return subprocess.run([sys.executable,str(self.script),*args],capture_output=True)

    def test_empty_function_inventory_reports_no_candidate_without_traceback(self):
        image = fixture()
        struct.pack_into('<I',image,64+4*64+4,11)
        self.candidate.write_bytes(image)
        result = self.cli('show','0x1000','--cand',str(self.candidate))
        self.assertEqual(result.returncode,1)
        self.assertNotIn(b'Traceback',result.stderr)
        self.assertIn(b'no candidate function',result.stderr)

    def test_negative_limits_and_bad_regexes_are_cli_input_errors(self):
        cases = [('list','--top','-1'),('show','0x1000','--context','-1'),('show','0x1000','--sym','['),('sym','[')]
        for args in cases:
            with self.subTest(args=args):
                result = self.cli(*args,'--cand',str(self.candidate))
                self.assertEqual(result.returncode,2,result.stderr.decode('utf-8',errors='replace'))
                self.assertNotIn(b'Traceback',result.stderr)

    def test_valid_symbol_and_nonnegative_list_limits_remain_supported(self):
        result = self.cli('sym','local','--cand',str(self.candidate))
        self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
        self.assertIn(b'local',result.stdout)
        for limit in (0,1):
            result = self.cli('list','--all','--top',str(limit),'--cand',str(self.candidate))
            self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
            self.assertEqual(len(result.stdout.splitlines()),limit)


if __name__ == '__main__': unittest.main()
