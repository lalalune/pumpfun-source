"""Real Fees fees_donation_create_differential CLI mutations bind execution and receipt to the same image."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/fees_donation_create_differential.py'
ORIGINAL=ROOT/'evidence/original/pump_fees/deployed.so'
OTHER=ROOT/'evidence/original/mayhem/deployed.so'
DRIVER=r'''
import sys,runpy,shutil
from pathlib import Path
script,candidate,replacement,output=sys.argv[1:]
sys.path.insert(0,str(Path(script).parent))
returned=[]
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_name=='run' and frame.f_code.co_filename==script:
        returned.append(1)
        if len(returned)==2:
            sys.setprofile(None)
            shutil.copyfile(replacement,candidate)
sys.setprofile(hook)
sys.argv=[script,'--candidate',candidate,'--output',output]
try:runpy.run_path(script,run_name='__main__')
finally:
    sys.setprofile(None)
    if len(returned)<2:raise RuntimeError('candidate case never completed')
'''

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class FeesPinnedImageTests(unittest.TestCase):
    def test_replaced_candidate_cannot_change_the_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);candidate=directory/'candidate.so';output=directory/'report.json'
            shutil.copyfile(ORIGINAL,candidate)
            result=subprocess.run([sys.executable,'-B','-c',DRIVER,str(SCRIPT),str(candidate),str(OTHER),str(output)],cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,0,result.stdout[-2000:]+result.stderr[-2000:])
            self.assertEqual(sha(candidate),sha(OTHER))
            report=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['candidate_sha256'],sha(ORIGINAL))
            self.assertEqual(report['original_sha256'],sha(ORIGINAL))
            self.assertGreater(len(report['cases']),1)
            self.assertEqual(report['mismatches'],[])

    def test_stable_wrong_candidate_is_actually_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json'
            result=subprocess.run([sys.executable,'-B',str(SCRIPT),'--candidate',str(OTHER),'--output',str(output)],cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertNotEqual(result.returncode,0,result.stdout[-2000:])
            self.assertTrue(output.is_file(),result.stderr[-2000:])
            report=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['candidate_sha256'],sha(OTHER))
            self.assertTrue(report['mismatches'])

if __name__=='__main__':unittest.main()
