"""Real AMM trade report publication controls.

One full run per CLI exercises its unchanged corpus. Failure controls run the
first two real cases and jump to the original report block; no VM result is
mocked, and those receipts are asserted to contain exactly two cases.
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
NAMES=('pump_amm_trade_v2_differential.py','pump_amm_legacy_buy_differential.py',
       'pump_amm_legacy_sell_differential.py','pump_amm_sweep_differential.py','pump_amm_multi_hop_differential.py')
HELPERS=('pump_amm_liquidity_differential.py','pump_amm_admin_differential.py',
         'pump_amm_reusable_harness.py','pump_differential_output.py')
TRADE='research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json'
CURVE='research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'
CONFIG='research/imported-lab/analysis/pump_fun/config-snapshot.json'
DATA=(TRADE,CURVE,CONFIG,'evidence/upstream/pump.json','evidence/upstream/pump_amm.json',
      'evidence/original/pump/deployed.so','evidence/original/pump_amm/deployed.so',
      'evidence/original/pump_fees/deployed.so','evidence/dependencies/spl_token/deployed.so',
      'evidence/dependencies/spl_token_2022/deployed.so','evidence/dependencies/associated_token/deployed.so')
DRIVER=r'''
import ast,json,os,runpy,shutil,sys
from pathlib import Path
root,name,mode,output=sys.argv[1:];root=Path(root);output=Path(output)
script=root/'scripts'/name
sys.path.insert(0,str(root/'scripts'))
import pump_differential_output as publication
if mode=='fsync-failure':
 def fail(fd):raise OSError('controlled fsync failure')
 publication.os.fsync=fail
elif mode=='late-fixture-alias':
 fsync=publication.os.fsync
 def collide(fd):
  fsync(fd);os.link(root/'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',output)
 publication.os.fsync=collide
elif mode in ('replace','recreate'):
 replace=publication.os.replace
 def publish(stage,destination):
  value=json.loads(Path(stage).read_bytes())
  if value['case_count']!=2 or destination.read_bytes()!=b'prior receipt':raise RuntimeError('incomplete publication')
  replace(stage,destination)
  if mode=='recreate':
   stage.write_bytes(b'later staging owner');(root/'recreated.txt').write_text(str(stage))
 publication.os.replace=publish
parsed=ast.parse(script.read_text())
scope=next((n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='main'),None)
if scope is None:scope=next(n for n in parsed.body if isinstance(n,ast.If) and '__main__' in ast.unparse(n.test))
report_line=min(n.lineno for n in scope.body if isinstance(n,ast.Assign) and
                any(isinstance(t,ast.Name) and t.id in ('sha','failures','report') for t in n.targets))
completed=[];jumped=False

def hook(frame,event,arg):
 global jumped
 if frame.f_code.co_filename!=str(script):return hook
 if event=='return' and frame.f_code.co_name=='test':
  completed.append(1)
  if len(completed)==1:
   if mode=='late-alias':os.link(root/'candidate.so',output)
   elif mode=='image-swap':shutil.copyfile(root/'evidence/original/pump_fees/deployed.so',root/'candidate.so')
 if mode!='full' and event=='line' and len(completed)==2 and not jumped and frame.f_code.co_name in ('main','<module>') and frame.f_lineno<report_line:
  frame.f_lineno=report_line;jumped=True
 return hook
sys.argv=[str(script),'--candidate',str(root/'candidate.so'),'--output',str(output)]
if mode=='full':sys.setprofile(hook)
else:sys.settrace(hook)
try:runpy.run_path(str(script),run_name='__main__')
finally:
 sys.settrace(None);sys.setprofile(None)
 (root/'executions.json').write_text(json.dumps({'pairs':len(completed),'jumped':jumped}))
'''


class AmmTradePublicationTests(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory(prefix='amm-trade-publication-')
  self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
  for name in tuple('scripts/'+n for n in (*NAMES,*HELPERS))+DATA:
   path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,path)
  shutil.copyfile(self.root/'evidence/original/pump_amm/deployed.so',self.root/'candidate.so')
  self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  self.output=self.root/'reports/output.json'

 def reset(self):
  for path,raw in self.inputs.items():path.write_bytes(raw)

 def invoke(self,name,mode='normal',output=None):
  env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
  return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),name,mode,str(output or self.output)],
    cwd=self.root,env=env,capture_output=True,text=True,timeout=180)

 def control(self):return json.loads((self.root/'executions.json').read_bytes())
 def report(self):return json.loads(self.output.read_bytes())

 def test_all_five_full_corpora_publish_without_mismatches(self):
  summary={}
  for name in NAMES:
   with self.subTest(script=name):
    result=self.invoke(name,'full');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    report=self.report();control=self.control()
    self.assertEqual(report['mismatches'],[]);self.assertGreater(report['case_count'],2)
    self.assertEqual(report['case_count'],len(report['cases']));self.assertEqual(control['pairs'],report['case_count'])
    self.assertFalse(control['jumped']);self.assertTrue(self.output.read_bytes().endswith(b'\n'))
    summary[name]={'cases':report['case_count'],'mismatches':0,'stdout':result.stdout}
    if os.environ.get('PUMP_TRADE_PROOF_OUT'):
     dest=Path(os.environ['PUMP_TRADE_PROOF_OUT']);dest.mkdir(parents=True,exist_ok=True)
     shutil.copyfile(self.output,dest/(name+'.json'))
  if os.environ.get('PUMP_TRADE_PROOF_OUT'):
   (Path(os.environ['PUMP_TRADE_PROOF_OUT'])/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')

 def test_all_transitive_input_aliases_are_refused_before_cases(self):
  common=('candidate.so',TRADE,CONFIG,'evidence/upstream/pump_amm.json',
          'evidence/original/pump_amm/deployed.so','evidence/dependencies/spl_token/deployed.so',
          'evidence/dependencies/spl_token_2022/deployed.so',
          'scripts/pump_amm_liquidity_differential.py','scripts/pump_amm_admin_differential.py',
          'scripts/pump_amm_reusable_harness.py','scripts/pump_differential_output.py')
  for name in NAMES:
   ancestry=[]
   if 'sweep' not in name:
    ancestry += ['scripts/pump_amm_trade_v2_differential.py','evidence/upstream/pump.json','evidence/original/pump_fees/deployed.so']
   if 'legacy_buy' in name or 'multi_hop' in name:ancestry += ['scripts/pump_amm_legacy_sell_differential.py']
   if any(part in name for part in ('legacy','multi_hop','sweep')):ancestry += ['evidence/dependencies/associated_token/deployed.so']
   if 'multi_hop' in name:ancestry += [CURVE,'evidence/original/pump/deployed.so']
   for index,relative in enumerate(dict.fromkeys((*common,'scripts/'+name,*ancestry))):
    for kind in ('direct','symlink','hardlink'):
     with self.subTest(script=name,input=relative,kind=kind):
      source=self.root/relative;output=source if kind=='direct' else self.root/(name+str(index)+kind)
      if kind=='symlink':output.symlink_to(source)
      if kind=='hardlink':os.link(source,output)
      result=self.invoke(name,output=output)
      self.assertNotEqual(result.returncode,0);self.assertIn('report output aliases an input',result.stderr)
      self.assertEqual(source.read_bytes(),self.inputs[source]);self.assertEqual(self.control()['pairs'],0)

 def test_bounded_real_publication_failure_and_ownership_controls(self):
  for name in NAMES:
   for mode in ('normal','late-alias','late-fixture-alias','fsync-failure','replace','recreate','image-swap','wrong'):
    with self.subTest(script=name,mode=mode):
     self.reset();self.output.parent.mkdir(exist_ok=True);self.output.unlink(missing_ok=True)
     if mode=='wrong':shutil.copyfile(self.root/'evidence/original/pump_fees/deployed.so',self.root/'candidate.so')
     if mode in ('fsync-failure','replace','recreate'):self.output.write_bytes(b'prior receipt')
     result=self.invoke(name,mode)
     self.assertEqual(self.control(),{'pairs':2,'jumped':True})
     if mode in ('late-alias','late-fixture-alias'):
      self.assertNotEqual(result.returncode,0);self.assertIn('report output aliases an input',result.stderr)
      target=self.root/('candidate.so' if mode=='late-alias' else TRADE)
      self.assertEqual(target.read_bytes(),self.inputs[target])
     elif mode=='fsync-failure':
      self.assertNotEqual(result.returncode,0);self.assertIn('controlled fsync failure',result.stderr)
      self.assertEqual(self.output.read_bytes(),b'prior receipt')
     elif mode=='wrong':
      self.assertEqual(result.returncode,1,result.stdout+result.stderr)
      self.assertEqual(self.report()['case_count'],2);self.assertTrue(self.report()['mismatches'])
     else:
      self.assertEqual(result.returncode,0,result.stdout+result.stderr)
      self.assertEqual(self.report()['case_count'],2);self.assertEqual(self.report()['mismatches'],[])
      if mode=='recreate':self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'later staging owner')
      if mode=='image-swap':
       import hashlib
       self.assertEqual(self.report()['candidate_sha256'],hashlib.sha256(self.inputs[self.root/'candidate.so']).hexdigest())


if __name__=='__main__':unittest.main()
