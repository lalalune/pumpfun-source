"""Actual full buyback CLI/VM publication tests using copied contract inputs.

These controls keep the original 369-case differential unchanged. They test
report admission/publication, not newly reconstructed contract behavior.
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
FILES = ('scripts/pump_amm_buyback_differential.py','scripts/pump_amm_admin_differential.py',
         'scripts/pump_differential_output.py','evidence/original/pump_amm/deployed.so',
         'evidence/upstream/pump_amm.json',
         'research/imported-lab/analysis/pump_fun/config-snapshot.json')
DRIVER = r'''
import json, os, runpy, sys
from pathlib import Path
root, mode, output = sys.argv[1:]; root=Path(root); output=Path(output)
sys.path.insert(0,str(root/'scripts'))
import pump_differential_output as publication
if mode=='fsync-failure':
    def fail(fd): raise OSError('injected fsync failure')
    publication.os.fsync=fail
elif mode in ('replace','recreate'):
    replace=publication.os.replace
    def publish(stage,destination):
        assert json.loads(Path(stage).read_bytes())['case_count']==369
        assert Path(destination).read_bytes()==b'prior report'
        replace(stage,destination)
        if mode=='recreate':
            Path(stage).write_bytes(b'new staging owner')
            (root/'recreated.txt').write_text(str(stage))
    publication.os.replace=publish
script=str(root/'scripts/pump_amm_buyback_differential.py');calls=[]
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_filename==script and frame.f_code.co_name=='run':
        calls.append(1)
        if len(calls)==2:
            if mode=='late-alias':os.link(root/'candidate.so',output)
            if mode=='image-swap':
                (root/'candidate.so').write_bytes(b'replaced candidate')
                (root/'evidence/original/pump_amm/deployed.so').write_bytes(b'replaced original')
sys.argv=[script,'--candidate',str(root/'candidate.so'),'--output',str(output)]
sys.setprofile(hook)
try:runpy.run_path(script,run_name='__main__')
finally:
    sys.setprofile(None)
    (root/'executions.json').write_text(json.dumps(calls))
'''


class AmmBuybackPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='amm-buyback-publication-')
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
        for name in FILES:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,path)
        shutil.copyfile(self.root/FILES[3],self.root/'candidate.so')
        self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.output=self.root/'reports/output.json'

    def invoke(self,mode='normal',output=None):
        env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),mode,str(output or self.output)],
            cwd=self.root,env=env,capture_output=True,text=True,timeout=60)

    def executions(self):return len(json.loads((self.root/'executions.json').read_bytes()))

    def test_full_cli_publishes_all_369_pairs(self):
        result=self.invoke()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes())
        self.assertEqual(report['case_count'],369)
        self.assertEqual(report['mismatches'],[])
        self.assertEqual(self.executions(),738)
        self.assertTrue(any(row['original']['error'] is None for row in report['cases']))
        self.assertTrue(any(row['original']['error'] is not None for row in report['cases']))

    def test_candidate_original_metadata_and_script_aliases_rejected_before_vm(self):
        for name in ('candidate.so',*FILES):
            source=self.root/name
            for kind in ('direct','symlink','hardlink'):
                with self.subTest(name=name,kind=kind):
                    for path,raw in self.inputs.items():path.write_bytes(raw)
                    output=source if kind=='direct' else self.root/(source.name+'-'+kind)
                    if kind=='symlink':output.symlink_to(source)
                    if kind=='hardlink':os.link(source,output)
                    result=self.invoke(output=output)
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('report output aliases an input',result.stderr)
                    self.assertEqual(self.executions(),0)
                    self.assertEqual(source.read_bytes(),self.inputs[source])

    def test_late_candidate_alias_preserves_input(self):
        self.output.parent.mkdir();candidate=self.root/'candidate.so';before=candidate.read_bytes()
        result=self.invoke('late-alias')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('report output aliases an input',result.stderr)
        self.assertEqual(candidate.read_bytes(),before)
        self.assertEqual(self.executions(),738)

    def test_fsync_failure_preserves_prior_report(self):
        self.output.parent.mkdir();self.output.write_bytes(b'prior report')
        result=self.invoke('fsync-failure')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('injected fsync failure',result.stderr)
        self.assertEqual(self.output.read_bytes(),b'prior report')
        self.assertEqual(list(self.output.parent.iterdir()),[self.output])
        self.assertEqual(self.executions(),738)

    def test_atomic_replacement_and_recreated_stage_ownership(self):
        for mode in ('replace','recreate'):
            with self.subTest(mode=mode):
                self.output.parent.mkdir(exist_ok=True);self.output.write_bytes(b'prior report')
                result=self.invoke(mode)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertEqual(json.loads(self.output.read_bytes())['case_count'],369)
                if mode=='recreate':
                    self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'new staging owner')

    def test_public_image_replacement_does_not_change_loaded_bytes(self):
        original_sha=hashlib.sha256((self.root/'candidate.so').read_bytes()).hexdigest()
        result=self.invoke('image-swap')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes())
        self.assertEqual(report['candidate_sha256'],original_sha)
        self.assertEqual(report['original_sha256'],original_sha)
        self.assertEqual(report['mismatches'],[])
        self.assertEqual((self.root/'candidate.so').read_bytes(),b'replaced candidate')
        self.assertEqual(self.executions(),738)

    def test_wrong_real_image_retains_mismatch_receipt_and_failure_exit(self):
        shutil.copyfile(ROOT/'evidence/original/mayhem/deployed.so',self.root/'candidate.so')
        result=self.invoke()
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes())
        self.assertEqual(report['case_count'],369)
        self.assertTrue(report['mismatches'])
        self.assertEqual(self.executions(),738)


if __name__=='__main__':unittest.main()
