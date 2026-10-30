"""Full real-VM claim-incentive CLI publication and input-preservation controls.

The candidate is a captured ELF and the build JSON is explicitly synthetic hash
admission data. No compiler or reconstructed-program equivalence is claimed.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = 'scripts/pump_claim_token_incentives_differential.py'
BUILD = 'repro/pump/claim-token-incentives/build-comparison.json'
FIXTURE = 'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'
ORIGINAL = 'evidence/original/pump/deployed.so'
FILES = (SCRIPT, 'scripts/pump_amm_reusable_harness.py', 'scripts/pump_differential_output.py',
         ORIGINAL, 'evidence/upstream/pump.json', FIXTURE,
         'evidence/dependencies/spl_token_2022/deployed.so',
         'evidence/dependencies/associated_token/deployed.so',
         'programs/pump/Cargo.toml', 'programs/pump/Cargo.lock',
         'programs/pump/src/lib.rs', 'programs/pump/src/volume_sync.rs',
         'programs/pump/src/token_incentives/mod.rs',
         'programs/pump/src/token_incentives/claim_token_incentives.rs')
DRIVER = r'''
import json,os,runpy,sys
from pathlib import Path
root,mode,output=sys.argv[1:];root=Path(root);output=Path(output)
sys.path.insert(0,str(root/'scripts'))
import pump_differential_output as publication
if mode=='fsync-failure':
    def fail(fd):raise OSError('injected fsync failure')
    publication.os.fsync=fail
elif mode in ('replace','recreate'):
    replace=publication.os.replace
    def publish(stage,destination):
        assert json.loads(Path(stage).read_bytes())['summary']['cases']==60
        assert Path(destination).read_bytes()==b'previous receipt'
        replace(stage,destination)
        if mode=='recreate':
            Path(stage).write_bytes(b'new staging owner')
            (root/'recreated.txt').write_text(str(stage))
    publication.os.replace=publish
script=str(root/'scripts/pump_claim_token_incentives_differential.py');calls=[]
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_filename==script and frame.f_code.co_name=='run_case':
        calls.append(1)
        if len(calls)==2:
            if mode=='late-alias':os.link(root/'repro/pump/claim-token-incentives/build-comparison.json',output)
            elif mode=='image-swap':
                (root/'candidate.so').write_bytes(b'changed candidate')
                (root/'evidence/original/pump/deployed.so').write_bytes(b'changed original')
sys.argv=[script,'--output',str(output)]
if mode!='original-only':sys.argv+=['--candidate',str(root/'candidate.so')]
sys.setprofile(hook)
try:runpy.run_path(script,run_name='__main__')
finally:
    sys.setprofile(None)
    (root/'executions.json').write_text(json.dumps(calls))
'''


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class ClaimIncentivePublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='claim-publication-')
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
        for name in FILES:
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,dest)
        shutil.copyfile(self.root/ORIGINAL,self.root/'candidate.so')
        self.write_binding()
        self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.output=self.root/'reports/receipt.json'

    def write_binding(self):
        path=self.root/BUILD;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'test_only':'synthetic hash admission; not a compiler receipt',
            'comparison':{'original_sha256':digest(self.root/ORIGINAL),
                          'candidate_sha256':digest(self.root/'candidate.so')}}))

    def invoke(self,mode='normal',output=None):
        env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),mode,str(output or self.output)],
            cwd=self.root,env=env,capture_output=True,text=True,timeout=60)

    def executions(self):return len(json.loads((self.root/'executions.json').read_bytes()))

    def test_full_cli_and_original_only_keep_all_cases(self):
        for mode,count in (('normal',120),('original-only',60)):
            with self.subTest(mode=mode):
                result=self.invoke(mode)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                report=json.loads(self.output.read_bytes())
                self.assertEqual(report['summary']['cases'],60)
                self.assertEqual(self.executions(),count)
                self.assertGreater(report['summary']['target_successes'],0)
                self.assertTrue(report['signed_local'])
                if mode=='normal':self.assertEqual(report['summary']['matched'],60)
                else:self.assertIsNone(report['candidate_sha256'])

    def test_all_consumed_paths_reject_direct_and_linked_outputs(self):
        names=('candidate.so',BUILD,ORIGINAL,FIXTURE,'evidence/upstream/pump.json',
               'evidence/dependencies/spl_token_2022/deployed.so',
               'programs/pump/src/token_incentives/claim_token_incentives.rs',SCRIPT)
        for name in names:
            source=self.root/name
            for kind in ('direct','symlink','hardlink'):
                with self.subTest(name=name,kind=kind):
                    for path,raw in self.inputs.items():path.write_bytes(raw)
                    destination=source if kind=='direct' else self.root/('alias-'+name.replace('/','_')+'-'+kind)
                    if kind=='symlink':destination.symlink_to(source)
                    if kind=='hardlink':os.link(source,destination)
                    result=self.invoke(output=destination)
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('report output aliases an input',result.stderr)
                    self.assertEqual(self.executions(),0)
                    self.assertEqual(source.read_bytes(),self.inputs[source])

    def test_late_build_alias_preserves_receipt_input(self):
        self.output.parent.mkdir();before=(self.root/BUILD).read_bytes()
        result=self.invoke('late-alias')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('report output aliases an input',result.stderr)
        self.assertEqual((self.root/BUILD).read_bytes(),before)
        self.assertEqual(self.executions(),120)

    def test_failed_staging_preserves_previous_report(self):
        self.output.parent.mkdir();self.output.write_bytes(b'previous receipt')
        result=self.invoke('fsync-failure')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('injected fsync failure',result.stderr)
        self.assertEqual(self.output.read_bytes(),b'previous receipt')
        self.assertEqual(list(self.output.parent.iterdir()),[self.output])
        self.assertEqual(self.executions(),120)

    def test_atomic_replace_and_consumed_stage_recreation(self):
        for mode in ('replace','recreate'):
            with self.subTest(mode=mode):
                self.output.parent.mkdir(exist_ok=True);self.output.write_bytes(b'previous receipt')
                result=self.invoke(mode)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertEqual(json.loads(self.output.read_bytes())['summary']['matched'],60)
                if mode=='recreate':
                    self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'new staging owner')

    def test_loaded_programs_survive_public_image_replacement(self):
        before=digest(self.root/ORIGINAL)
        result=self.invoke('image-swap')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes())
        self.assertEqual(report['target_sha256'],before)
        self.assertEqual(report['candidate_sha256'],before)
        self.assertEqual(report['summary']['matched'],60)
        self.assertEqual((self.root/'candidate.so').read_bytes(),b'changed candidate')

    def test_wrong_image_keeps_real_mismatch_report_and_exit_one(self):
        shutil.copyfile(ROOT/'evidence/original/pump_fees/deployed.so',self.root/'candidate.so')
        self.write_binding()
        result=self.invoke()
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes())
        self.assertEqual(report['summary']['cases'],60)
        self.assertLess(report['summary']['matched'],60)
        self.assertEqual(self.executions(),120)


if __name__=='__main__':unittest.main()
