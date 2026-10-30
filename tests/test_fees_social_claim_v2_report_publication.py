"""One full social-claim-v2 corpus and bounded real-VM publication controls."""
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
FILES=('scripts/fees_social_claim_v2_differential.py','scripts/fees_social_claim_differential.py',
       'scripts/fees_admin_differential.py','scripts/pump_amm_reusable_harness.py','scripts/pump_differential_output.py',
       'evidence/original/pump_fees/deployed.so','evidence/upstream/pump_fees.json',
       'evidence/dependencies/spl_token/deployed.so','evidence/dependencies/spl_token_2022/deployed.so',
       'evidence/dependencies/associated_token/deployed.so')
DRIVER=r'''
import json,os,runpy,sys
from pathlib import Path
root,mode,output=sys.argv[1:];root=Path(root);output=Path(output)
sys.path.insert(0,str(root/'scripts'));import pump_differential_output as publication
if mode=='fsync-failure':
    def fail(fd):raise OSError('injected fsync failure')
    publication.os.fsync=fail
elif mode in ('replace','recreate'):
    replace=publication.os.replace
    def publish(stage,destination):
        if len(json.loads(Path(stage).read_bytes())['cases'])!=2 or Path(destination).read_bytes()!=b'prior report':
            raise RuntimeError('incomplete report or premature replacement')
        replace(stage,destination)
        if mode=='recreate':Path(stage).write_bytes(b'new staging owner');(root/'recreated.txt').write_text(str(stage))
    publication.os.replace=publish
script=root/'scripts/fees_social_claim_v2_differential.py';calls=[]
def hook(frame,event,arg):
    if frame.f_code.co_filename!=str(script):return
    if event=='call' and frame.f_code.co_name=='main' and mode!='full':
        selected=frame.f_globals['cases']()[:2]
        frame.f_globals['cases']=lambda:selected
    if event=='return' and frame.f_code.co_name=='run':
        calls.append(1)
        if len(calls)==2:
            if mode=='late-alias':os.link(root/'candidate.so',output)
            if mode=='image-swap':
                (root/'candidate.so').write_bytes(b'replaced candidate')
                (root/'evidence/original/pump_fees/deployed.so').write_bytes(b'replaced original')
sys.argv=[str(script),'--output',str(output)]
if mode!='original-only':sys.argv+=['--candidate',str(root/'candidate.so')]
sys.setprofile(hook)
try:runpy.run_path(str(script),run_name='__main__')
finally:sys.setprofile(None);(root/'executions.json').write_text(json.dumps(calls))
'''


class FeesSocialClaimV2ReportPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='fees-social-v2-publication-');self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve()
        for name in FILES:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
        shutil.copyfile(self.root/FILES[5],self.root/'candidate.so')
        self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.output=self.root/'reports/output.json'

    def invoke(self,mode='normal',output=None):
        env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),mode,str(output or self.output)],cwd=self.root,env=env,capture_output=True,text=True,timeout=120)

    def executions(self):return len(json.loads((self.root/'executions.json').read_bytes()))

    def unchanged(self):
        for p,b in self.inputs.items():self.assertEqual(p.read_bytes(),b,str(p))

    def test_full_unmodified_cli_publishes_627_pairs(self):
        result=self.invoke('full');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes());self.assertEqual(len(report['cases']),627)
        self.assertEqual(self.executions(),1254);self.assertEqual(report['mismatches'],[])
        self.assertTrue(any(row['original']['error'] is None for row in report['cases']))
        self.assertTrue(any(row['original']['error'] is not None for row in report['cases']))
        expected=hashlib.sha256(self.inputs[self.root/'candidate.so']).hexdigest()
        self.assertEqual(report['candidate_sha256'],expected);self.assertEqual(report['original_sha256'],expected)
        self.unchanged()

    def test_original_only_mode(self):
        result=self.invoke('original-only');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes());self.assertEqual(len(report['cases']),2)
        self.assertIsNone(report['candidate_sha256']);self.assertEqual(self.executions(),2)
        self.assertTrue(all(row['candidate'] is None and row['match'] is None for row in report['cases']))
        self.unchanged()

    def test_all_input_aliases_rejected_before_vm(self):
        for name in ('candidate.so',*FILES):
            source=self.root/name
            for kind in ('direct','symlink','hardlink'):
                with self.subTest(name=name,kind=kind):
                    output=source if kind=='direct' else self.root/(source.name+'-'+kind)
                    if kind=='symlink':output.symlink_to(source)
                    if kind=='hardlink':os.link(source,output)
                    result=self.invoke(output=output);self.assertNotEqual(result.returncode,0)
                    self.assertIn('report output aliases an input',result.stderr);self.assertEqual(self.executions(),0)
                    self.unchanged()
                    if kind!='direct':output.unlink()

    def test_late_candidate_alias_preserves_input(self):
        self.output.parent.mkdir();result=self.invoke('late-alias');self.assertNotEqual(result.returncode,0)
        self.assertIn('report output aliases an input',result.stderr);self.assertEqual(self.executions(),4);self.unchanged()

    def test_fsync_failure_preserves_prior(self):
        self.output.parent.mkdir();self.output.write_bytes(b'prior report')
        result=self.invoke('fsync-failure');self.assertNotEqual(result.returncode,0)
        self.assertIn('injected fsync failure',result.stderr);self.assertEqual(self.output.read_bytes(),b'prior report')
        self.assertEqual(list(self.output.parent.iterdir()),[self.output]);self.assertEqual(self.executions(),4);self.unchanged()

    def test_atomic_replacement_and_recreated_stage(self):
        for mode in ('replace','recreate'):
            with self.subTest(mode=mode):
                self.output.parent.mkdir(exist_ok=True);self.output.write_bytes(b'prior report')
                result=self.invoke(mode);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertEqual(len(json.loads(self.output.read_bytes())['cases']),2);self.assertEqual(self.executions(),4)
                if mode=='recreate':self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'new staging owner')
                self.unchanged()

    def test_image_replacement_keeps_admitted_buffers(self):
        expected=hashlib.sha256(self.inputs[self.root/'candidate.so']).hexdigest()
        result=self.invoke('image-swap');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes());self.assertEqual(report['candidate_sha256'],expected)
        self.assertEqual(report['original_sha256'],expected);self.assertEqual(report['mismatches'],[])
        self.assertEqual((self.root/'candidate.so').read_bytes(),b'replaced candidate');self.assertEqual(self.executions(),4)

    def test_wrong_real_image_keeps_failure_receipt(self):
        shutil.copyfile(ROOT/'evidence/original/mayhem/deployed.so',self.root/'candidate.so')
        result=self.invoke();self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes());self.assertEqual(len(report['cases']),2)
        self.assertTrue(report['mismatches']);self.assertEqual(self.executions(),4)


if __name__=='__main__':unittest.main()
