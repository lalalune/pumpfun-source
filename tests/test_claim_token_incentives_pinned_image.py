"""Exercise real claim VM runs with stable image and build-metadata bindings.

The tests use captured program bytes and explicitly synthetic hash-binding JSON
for admission testing. They make no compilation or reconstructed-source claim.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/pump_claim_token_incentives_differential.py'
ORIGINAL=ROOT/'evidence/original/pump/deployed.so'
OTHER=ROOT/'evidence/original/pump_fees/deployed.so'
DRIVER=r'''
import sys,shutil,json
from pathlib import Path
scripts,original,candidate,build,other,output,mutate=sys.argv[1:]
sys.path.insert(0,scripts)
import pump_claim_token_incentives_differential as module
module.ORIGINAL=Path(original)
module.BUILD=Path(build)
returned=[]
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_name=='run_case' and frame.f_code.co_filename==module.__file__:
        returned.append(1)
        if len(returned)==2:
            sys.setprofile(None)
            shutil.copyfile(other,original)
            shutil.copyfile(other,candidate)
            Path(build).write_text(json.dumps({'test_only':'replaced metadata'}))
if mutate=='yes':sys.setprofile(hook)
sys.argv=[module.__file__,'--candidate',candidate,'--output',output]
try:module.main()
finally:
    sys.setprofile(None)
    if mutate=='yes' and len(returned)<2:raise RuntimeError('candidate case never completed')
'''

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class ClaimTokenIncentivesPinnedImageTests(unittest.TestCase):
    def staged_run(self, *, mutate=False, wrong=False, bad_binding=False):
        temporary=tempfile.TemporaryDirectory(prefix='claim-binding-')
        self.addCleanup(temporary.cleanup)
        directory=Path(temporary.name)
        original=directory/'original.so';candidate=directory/'candidate.so';build=directory/'test-only-binding.json';output=directory/'receipt.json'
        shutil.copyfile(ORIGINAL,original);shutil.copyfile(OTHER if wrong else ORIGINAL,candidate)
        build.write_text(json.dumps({'test_only':'synthetic admission metadata; not a build receipt',
            'comparison':{'original_sha256':sha(original),'candidate_sha256':sha(OTHER if bad_binding else candidate)}}))
        before=sha(build)
        result=subprocess.run([sys.executable,'-B','-c',DRIVER,str(ROOT/'scripts'),str(original),str(candidate),str(build),str(OTHER),str(output),'yes' if mutate else 'no'],cwd=ROOT,capture_output=True,text=True,timeout=180)
        return result,output,original,candidate,build,before

    def test_candidate_original_and_metadata_bindings_survive_path_changes(self):
        result,output,original,candidate,build,before=self.staged_run(mutate=True)
        self.assertEqual(result.returncode,0,result.stdout[-2000:]+result.stderr[-2000:])
        self.assertEqual(sha(original),sha(OTHER));self.assertEqual(sha(candidate),sha(OTHER))
        self.assertNotEqual(sha(build),before)
        report=json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual(report['target_sha256'],sha(ORIGINAL))
        self.assertEqual(report['candidate_sha256'],sha(ORIGINAL))
        self.assertEqual(report['build_receipt_sha256'],before)
        self.assertEqual(report['summary']['matched'],report['summary']['cases'])
        self.assertGreater(report['summary']['cases'],1)

    def test_stable_wrong_candidate_produces_real_mismatches(self):
        result,output,*_=self.staged_run(wrong=True)
        self.assertNotEqual(result.returncode,0)
        self.assertTrue(output.is_file(),result.stderr[-2000:])
        report=json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual(report['candidate_sha256'],sha(OTHER))
        self.assertLess(report['summary']['matched'],report['summary']['cases'])

    def test_mismatched_binding_is_rejected_before_publication(self):
        result,output,*_=self.staged_run(bad_binding=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('AssertionError',result.stderr)
        self.assertFalse(output.exists())

if __name__=='__main__':unittest.main()
