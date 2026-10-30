"""Real 119-case creator-collection CLI publication and input guards.

Captured Pump bytes are used on both sides for positive controls. These checks
prove report behavior; no compiler or reconstructed-program claim is made.
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
FILES=('scripts/pump_creator_collect_differential.py','scripts/pump_differential_output.py',
       'evidence/original/pump/deployed.so','evidence/upstream/pump.json')
DRIVER=r'''
import gzip,json,os,runpy,sys
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
        assert json.loads(gzip.decompress(Path(stage).read_bytes()))['case_count']==119
        assert Path(destination).read_bytes()==b'previous receipt'
        replace(stage,destination)
        if mode=='recreate':
            Path(stage).write_bytes(b'new staging owner')
            (root/'recreated.txt').write_text(str(stage))
    publication.os.replace=publish
script=str(root/'scripts/pump_creator_collect_differential.py');calls=[]
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_filename==script and frame.f_code.co_name=='execute':
        calls.append(1)
        if len(calls)==2:
            if mode=='late-alias':os.link(root/'candidate.so',output)
            elif mode=='metadata-mutation':(root/'evidence/upstream/pump.json').write_bytes(b'changed metadata')
sys.argv=[script,'--candidate',str(root/'candidate.so'),'--output',str(output)]
sys.setprofile(hook)
try:runpy.run_path(script,run_name='__main__')
finally:
    sys.setprofile(None)
    (root/'executions.json').write_text(json.dumps(calls))
'''


class CreatorCollectPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='creator-collect-publication-')
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
        for name in FILES:
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,dest)
        shutil.copyfile(self.root/FILES[2],self.root/'candidate.so')
        self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.output=self.root/'reports/report.json.gz'

    def invoke(self,mode='normal',output=None):
        env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),mode,str(output or self.output)],
            cwd=self.root,env=env,capture_output=True,text=True,timeout=60)

    def executions(self):return len(json.loads((self.root/'executions.json').read_bytes()))

    def report(self):return json.loads(gzip.decompress(self.output.read_bytes()))

    def test_normal_full_cli_keeps_all_cases_and_gzip(self):
        result=self.invoke()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=self.report();self.assertEqual(report['case_count'],119)
        self.assertEqual(report['mismatches'],[]);self.assertEqual(self.executions(),238)
        self.assertTrue(any(row['original']['error'] is None for row in report['cases']))
        self.assertTrue(any(row['original']['error'] is not None for row in report['cases']))
        self.assertTrue(all(all(row[side]['signature_verification'])
                            for row in report['cases'] for side in ('original','candidate')))

    def test_all_input_aliases_fail_before_execution(self):
        for name in ('candidate.so',*FILES):
            source=self.root/name
            for kind in ('direct','symlink','hardlink'):
                with self.subTest(name=name,kind=kind):
                    for path,raw in self.inputs.items():path.write_bytes(raw)
                    output=source if kind=='direct' else self.root/('alias-'+name.replace('/','_')+'-'+kind)
                    if kind=='symlink':output.symlink_to(source)
                    if kind=='hardlink':os.link(source,output)
                    result=self.invoke(output=output)
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('report output aliases an input',result.stderr)
                    self.assertEqual(self.executions(),0)
                    self.assertEqual(source.read_bytes(),self.inputs[source])

    def test_late_candidate_alias_does_not_clobber_input(self):
        self.output.parent.mkdir();before=(self.root/'candidate.so').read_bytes()
        result=self.invoke('late-alias')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('report output aliases an input',result.stderr)
        self.assertEqual((self.root/'candidate.so').read_bytes(),before)
        self.assertEqual(self.executions(),238)

    def test_fsync_failure_preserves_previous_receipt(self):
        self.output.parent.mkdir();self.output.write_bytes(b'previous receipt')
        result=self.invoke('fsync-failure')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('injected fsync failure',result.stderr)
        self.assertEqual(self.output.read_bytes(),b'previous receipt')
        self.assertEqual(list(self.output.parent.iterdir()),[self.output])
        self.assertEqual(self.executions(),238)

    def test_atomic_replace_and_recreated_stage_ownership(self):
        for mode in ('replace','recreate'):
            with self.subTest(mode=mode):
                self.output.parent.mkdir(exist_ok=True);self.output.write_bytes(b'previous receipt')
                result=self.invoke(mode)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertEqual(self.report()['mismatches'],[])
                if mode=='recreate':
                    self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'new staging owner')

    def test_existing_metadata_guard_prevents_success_publication(self):
        self.output.parent.mkdir();self.output.write_bytes(b'previous receipt')
        result=self.invoke('metadata-mutation')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('AssertionError',result.stderr)
        self.assertEqual(self.executions(),238)
        self.assertEqual(self.output.read_bytes(),b'previous receipt')

    def test_wrong_real_image_publishes_mismatches_and_exits_one(self):
        shutil.copyfile(ROOT/'evidence/original/mayhem/deployed.so',self.root/'candidate.so')
        result=self.invoke()
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        report=self.report();self.assertEqual(report['case_count'],119)
        self.assertTrue(report['mismatches']);self.assertEqual(self.executions(),238)


if __name__=='__main__':unittest.main()
