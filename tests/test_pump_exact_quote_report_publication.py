"""Real signed exact-quote VM cases and report input/publication controls.

Captured Pump is a control candidate; these tests make no reconstruction claim.
"""
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
FIXTURE='research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'
FILES=['scripts/'+name for name in ('pump_exact_quote_differential.py','pump_trade_fixture.py',
       'pump_amm_reusable_harness.py','pump_differential_output.py')]+[FIXTURE]
FILES += ['evidence/original/'+name+'/'+file for name in ('pump','pump_fees') for file in ('deployed.so','capture.json')]
FILES += ['evidence/dependencies/'+name+'/'+file for name in ('spl_token','spl_token_2022','associated_token') for file in ('deployed.so','capture.json')]
COUNT=352
DRIVER=r'''
import gzip,json,os,runpy,sys
from pathlib import Path
root,mode,output=sys.argv[1:];root=Path(root);output=Path(output)
sys.path.insert(0,str(root/'scripts'))
import pump_differential_output as publication
if mode=='fsync-failure':
 def fail(fd):raise OSError('injected fsync failure')
 publication.os.fsync=fail
elif mode=='late-fixture-alias':
 fsync=publication.os.fsync
 def collide(fd):
  fsync(fd)
  os.link(root/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',output)
 publication.os.fsync=collide
elif mode in ('replace','recreate'):
 replace=publication.os.replace
 def publish(stage,destination):
  raw=Path(stage).read_bytes();report=json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
  if report['case_count']!=352 or Path(destination).read_bytes()!=b'prior receipt':
   raise RuntimeError('incomplete report or prematurely replaced destination')
  replace(stage,destination)
  if mode=='recreate':
   Path(stage).write_bytes(b'new staging owner');(root/'recreated.txt').write_text(str(stage))
 publication.os.replace=publish
script=str(root/'scripts/pump_exact_quote_differential.py');calls=[]
def hook(frame,event,arg):
 if event=='return' and frame.f_code.co_filename==script and frame.f_code.co_name=='run':
  calls.append(1)
  if len(calls)==2:
   if mode=='late-alias':os.link(root/'candidate.so',output)
   elif mode=='image-swap':
    (root/'candidate.so').write_bytes(b'replaced candidate')
    (root/'evidence/original/pump/deployed.so').write_bytes(b'replaced original')
sys.argv=[script,'--output',str(output)]
if mode!='original-only':sys.argv+=['--candidate',str(root/'candidate.so')]
sys.setprofile(hook)
try:runpy.run_path(script,run_name='__main__')
finally:
 sys.setprofile(None)
 (root/'executions.json').write_text(json.dumps(calls))
'''


class ExactQuotePublicationTests(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory(prefix='exact-quote-publication-')
  self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
  for name in FILES:
   path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,path)
  shutil.copyfile(self.root/'evidence/original/pump/deployed.so',self.root/'candidate.so')
  self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  self.output=self.root/'reports/output.json.gz'

 def invoke(self,mode='normal',output=None):
  env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
  return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),mode,str(output or self.output)],
    cwd=self.root,env=env,capture_output=True,text=True,timeout=180)

 def report(self,path=None):
  raw=(path or self.output).read_bytes()
  return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)

 def executions(self):return len(json.loads((self.root/'executions.json').read_bytes()))

 def check_report(self,report,candidate=True):
  self.assertEqual(report['case_count'],COUNT);self.assertEqual(len(report['cases']),COUNT)
  for row in report['cases']:
   self.assertTrue(row['original']['signature_verified'])
   if candidate:self.assertTrue(row['candidate']['signature_verified'])

 def test_complete_plain_and_gzip_reports_keep_all_signed_pairs(self):
  reports=[]
  for name in ('report.json','report.json.gz'):
   output=self.output.with_name(name);result=self.invoke(output=output)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   report=self.report(output);self.check_report(report)
   self.assertEqual(report['mismatches'],[]);self.assertEqual(self.executions(),COUNT*2)
   reports.append(report)
  self.assertEqual(reports[0],reports[1])

 def test_all_consumed_input_aliases_are_rejected_before_cases(self):
  for index,name in enumerate(['candidate.so',*FILES]):
   source=self.root/name
   for kind in ('direct','symlink','hardlink'):
    with self.subTest(name=name,kind=kind):
     output=source if kind=='direct' else self.root/(str(index)+'-'+kind)
     if kind=='symlink':output.symlink_to(source)
     if kind=='hardlink':os.link(source,output)
     result=self.invoke(output=output)
     self.assertNotEqual(result.returncode,0)
     self.assertIn('report output aliases an input',result.stderr)
     self.assertEqual(self.executions(),0)
     self.assertEqual(source.read_bytes(),self.inputs[source])

 def test_late_candidate_and_fixture_aliases_preserve_inputs(self):
  self.output.parent.mkdir()
  for mode,name in (('late-alias','candidate.so'),('late-fixture-alias',FIXTURE)):
   with self.subTest(mode=mode):
    self.output.unlink(missing_ok=True)
    result=self.invoke(mode)
    self.assertNotEqual(result.returncode,0)
    self.assertIn('report output aliases an input',result.stderr)
    self.assertEqual((self.root/name).read_bytes(),self.inputs[self.root/name])
    self.assertEqual(self.executions(),COUNT*2)

 def test_fsync_failure_preserves_previous_receipt(self):
  self.output.parent.mkdir();self.output.write_bytes(b'prior receipt')
  result=self.invoke('fsync-failure')
  self.assertNotEqual(result.returncode,0);self.assertIn('injected fsync failure',result.stderr)
  self.assertEqual(self.output.read_bytes(),b'prior receipt')
  self.assertEqual(list(self.output.parent.iterdir()),[self.output]);self.assertEqual(self.executions(),COUNT*2)

 def test_atomic_replacement_and_recreated_staging_ownership(self):
  for mode in ('replace','recreate'):
   with self.subTest(mode=mode):
    self.output.parent.mkdir(exist_ok=True);self.output.write_bytes(b'prior receipt')
    result=self.invoke(mode);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    self.check_report(self.report());self.assertEqual(self.executions(),COUNT*2)
    if mode=='recreate':self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'new staging owner')

 def test_public_image_replacement_keeps_pinned_hashes(self):
  expected=hashlib.sha256((self.root/'candidate.so').read_bytes()).hexdigest()
  result=self.invoke('image-swap');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  report=self.report();self.check_report(report)
  self.assertEqual(report['candidate_sha256'],expected);self.assertEqual(report['original_sha256'],expected)
  self.assertEqual(report['mismatches'],[]);self.assertEqual(self.executions(),COUNT*2)

 def test_original_only_keeps_null_comparison(self):
  result=self.invoke('original-only');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  report=self.report();self.check_report(report,False)
  self.assertIsNone(report['candidate_sha256']);self.assertEqual(report['mismatches'],[])
  self.assertTrue(all(row['candidate'] is None and row['match'] is None for row in report['cases']))
  self.assertEqual(self.executions(),COUNT)

 def test_wrong_real_image_keeps_failure_receipt_and_exit(self):
  shutil.copyfile(self.root/'evidence/original/pump_fees/deployed.so',self.root/'candidate.so')
  result=self.invoke();self.assertEqual(result.returncode,1,result.stdout+result.stderr)
  report=self.report();self.check_report(report)
  self.assertTrue(report['mismatches']);self.assertEqual(self.executions(),COUNT*2)


if __name__=='__main__':unittest.main()
