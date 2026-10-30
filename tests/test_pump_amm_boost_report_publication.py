"""One full boost CLI corpus plus bounded real-VM report publication controls.

Bounded controls copy the production script and add only a two-row return
inside main's local case dispatcher. The publication path and the executed
cases stay unchanged; the full test executes the unmodified script.
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

ROOT=Path(__file__).resolve().parents[1]
FILES=('scripts/pump_amm_boost_differential.py','scripts/pump_amm_create_differential.py',
       'scripts/pump_amm_liquidity_differential.py','scripts/pump_amm_admin_differential.py',
       'scripts/pump_amm_reusable_harness.py','scripts/pump_differential_output.py',
       'evidence/original/pump_amm/deployed.so','evidence/original/pump/deployed.so',
       'evidence/upstream/pump_amm.json','evidence/upstream/pump.json',
       'evidence/dependencies/spl_token/deployed.so','evidence/dependencies/spl_token_2022/deployed.so',
       'evidence/dependencies/associated_token/deployed.so',
       'research/imported-lab/analysis/pump_fun/config-snapshot.json',
       'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',
       'research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json')
DRIVER=r'''
import ast, json, os, runpy, sys
from pathlib import Path
root,mode,output=sys.argv[1:];root=Path(root);output=Path(output)
script=root/'scripts/pump_amm_boost_differential.py'
if mode!='full':
    tree=ast.parse(script.read_text())
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    dispatch=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='test')
    dispatch.body.insert(0,ast.parse('if len(rows)>=2: return').body[0])
    script.write_text(ast.unparse(tree)+'\n',encoding='utf-8')
sys.path.insert(0,str(root/'scripts'))
import pump_differential_output as publication
if mode=='fsync-failure':
    def fail(fd):raise OSError('injected fsync failure')
    publication.os.fsync=fail
elif mode in ('replace','recreate'):
    replace=publication.os.replace
    def publish(stage,destination):
        if json.loads(Path(stage).read_bytes())['case_count']!=2 or Path(destination).read_bytes()!=b'prior report':
            raise RuntimeError('incomplete report or premature replacement')
        replace(stage,destination)
        if mode=='recreate':
            Path(stage).write_bytes(b'new staging owner');(root/'recreated.txt').write_text(str(stage))
    publication.os.replace=publish
calls=[]
def hook(frame,event,arg):
    if event=='return' and frame.f_code.co_filename==str(script) and frame.f_code.co_name in ('boost','run_migration'):
        calls.append(frame.f_code.co_name)
        if len(calls)==2:
            if mode=='late-alias':os.link(root/'candidate.so',output)
            if mode=='image-swap':
                (root/'candidate.so').write_bytes(b'replaced candidate')
                (root/'evidence/original/pump_amm/deployed.so').write_bytes(b'replaced original')
sys.argv=[str(script),'--candidate',str(root/'candidate.so'),'--output',str(output)]
sys.setprofile(hook)
try:runpy.run_path(str(script),run_name='__main__')
finally:
    sys.setprofile(None);(root/'executions.json').write_text(json.dumps(calls))
'''


class BoostReportPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='amm-boost-publication-');self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve()
        for name in FILES:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
        shutil.copyfile(self.root/FILES[6],self.root/'candidate.so')
        self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.output=self.root/'reports/output.json'

    def invoke(self,mode='normal',output=None):
        env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),mode,str(output or self.output)],cwd=self.root,env=env,capture_output=True,text=True,timeout=120)

    def executions(self):return json.loads((self.root/'executions.json').read_bytes())

    def unchanged_inputs(self):
        for p,b in self.inputs.items():
            if p!=self.root/FILES[0]:self.assertEqual(p.read_bytes(),b,str(p))

    def test_full_unmodified_cli_publishes_100_pairs(self):
        result=self.invoke('full');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes());self.assertEqual(report['case_count'],100)
        self.assertEqual(len(self.executions()),200);self.assertIn('run_migration',self.executions())
        self.assertEqual(report['mismatches'],[])
        self.assertTrue(any(row['original']['error'] is None for row in report['cases']))
        self.assertTrue(any(row['original']['error'] is not None for row in report['cases']))
        expected=hashlib.sha256(self.inputs[self.root/'candidate.so']).hexdigest()
        self.assertEqual(report['candidate_sha256'],expected);self.assertEqual(report['original_sha256'],expected)
        self.assertEqual((self.root/FILES[0]).read_bytes(),self.inputs[self.root/FILES[0]])
        self.unchanged_inputs()

    def test_all_input_aliases_reject_before_vm(self):
        for name in ('candidate.so',*FILES):
            source=self.root/name
            for kind in ('direct','symlink','hardlink'):
                with self.subTest(name=name,kind=kind):
                    for p,b in self.inputs.items():p.write_bytes(b)
                    output=source if kind=='direct' else self.root/(source.name+'-'+kind)
                    if kind=='symlink':output.symlink_to(source)
                    if kind=='hardlink':os.link(source,output)
                    result=self.invoke(output=output)
                    self.assertNotEqual(result.returncode,0);self.assertIn('report output aliases an input',result.stderr)
                    self.assertEqual(self.executions(),[]);self.unchanged_inputs()
                    if kind!='direct':output.unlink()

    def test_late_alias_preserves_candidate(self):
        self.output.parent.mkdir();before=(self.root/'candidate.so').read_bytes()
        result=self.invoke('late-alias');self.assertNotEqual(result.returncode,0)
        self.assertIn('report output aliases an input',result.stderr)
        self.assertEqual((self.root/'candidate.so').read_bytes(),before);self.assertEqual(len(self.executions()),4)

    def test_fsync_failure_preserves_prior_report(self):
        self.output.parent.mkdir();self.output.write_bytes(b'prior report')
        result=self.invoke('fsync-failure');self.assertNotEqual(result.returncode,0)
        self.assertIn('injected fsync failure',result.stderr)
        self.assertEqual(self.output.read_bytes(),b'prior report');self.assertEqual(list(self.output.parent.iterdir()),[self.output])
        self.assertEqual(len(self.executions()),4);self.unchanged_inputs()

    def test_atomic_replacement_and_recreated_stage(self):
        for mode in ('replace','recreate'):
            with self.subTest(mode=mode):
                (self.root/FILES[0]).write_bytes(self.inputs[self.root/FILES[0]])
                self.output.parent.mkdir(exist_ok=True);self.output.write_bytes(b'prior report')
                result=self.invoke(mode);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertEqual(json.loads(self.output.read_bytes())['case_count'],2);self.assertEqual(len(self.executions()),4)
                if mode=='recreate':self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'new staging owner')
                self.unchanged_inputs()

    def test_public_image_replacement_keeps_pinned_bytes(self):
        expected=hashlib.sha256((self.root/'candidate.so').read_bytes()).hexdigest()
        result=self.invoke('image-swap');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes());self.assertEqual(report['case_count'],2)
        self.assertEqual(report['mismatches'],[]);self.assertEqual(report['candidate_sha256'],expected)
        self.assertEqual(report['original_sha256'],expected);self.assertEqual(len(self.executions()),4)
        self.assertEqual((self.root/'candidate.so').read_bytes(),b'replaced candidate')

    def test_wrong_image_retains_failed_comparison(self):
        shutil.copyfile(ROOT/'evidence/original/mayhem/deployed.so',self.root/'candidate.so')
        result=self.invoke();self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        report=json.loads(self.output.read_bytes());self.assertEqual(report['case_count'],2)
        self.assertTrue(report['mismatches']);self.assertEqual(len(self.executions()),4)


if __name__=='__main__':unittest.main()
