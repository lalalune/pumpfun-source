"""Real full-matrix CLI controls for all five Pump trade report writers.

No case generator or VM is mocked. Independent subprocesses are bounded to two
at a time. Captured images exercise report behavior, not source reconstruction.
"""
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
SCRIPTS={'pump_buy_v2_differential.py':216,'pump_sell_v2_differential.py':206,
         'pump_legacy_buy_differential.py':284,'pump_legacy_sell_differential.py':115,
         'pump_legacy_sell_configured_fee_differential.py':28}
FIXTURE='research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'
IMAGES=('original/pump','original/pump_fees','dependencies/spl_token',
        'dependencies/spl_token_2022','dependencies/associated_token')
DRIVER=r'''
import gzip,json,os,runpy,sys
from pathlib import Path
root,scriptname,mode,output=sys.argv[1:];root=Path(root);output=Path(output)
sys.path.insert(0,str(root/'scripts'))
import pump_differential_output as publication
if mode=='fsync-failure':
    def fail(fd):raise OSError('injected fsync failure')
    publication.os.fsync=fail
elif mode=='atomic':
    replace=publication.os.replace
    def publish(stage,destination):
        raw=Path(stage).read_bytes();report=json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        assert report['case_count']>0 and not report['mismatches']
        assert Path(destination).read_bytes()==b'previous receipt'
        replace(stage,destination)
        Path(stage).write_bytes(b'new staging owner')
        (root/('recreated-'+scriptname+'.txt')).write_text(str(stage))
    publication.os.replace=publish
calls=[]
owner='pump_legacy_sell_differential.py' if 'configured_fee' in scriptname else scriptname
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_name=='run' and Path(frame.f_code.co_filename).name==owner:
        calls.append(1)
        if len(calls)==2:
            if mode=='late-alias':os.link(root/'candidate.so',output)
            elif mode=='late-fixture-alias':os.link(root/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',output)
            elif mode=='late-capture-alias':os.link(root/'evidence/original/pump/capture.json',output)
sys.argv=[str(root/'scripts'/scriptname),'--output',str(output)]
if mode!='original-only':sys.argv+=['--candidate',str(root/'candidate.so')]
if mode=='include-baseline':sys.argv+=['--include-baseline']
sys.setprofile(hook)
try:runpy.run_path(sys.argv[0],run_name='__main__')
finally:
    sys.setprofile(None)
    (root/('executions-'+scriptname+'.json')).write_text(json.dumps(calls))
'''


class TradeReportPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='pump-trade-publication-')
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
        files=['scripts/'+name for name in (*SCRIPTS,'pump_trade_fixture.py',
               'pump_amm_reusable_harness.py','pump_differential_output.py')]
        files+=[f'evidence/{name}/{file}' for name in IMAGES for file in ('deployed.so','capture.json')]
        files+=['evidence/upstream/pump.json',FIXTURE]
        for name in files:
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
        shutil.copyfile(self.root/'evidence/original/pump/deployed.so',self.root/'candidate.so')
        self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def output(self,script):return self.root/'reports'/(script+'.json')

    def invoke(self,script,mode='normal',output=None):
        env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),script,mode,str(output or self.output(script))],
            cwd=self.root,env=env,capture_output=True,text=True,timeout=180)

    def batched(self,scripts,mode):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda name:(name,self.invoke(name,mode)),scripts))
        return results

    def report(self,script):
        raw=self.output(script).read_bytes()
        return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)

    def executions(self,script):return len(json.loads((self.root/('executions-'+script+'.json')).read_bytes()))

    def test_full_case_matrices_publish_atomically_and_preserve_recreated_stages(self):
        for script in SCRIPTS:
            out=self.output(script);out.parent.mkdir(exist_ok=True);out.write_bytes(b'previous receipt')
        for script,result in self.batched(SCRIPTS,'atomic'):
            with self.subTest(script=script):
                self.assertEqual(result.returncode,0,result.stdout[-2000:]+result.stderr[-2000:])
                report=self.report(script)
                self.assertEqual(report['case_count'],SCRIPTS[script]);self.assertEqual(report['mismatches'],[])
                self.assertEqual(self.executions(script),2*SCRIPTS[script])
                staged=Path((self.root/('recreated-'+script+'.txt')).read_text())
                self.assertEqual(staged.read_bytes(),b'new staging owner')

    def test_transitive_fixture_capture_metadata_and_candidate_outputs_are_rejected(self):
        for script in SCRIPTS:
            # Check every consumed capture file plus shared fixture/source. The
            # two link forms are additionally exercised for public candidate.
            names=['candidate.so',FIXTURE,'scripts/pump_trade_fixture.py','evidence/upstream/pump.json']
            names += [f'evidence/{name}/capture.json' for name in IMAGES]
            for name in names:
                source=self.root/name
                for kind in (('direct','symlink','hardlink') if name=='candidate.so' else ('direct',)):
                    with self.subTest(script=script,name=name,kind=kind):
                        for path,raw in self.inputs.items():path.write_bytes(raw)
                        dest=source if kind=='direct' else self.root/('alias-'+script+'-'+kind)
                        if kind=='symlink':dest.symlink_to(source)
                        if kind=='hardlink':os.link(source,dest)
                        result=self.invoke(script,output=dest)
                        self.assertNotEqual(result.returncode,0)
                        self.assertIn('report output aliases an input',result.stderr)
                        self.assertEqual(self.executions(script),0)
                        self.assertEqual(source.read_bytes(),self.inputs[source])

    def test_late_candidate_alias_is_rejected_by_every_writer(self):
        self.output(next(iter(SCRIPTS))).parent.mkdir()
        for script,result in self.batched(SCRIPTS,'late-alias'):
            with self.subTest(script=script):
                self.assertNotEqual(result.returncode,0)
                self.assertIn('report output aliases an input',result.stderr)
                self.assertEqual(self.executions(script),2*SCRIPTS[script])
        self.assertEqual((self.root/'candidate.so').read_bytes(),self.inputs[self.root/'candidate.so'])

    def test_late_transitive_fixture_and_capture_aliases_are_rejected(self):
        pairs=(('pump_buy_v2_differential.py','late-fixture-alias',FIXTURE),
               ('pump_legacy_sell_configured_fee_differential.py','late-capture-alias','evidence/original/pump/capture.json'))
        for script,mode,name in pairs:
            with self.subTest(script=script,mode=mode):
                self.output(script).parent.mkdir(exist_ok=True)
                before=(self.root/name).read_bytes()
                result=self.invoke(script,mode)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('report output aliases an input',result.stderr)
                self.assertEqual((self.root/name).read_bytes(),before)
                self.assertEqual(self.executions(script),2*SCRIPTS[script])

    def test_fsync_failure_preserves_plain_and_compressed_receipts(self):
        selected=('pump_buy_v2_differential.py','pump_legacy_buy_differential.py')
        for script in selected:
            out=self.output(script);out.parent.mkdir(exist_ok=True);out.write_bytes(b'previous receipt')
        for script,result in self.batched(selected,'fsync-failure'):
            with self.subTest(script=script):
                self.assertNotEqual(result.returncode,0)
                self.assertIn('injected fsync failure',result.stderr)
                self.assertEqual(self.output(script).read_bytes(),b'previous receipt')
                self.assertEqual(self.executions(script),2*SCRIPTS[script])

    def test_wrong_real_image_keeps_each_full_mismatch_receipt_and_failure_exit(self):
        shutil.copyfile(ROOT/'evidence/original/mayhem/deployed.so',self.root/'candidate.so')
        for script,result in self.batched(SCRIPTS,'normal'):
            with self.subTest(script=script):
                self.assertEqual(result.returncode,1,result.stdout[-2000:]+result.stderr[-2000:])
                self.assertEqual(self.report(script)['case_count'],SCRIPTS[script])
                self.assertTrue(self.report(script)['mismatches'])
                self.assertEqual(self.executions(script),2*SCRIPTS[script])

    def test_original_only_modes_keep_all_cases(self):
        scripts=[name for name in SCRIPTS if 'configured_fee' not in name]
        for script,result in self.batched(scripts,'original-only'):
            with self.subTest(script=script):
                self.assertEqual(result.returncode,0,result.stdout[-2000:]+result.stderr[-2000:])
                self.assertEqual(self.report(script)['case_count'],SCRIPTS[script])
                self.assertIsNone(self.report(script)['candidate_sha256'])
                self.assertEqual(self.executions(script),SCRIPTS[script])

    def test_configured_fee_include_baseline_retains_all_143_cases(self):
        script='pump_legacy_sell_configured_fee_differential.py';result=self.invoke(script,'include-baseline')
        self.assertEqual(result.returncode,0,result.stdout[-2000:]+result.stderr[-2000:])
        self.assertEqual(self.report(script)['case_count'],143)
        self.assertEqual(self.executions(script),286)


if __name__=='__main__':unittest.main()
