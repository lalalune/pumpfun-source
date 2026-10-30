"""Real bootstrap/VM publication controls for both creator report CLIs.

Two retained cases per script exercise publication; the full distribution and
migration corpora are independently run during review. No source-build claim.
"""
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=('pump_creator_distribution_differential.py','pump_creator_migration_differential.py')
HELPERS=('fees_sharing_update_differential.py','fees_sharing_create_differential.py',
         'fees_donation_create_differential.py','fees_admin_differential.py',
         'pump_validate_admin.py','pump_amm_reusable_harness.py','pump_differential_output.py')
DRIVER=r'''
import gzip,json,os,runpy,sys
from pathlib import Path
root,scriptname,mode,output=sys.argv[1:];root=Path(root);output=Path(output)
sys.path.insert(0,str(root/'scripts'))
import pump_differential_output as publication
if mode=='fsync-failure':
    def fail(fd):raise OSError('injected fsync failure')
    publication.os.fsync=fail
elif mode in ('replace','recreate'):
    replace=publication.os.replace
    def publish(stage,dest):
        raw=Path(stage).read_bytes();data=json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        assert len(data['cases'])==2
        assert Path(dest).read_bytes()==b'previous receipt'
        replace(stage,dest)
        if mode=='recreate':
            Path(stage).write_bytes(b'new staging owner')
            (root/'recreated.txt').write_text(str(stage))
    publication.os.replace=publish
script=str(root/'scripts'/scriptname);calls=[]
def hook(frame,event,arg):
    if frame.f_code.co_filename!=script:return
    if event=='call' and frame.f_code.co_name=='main':
        g=frame.f_globals;selected=g['cases']()[:2];g['cases']=lambda:selected
    if event=='return' and frame.f_code.co_name=='run':
        calls.append(1)
        if len(calls)==2:
            if mode=='late-alias':os.link(root/'candidate.so',output)
            elif mode=='metadata-mutation':(root/'evidence/upstream/pump.json').write_bytes(b'changed metadata')
sys.argv=[script,'--output',str(output)]
if mode!='original-only':sys.argv+=['--candidate',str(root/'candidate.so')]
sys.setprofile(hook)
try:runpy.run_path(script,run_name='__main__')
finally:
    sys.setprofile(None)
    (root/'executions.json').write_text(json.dumps(calls))
'''


class CreatorReportsPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='creator-reports-publication-')
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
        names=['scripts/'+name for name in (*SCRIPTS,*HELPERS)]
        names += ['evidence/original/'+name+'/deployed.so' for name in ('pump','pump_fees','pump_amm')]
        names += ['evidence/upstream/'+name+'.json' for name in ('pump','pump_fees','pump_amm')]
        names += ['evidence/dependencies/'+name+'/deployed.so' for name in ('spl_token','spl_token_2022','associated_token')]
        names += ['research/imported-lab/analysis/pump_fun/config-snapshot.json']
        for name in names:
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
        shutil.copyfile(self.root/'evidence/original/pump/deployed.so',self.root/'candidate.so')
        self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def reset(self):
        for path,raw in self.inputs.items():path.write_bytes(raw)

    def output(self,script):return self.root/'reports'/(script+'.json.gz' if 'migration' in script else script+'.json')

    def invoke(self,script,mode='normal',output=None):
        env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),script,mode,str(output or self.output(script))],
            cwd=self.root,env=env,capture_output=True,text=True,timeout=60)

    def report(self,script):
        raw=self.output(script).read_bytes()
        return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)

    def executions(self):return len(json.loads((self.root/'executions.json').read_bytes()))

    def test_real_cli_and_original_only_keep_cases(self):
        for script in SCRIPTS:
            for mode,count in (('normal',4),('original-only',2)):
                with self.subTest(script=script,mode=mode):
                    result=self.invoke(script,mode)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual(len(self.report(script)['cases']),2)
                    self.assertEqual(self.report(script)['mismatches'],[])
                    self.assertEqual(self.executions(),count)

    def test_candidate_metadata_dependency_and_script_aliases_fail_before_execution(self):
        names=('candidate.so','evidence/original/pump/deployed.so','evidence/upstream/pump.json',
               'evidence/dependencies/spl_token/deployed.so','scripts/fees_sharing_update_differential.py')
        for script in SCRIPTS:
            for name in names:
                source=self.root/name
                for kind in ('direct','symlink','hardlink'):
                    with self.subTest(script=script,name=name,kind=kind):
                        self.reset();dest=source if kind=='direct' else self.root/('alias-'+script+'-'+name.replace('/','_')+'-'+kind)
                        if kind=='symlink':dest.symlink_to(source)
                        if kind=='hardlink':os.link(source,dest)
                        result=self.invoke(script,output=dest)
                        self.assertNotEqual(result.returncode,0)
                        self.assertIn('report output aliases an input',result.stderr)
                        self.assertEqual(self.executions(),0)
                        self.assertEqual(source.read_bytes(),self.inputs[source])

    def test_late_candidate_alias_preserves_image(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                output=self.output(script);output.parent.mkdir(exist_ok=True)
                result=self.invoke(script,'late-alias')
                self.assertNotEqual(result.returncode,0)
                self.assertIn('report output aliases an input',result.stderr)
                self.assertEqual((self.root/'candidate.so').read_bytes(),self.inputs[self.root/'candidate.so'])
                self.assertEqual(self.executions(),4)

    def test_failed_staging_preserves_previous_report(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                output=self.output(script);output.parent.mkdir(exist_ok=True);output.write_bytes(b'previous receipt')
                result=self.invoke(script,'fsync-failure')
                self.assertNotEqual(result.returncode,0)
                self.assertIn('injected fsync failure',result.stderr)
                self.assertEqual(output.read_bytes(),b'previous receipt')
                self.assertEqual(self.executions(),4)

    def test_atomic_replacement_and_consumed_stage_recreation(self):
        for script in SCRIPTS:
            for mode in ('replace','recreate'):
                with self.subTest(script=script,mode=mode):
                    output=self.output(script);output.parent.mkdir(exist_ok=True);output.write_bytes(b'previous receipt')
                    result=self.invoke(script,mode)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual(len(self.report(script)['cases']),2)
                    if mode=='recreate':self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'new staging owner')

    def test_migration_existing_metadata_guard_still_preserves_old_output(self):
        script=SCRIPTS[1];output=self.output(script);output.parent.mkdir();output.write_bytes(b'previous receipt')
        result=self.invoke(script,'metadata-mutation')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('AssertionError',result.stderr)
        self.assertEqual(output.read_bytes(),b'previous receipt')
        self.assertEqual(self.executions(),4)

    def test_wrong_real_candidate_keeps_failure_receipts(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                shutil.copyfile(ROOT/'evidence/original/mayhem/deployed.so',self.root/'candidate.so')
                result=self.invoke(script)
                self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                self.assertTrue(self.report(script)['mismatches'])
                self.assertEqual(self.executions(),4)


if __name__=='__main__':unittest.main()
