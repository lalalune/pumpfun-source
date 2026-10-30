"""Real signed 507-case quote-control report admission/publication checks.

Copied captured Pump is a diagnostic candidate. The adjacent build-comparison
file is a hash-only test fixture; it is not evidence of a source rebuild.
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
FILES=('scripts/pump_quote_control_fresh_differential.py','scripts/pump_diagnostic_audit.py',
       'scripts/pump_differential_output.py','evidence/original/pump/deployed.so',
       'evidence/upstream/pump.json','research/imported-lab/analysis/pump_fun/config-snapshot.json',
       'programs/pump/Cargo.toml','programs/pump/Cargo.lock','programs/pump/src/creator/admin_cto.rs')
DRIVER=r'''
import gzip,json,os,runpy,sys
from pathlib import Path
root,mode,output=sys.argv[1:];root=Path(root);output=Path(output)
sys.path.insert(0,str(root/'scripts'))
import pump_differential_output as publication
if mode=='fsync-failure':
 def fail(fd):raise OSError('injected fsync failure')
 publication.os.fsync=fail
elif mode=='late-source-alias':
 fsync=publication.os.fsync
 def collide(fd):
  fsync(fd);os.link(root/'programs/pump/src/creator/admin_cto.rs',output)
 publication.os.fsync=collide
elif mode in ('replace','recreate'):
 replace=publication.os.replace
 def publish(stage,destination):
  report=json.loads(gzip.decompress(Path(stage).read_bytes()))
  if report['cases']!=507 or Path(destination).read_bytes()!=b'prior receipt':raise RuntimeError('incomplete atomic publication')
  replace(stage,destination)
  if mode=='recreate':
   Path(stage).write_bytes(b'new staging owner');(root/'recreated.txt').write_text(str(stage))
 publication.os.replace=publish
script=str(root/'scripts/pump_quote_control_fresh_differential.py');calls=[]
def hook(frame,event,arg):
 if event=='return' and frame.f_code.co_filename==script and frame.f_code.co_name=='execute':
  calls.append(1)
  if len(calls)==2:
   if mode=='late-alias':os.link(root/'candidate.so',output)
   elif mode=='metadata-mutation':(root/'build-comparison.json').write_bytes(b'changed metadata')
   elif mode=='helper-mutation':(root/'scripts/pump_differential_output.py').write_bytes(b'changed helper')
   elif mode=='image-mutation':(root/'candidate.so').write_bytes((root/'evidence/original/pump/deployed.so').read_bytes()+b'changed')
sys.argv=[script,'--candidate',str(root/'candidate.so'),'--output',str(output)]
sys.setprofile(hook)
try:runpy.run_path(script,run_name='__main__')
finally:
 sys.setprofile(None);(root/'executions.json').write_text(json.dumps(calls))
'''


class QuoteControlOutputPublicationTests(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory(prefix='quote-control-publication-')
  self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
  for name in FILES:
   path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,path)
  shutil.copyfile(self.root/'evidence/original/pump/deployed.so',self.root/'candidate.so')
  self.build=self.root/'build-comparison.json'
  self.write_build_record()
  self.inputs={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  self.output=self.root/'reports/output.json.gz'

 def write_build_record(self):
  self.build.write_text(json.dumps({'test_only':'hash fixture; no source-build claim',
   'comparison':{'candidate_sha256':hashlib.sha256((self.root/'candidate.so').read_bytes()).hexdigest()},
   'source_sha256':{name:hashlib.sha256((self.root/name).read_bytes()).hexdigest() for name in FILES if name.startswith('programs/')}}))

 def invoke(self,mode='normal',output=None):
  env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
  return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),mode,str(output or self.output)],
    cwd=self.root,env=env,capture_output=True,text=True,timeout=180)

 def executions(self):return len(json.loads((self.root/'executions.json').read_bytes()))
 def report(self):return json.loads(gzip.decompress(self.output.read_bytes()))

 def check_complete(self):
  report=self.report();self.assertEqual(report['cases'],507);self.assertEqual(len(report['results']),507)
  self.assertEqual(report['bound_inputs_sha256']['scripts/pump_differential_output.py'],
                   hashlib.sha256((self.root/'scripts/pump_differential_output.py').read_bytes()).hexdigest())
  self.assertEqual(self.executions(),1014)
  for row in report['results']:
   for side in ('original','candidate'):
    self.assertTrue(row[side]['signature_verification'])
    self.assertTrue(all(row[side]['signature_verification']))
    self.assertTrue(row[side]['sigverify_enabled']);self.assertTrue(row[side]['blockhash_check_enabled'])
  return report

 def test_complete_cli_with_build_metadata_and_fallback_sources(self):
  for fallback in (False,True):
   with self.subTest(fallback=fallback):
    if fallback:self.build.unlink()
    result=self.invoke();self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    self.assertEqual(self.check_complete()['mismatches'],0)

 def test_every_consumed_input_alias_fails_before_cases(self):
  for index,name in enumerate(('candidate.so','build-comparison.json',*FILES)):
   source=self.root/name
   for kind in ('direct','symlink','hardlink'):
    with self.subTest(name=name,kind=kind):
     output=source if kind=='direct' else self.root/(str(index)+'-'+kind)
     if kind=='symlink':output.symlink_to(source)
     if kind=='hardlink':os.link(source,output)
     result=self.invoke(output=output)
     self.assertNotEqual(result.returncode,0);self.assertIn('report output aliases an input',result.stderr)
     self.assertEqual(self.executions(),0);self.assertEqual(source.read_bytes(),self.inputs[source])

 def test_absent_report_inside_source_tree_is_rejected(self):
  output=self.root/'programs/pump/src/new-report.json.gz'
  result=self.invoke(output=output)
  self.assertNotEqual(result.returncode,0);self.assertIn('report output aliases an input',result.stderr)
  self.assertFalse(output.exists());self.assertEqual(self.executions(),0)

 def test_late_aliases_preserve_candidate_and_source(self):
  self.output.parent.mkdir()
  for mode,name in (('late-alias','candidate.so'),('late-source-alias','programs/pump/src/creator/admin_cto.rs')):
   with self.subTest(mode=mode):
    self.output.unlink(missing_ok=True)
    result=self.invoke(mode)
    self.assertNotEqual(result.returncode,0);self.assertIn('report output aliases an input',result.stderr)
    self.assertEqual((self.root/name).read_bytes(),self.inputs[self.root/name]);self.assertEqual(self.executions(),1014)

 def test_staging_failure_preserves_prior_receipt(self):
  self.output.parent.mkdir();self.output.write_bytes(b'prior receipt')
  result=self.invoke('fsync-failure')
  self.assertNotEqual(result.returncode,0);self.assertIn('injected fsync failure',result.stderr)
  self.assertEqual(self.output.read_bytes(),b'prior receipt');self.assertEqual(self.executions(),1014)
  self.assertEqual(list(self.output.parent.iterdir()),[self.output])

 def test_atomic_replacement_and_recreated_stage_ownership(self):
  for mode in ('replace','recreate'):
   with self.subTest(mode=mode):
    self.output.parent.mkdir(exist_ok=True);self.output.write_bytes(b'prior receipt')
    result=self.invoke(mode);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    self.assertEqual(self.check_complete()['mismatches'],0)
    if mode=='recreate':self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'new staging owner')

 def test_bound_input_mutation_preserves_prior_receipt(self):
  for mode in ('metadata-mutation','helper-mutation','image-mutation'):
   with self.subTest(mode=mode):
    for path,raw in self.inputs.items():path.write_bytes(raw)
    self.output.parent.mkdir(exist_ok=True);self.output.write_bytes(b'prior receipt')
    result=self.invoke(mode)
    self.assertNotEqual(result.returncode,0);self.assertIn('Inputs changed during run',result.stderr)
    self.assertEqual(self.output.read_bytes(),b'prior receipt');self.assertEqual(self.executions(),1014)

 def test_wrong_real_image_retains_mismatches_and_failure_exit(self):
  shutil.copyfile(ROOT/'evidence/original/pump_fees/deployed.so',self.root/'candidate.so');self.write_build_record()
  result=self.invoke();self.assertEqual(result.returncode,1,result.stdout+result.stderr)
  self.assertGreater(self.check_complete()['mismatches'],0)


if __name__=='__main__':unittest.main()
