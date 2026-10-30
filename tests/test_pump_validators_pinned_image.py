"""Each real Pump validator CLI executes and reports one candidate image."""
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'evidence/original/pump/deployed.so'
OTHER=ROOT/'evidence/original/pump_fees/deployed.so'
NAMES=('admin','authority','buy','config_admin','quote','sell','volume')
DRIVER=r'''
import sys,runpy,shutil
from pathlib import Path
script,candidate,replacement,output=sys.argv[1:]
sys.path.insert(0,str(Path(script).parent))
returned=[]
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_name in ('execute','run') and frame.f_code.co_filename==script:
        returned.append(1)
        if len(returned)==2:
            sys.setprofile(None)
            shutil.copyfile(replacement,candidate)
sys.setprofile(hook)
sys.argv=[script,'--candidate',candidate,'--output',output]
try:runpy.run_path(script,run_name='__main__')
finally:
    sys.setprofile(None)
    if len(returned)<2:raise RuntimeError('candidate case did not execute')
'''

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def report(path):
    data=path.read_bytes()
    return json.loads(gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data)

class PumpValidatorPinnedImageTests(unittest.TestCase):
    def run_mutated(self,name):
        with tempfile.TemporaryDirectory(prefix='pump-validator-') as directory:
            directory=Path(directory);candidate=directory/'candidate.so';output=directory/'report.json'
            shutil.copyfile(ORIGINAL,candidate)
            script=ROOT/'scripts'/('pump_validate_'+name+'.py')
            environment=dict(os.environ);environment.pop('PYTHONOPTIMIZE',None)
            result=subprocess.run([sys.executable,'-B','-c',DRIVER,str(script),str(candidate),str(OTHER),str(output)],cwd=ROOT,env=environment,capture_output=True,text=True,timeout=240)
            self.assertEqual(result.returncode,0,name+': '+result.stdout[-1800:]+result.stderr[-1800:])
            self.assertEqual(sha(candidate),sha(OTHER),name+' did not replace the input')
            data=report(output)
            self.assertEqual(data['candidate_sha256'],sha(ORIGINAL),name)
            self.assertEqual(data['mismatches'],[],name)
            self.assertGreater(data['case_count'],1,name)
    def run_wrong(self,name):
        with tempfile.TemporaryDirectory(prefix='pump-validator-negative-') as directory:
            output=Path(directory)/'report.json'
            script=ROOT/'scripts'/('pump_validate_'+name+'.py')
            environment=dict(os.environ);environment.pop('PYTHONOPTIMIZE',None)
            result=subprocess.run([sys.executable,'-B',str(script),'--candidate',str(OTHER),'--output',str(output)],cwd=ROOT,env=environment,capture_output=True,text=True,timeout=240)
            self.assertNotEqual(result.returncode,0,name)
            self.assertTrue(output.is_file(),name+': '+result.stderr[-1800:])
            data=report(output)
            self.assertEqual(data['candidate_sha256'],sha(OTHER),name)
            self.assertTrue(data['mismatches'],name)
    def test_every_validator_keeps_the_first_candidate_image(self):
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(self.run_mutated,NAMES))
    def test_every_validator_detects_a_stable_wrong_image(self):
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(self.run_wrong,NAMES))

if __name__=='__main__':unittest.main()
