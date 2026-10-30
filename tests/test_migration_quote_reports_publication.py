"""Actual migration quote CLI/VM controls for both finite case matrices.

Captured Pump is the positive candidate. The optional sibling build-comparison
file is a hash-only fixture, not evidence of a source rebuild.
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
SCRIPTS={'pump_migration_quote_differential.py':20,'pump_migration_v2_quote_differential.py':40}
FIXTURE='research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json'
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
        raw=Path(stage).read_bytes();report=json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        assert report['case_count']==(40 if '_v2_' in scriptname else 20)
        assert Path(dest).read_bytes()==b'previous receipt'
        replace(stage,dest)
        if mode=='recreate':
            Path(stage).write_bytes(b'new staging owner')
            (root/'recreated.txt').write_text(str(stage))
    publication.os.replace=publish
calls=[]
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_name=='run' and Path(frame.f_code.co_filename).name in ('pump_migrate_probe.py','pump_migrate_v2_probe.py'):
        calls.append(1)
        if len(calls)==2:
            if mode=='late-alias':os.link(root/'candidate.so',output)
            elif mode=='metadata-mutation':(root/'build-comparison.json').write_bytes(b'changed metadata')
sys.argv=[str(root/'scripts'/scriptname),'--candidate',str(root/'candidate.so'),'--output',str(output)]
if mode=='allow':sys.argv+=['--allow-mismatches']
sys.setprofile(hook)
try:runpy.run_path(sys.argv[0],run_name='__main__')
finally:
    sys.setprofile(None)
    (root/'executions.json').write_text(json.dumps(calls))
'''


class MigrationQuotePublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='migration-quote-publication-')
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
        files=['scripts/'+name for name in (*SCRIPTS,'pump_migrate_probe.py','pump_migrate_v2_probe.py',
               'probe_report.py','pump_diagnostic_audit.py','pump_differential_output.py')]
        files+=['evidence/original/'+name+'/deployed.so' for name in ('pump','pump_amm')]
        files+=['evidence/dependencies/'+name+'/deployed.so' for name in ('spl_token','spl_token_2022','associated_token')]
        files+=['evidence/upstream/pump.json',FIXTURE]
        for name in files:
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
        shutil.copyfile(self.root/'evidence/original/pump/deployed.so',self.root/'candidate.so')
        (self.root/'build-comparison.json').write_text('{"test_only":"hash fixture; no build claim"}')
        self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def reset(self):
        for path,raw in self.inputs.items():path.write_bytes(raw)

    def output(self,script):return self.root/'reports'/(script+('.gz' if '_v2_' in script else '.json'))

    def invoke(self,script,mode='normal',output=None):
        env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),script,mode,str(output or self.output(script))],
            cwd=self.root,env=env,capture_output=True,text=True,timeout=60)

    def report(self,script):
        raw=self.output(script).read_bytes()
        return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)

    def executions(self):return len(json.loads((self.root/'executions.json').read_bytes()))

    def test_complete_json_and_gzip_reports_preserve_all_cases(self):
        for script,count in SCRIPTS.items():
            with self.subTest(script=script):
                result=self.invoke(script)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                report=self.report(script)
                self.assertEqual(report['case_count'],count);self.assertEqual(self.executions(),count*2)
                self.assertEqual(report['mismatches'],[]);self.assertEqual(report['diagnostics']['mismatches'],[])
                self.assertTrue(all(row[side]['signature_verification'] for row in report['cases'] for side in ('original','candidate')))

    def test_all_consumed_input_aliases_rejected_before_vm(self):
        for script in SCRIPTS:
            for name in ('candidate.so','build-comparison.json',FIXTURE,'evidence/upstream/pump.json',
                         'evidence/original/pump_amm/deployed.so',
                         'scripts/pump_migrate_v2_probe.py' if '_v2_' in script else 'scripts/pump_migrate_probe.py'):
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

    def test_late_candidate_alias_is_preserved(self):
        for script,count in SCRIPTS.items():
            with self.subTest(script=script):
                self.output(script).parent.mkdir(exist_ok=True)
                result=self.invoke(script,'late-alias')
                self.assertNotEqual(result.returncode,0)
                self.assertIn('report output aliases an input',result.stderr)
                self.assertEqual((self.root/'candidate.so').read_bytes(),self.inputs[self.root/'candidate.so'])
                self.assertEqual(self.executions(),count*2)

    def test_failed_staging_preserves_previous_receipt(self):
        for script,count in SCRIPTS.items():
            with self.subTest(script=script):
                out=self.output(script);out.parent.mkdir(exist_ok=True);out.write_bytes(b'previous receipt')
                result=self.invoke(script,'fsync-failure')
                self.assertNotEqual(result.returncode,0)
                self.assertIn('injected fsync failure',result.stderr)
                self.assertEqual(out.read_bytes(),b'previous receipt');self.assertEqual(self.executions(),count*2)

    def test_atomic_replacement_and_recreated_stage_ownership(self):
        for script in SCRIPTS:
            for mode in ('replace','recreate'):
                with self.subTest(script=script,mode=mode):
                    out=self.output(script);out.parent.mkdir(exist_ok=True);out.write_bytes(b'previous receipt')
                    result=self.invoke(script,mode)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual(self.report(script)['mismatches'],[])
                    if mode=='recreate':self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'new staging owner')

    def test_bound_metadata_drift_preserves_previous_receipt(self):
        for script,count in SCRIPTS.items():
            with self.subTest(script=script):
                self.reset();out=self.output(script);out.parent.mkdir(exist_ok=True);out.write_bytes(b'previous receipt')
                result=self.invoke(script,'metadata-mutation')
                self.assertNotEqual(result.returncode,0)
                self.assertIn('Inputs changed during execution',result.stderr)
                self.assertEqual(out.read_bytes(),b'previous receipt');self.assertEqual(self.executions(),count*2)

    def test_wrong_real_image_and_explicit_allow_mismatches_keep_exit_contract(self):
        for script,count in SCRIPTS.items():
            for mode in ('normal','allow'):
                with self.subTest(script=script,mode=mode):
                    self.reset();shutil.copyfile(ROOT/'evidence/original/mayhem/deployed.so',self.root/'candidate.so')
                    result=self.invoke(script,mode)
                    self.assertEqual(result.returncode,0 if mode=='allow' else 1,result.stdout+result.stderr)
                    self.assertTrue(self.report(script)['mismatches'])
                    self.assertEqual(self.executions(),count*2)


if __name__=='__main__':unittest.main()
