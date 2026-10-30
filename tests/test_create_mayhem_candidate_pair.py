"""Real CLI admission, paired image snapshots, and wrong-image controls."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/pump_create_mayhem_differential.py'
PUMP=ROOT/'evidence/original/pump/deployed.so'
MAYHEM=ROOT/'evidence/original/mayhem/deployed.so'
OTHER=ROOT/'evidence/original/pump_fees/deployed.so'
DRIVER=r'''
import sys,runpy,shutil
from pathlib import Path
script,pump,mayhem,replacement,output=sys.argv[1:]
sys.path.insert(0,str(Path(script).parent))
returned=[]
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_name=='run' and frame.f_code.co_filename==script:
        returned.append(1)
        if len(returned)==2:
            sys.setprofile(None)
            shutil.copyfile(replacement,pump)
            shutil.copyfile(replacement,mayhem)
sys.setprofile(hook)
sys.argv=[script,'--candidate-pump',pump,'--candidate-mayhem',mayhem,'--output',output]
try:runpy.run_path(script,run_name='__main__')
finally:
    sys.setprofile(None)
    if len(returned)<2:raise RuntimeError('candidate pair did not execute')
'''

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_report(path):return json.loads(gzip.decompress(path.read_bytes()))
def run(arguments):
    return subprocess.run([sys.executable,'-B',str(SCRIPT),*arguments],cwd=ROOT,capture_output=True,text=True,timeout=180)

class CreateMayhemCandidateTests(unittest.TestCase):
    def test_single_candidate_is_rejected_before_inputs_or_output(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);output=directory/'retained.json.gz'
            for argument in ('--candidate-pump','--candidate-mayhem'):
                with self.subTest(argument=argument):
                    output.write_bytes(b'retained')
                    result=run([argument,str(directory/'missing.so'),'--output',str(output)])
                    self.assertEqual(result.returncode,2,result.stderr)
                    self.assertIn('must be supplied together',result.stderr)
                    self.assertNotIn('Traceback',result.stderr)
                    self.assertEqual(output.read_bytes(),b'retained')

    def test_both_candidate_images_remain_pinned_after_path_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);pump=directory/'pump.so';mayhem=directory/'mayhem.so';output=directory/'report.json.gz'
            shutil.copyfile(PUMP,pump);shutil.copyfile(MAYHEM,mayhem)
            result=subprocess.run([sys.executable,'-B','-c',DRIVER,str(SCRIPT),str(pump),str(mayhem),str(OTHER),str(output)],cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,0,result.stdout[-2000:]+result.stderr[-2000:])
            self.assertEqual(sha(pump),sha(OTHER));self.assertEqual(sha(mayhem),sha(OTHER))
            report=read_report(output)
            self.assertEqual(report['candidate_pump_sha256'],sha(PUMP))
            self.assertEqual(report['candidate_mayhem_sha256'],sha(MAYHEM))
            self.assertEqual(report['original_pump_sha256'],sha(PUMP))
            self.assertEqual(report['original_mayhem_sha256'],sha(MAYHEM))
            self.assertGreater(len(report['cases']),1)
            self.assertEqual(report['mismatches'],[])

    def test_original_only_mode_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json.gz';result=run(['--output',str(output)])
            self.assertEqual(result.returncode,0,result.stderr)
            report=read_report(output)
            self.assertIsNone(report['candidate_pump_sha256'])
            self.assertIsNone(report['candidate_mayhem_sha256'])
            self.assertTrue(all(row['candidate'] is None for row in report['cases']))

    def test_wrong_pump_image_is_executed_and_mismatches(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json.gz'
            result=run(['--candidate-pump',str(OTHER),'--candidate-mayhem',str(MAYHEM),'--output',str(output)])
            self.assertNotEqual(result.returncode,0,result.stdout[-2000:])
            self.assertTrue(output.is_file(),result.stderr[-2000:])
            report=read_report(output)
            self.assertEqual(report['candidate_pump_sha256'],sha(OTHER))
            self.assertTrue(report['mismatches'])

    def test_wrong_mayhem_image_fails_setup_without_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json.gz'
            result=run(['--candidate-pump',str(PUMP),'--candidate-mayhem',str(OTHER),'--output',str(output)])
            self.assertNotEqual(result.returncode,0,result.stdout[-2000:])
            self.assertIn('initialize_global_params failed',result.stderr)
            self.assertFalse(output.exists())

if __name__=='__main__':unittest.main()
