import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_elf_symbols import fixture


class ScoreHexAddressTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.harness,self.base = self.root/'harness',self.root/'base'
        self.harness.mkdir();self.base.mkdir()
        for name in ('score.py','score_admission.py','llvm_tools.py','elf_symbols.py','compare_scores.py','original_input.py'):
            shutil.copyfile(Path(__file__).with_name(name),self.harness/name)
        image = bytes(fixture())
        self.candidate = self.root/'candidate.so';self.candidate.write_bytes(image)
        (self.base/'original.so').write_bytes(image)
        (self.base/'functions.tsv').write_text('program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n',encoding='utf-8')
        self.baseline = self.root/'baseline.json'
        self.report = self.root/'candidate-score.json'
        self.row = {'bytes':8,'normalized':True,'raw':True}
        self.report.write_text(json.dumps({'windows':{'4096':self.row}}),encoding='utf-8')

    def write_baseline(self,key,form):
        windows = {key:self.row} if form == 'mapping' else [{'start':key,'bytes':8,'normalized_matches':['local'],'raw_match':True}]
        self.baseline.write_text(json.dumps({'windows':windows}),encoding='utf-8')

    def test_comparison_accepts_both_hex_prefix_cases_and_decimal(self):
        for key in (format(4096,'#X'),hex(4096),str(4096)):
            for form in ('mapping','inventory'):
                with self.subTest(key=key,form=form):
                    self.write_baseline(key,form)
                    before = self.baseline.read_bytes()
                    result = subprocess.run([sys.executable,str(self.harness/'compare_scores.py'),str(self.baseline),str(self.report)],capture_output=True)
                    self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                    self.assertTrue(json.loads(result.stdout)['accepted'])
                    self.assertEqual(self.baseline.read_bytes(),before)

    def test_actual_scorer_accepts_the_same_saved_baseline_formats(self):
        for key in (format(4096,'#X'),hex(4096),str(4096)):
            for form in ('mapping','inventory'):
                with self.subTest(key=key,form=form):
                    self.write_baseline(key,form)
                    before = self.baseline.read_bytes(),self.candidate.read_bytes()
                    result = subprocess.run([sys.executable,str(self.harness/'score.py'),str(self.candidate),'--baseline',str(self.baseline)],capture_output=True)
                    self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                    summary = json.loads(result.stdout)
                    self.assertEqual(summary['normalized'],1)
                    self.assertEqual(summary['losses'],[])
                    self.assertEqual(summary['raw_losses'],[])
                    self.assertEqual((self.baseline.read_bytes(),self.candidate.read_bytes()),before)

    def test_equivalent_address_spellings_still_count_as_duplicates(self):
        self.baseline.write_text(json.dumps({'windows':{'0x1000':self.row,'0X1000':self.row}}),encoding='utf-8')
        commands = [('compare_scores.py',str(self.baseline),str(self.report)),('score.py',str(self.candidate),'--baseline',str(self.baseline))]
        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run([sys.executable,str(self.harness/command[0]),*command[1:]],capture_output=True)
                self.assertNotEqual(result.returncode,0)


if __name__ == '__main__': unittest.main()
