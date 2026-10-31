"""Shared real-CLI controls; bounded runs select two real cases, never mock VM results."""
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
import ast,importlib,json,os,sys
from pathlib import Path
root,name,mode,output,options=sys.argv[1:];root=Path(root);output=Path(output);options=json.loads(options)
sys.path.insert(0,str(root/'scripts'))
module=importlib.import_module(name)
import pump_differential_output as publisher
selected=0
if hasattr(module,'cases'):
 original_cases=module.cases
 def cases(*args,**kwargs):
  global selected
  rows=original_cases(*args,**kwargs)
  rows=rows if mode=='full' else ([rows[0],next(r for r in rows if r.get('name')==options['keep_case'])] if options.get('keep_case') else rows[:2])
  selected=len(rows);return rows
 module.cases=cases
else:
 script=Path(module.__file__)
 scope=next(n for n in ast.parse(script.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
 line=min(n.lineno for n in scope.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('sha','report') for t in n.targets))
 jumped=False
 def hook(frame,event,arg):
  global selected,jumped
  if frame.f_code.co_filename!=str(script):return hook
  if event=='return' and frame.f_code.co_name=='test':selected+=1
  if mode!='full' and event=='line' and selected==2 and not jumped and frame.f_code.co_name=='main' and frame.f_lineno<line:
   frame.f_lineno=line;jumped=True
  return hook
 sys.settrace(hook)
original_fsync=publisher.os.fsync
original_replace=publisher.os.replace
if mode=='failure':
 def fail(fd):raise OSError('controlled fsync failure')
 publisher.os.fsync=fail
elif mode=='late':
 def collide(fd):
  original_fsync(fd);os.link(root/options['late_input'],output)
 publisher.os.fsync=collide
elif mode in ('replace','recreate'):
 def replace(stage,destination):
  if destination.read_bytes()!=b'prior receipt':raise RuntimeError('prior output lost before commit')
  original_replace(stage,destination)
  if mode=='recreate':
   Path(stage).write_bytes(b'later staging owner');(root/'recreated.txt').write_text(str(stage))
 publisher.os.replace=replace
sys.argv=[str(root/'scripts'/(name+'.py')),'--output',str(output),*options.get('args',[])]
if mode!='original':sys.argv+=['--candidate',str(root/'candidate.so')]
try:module.main()
finally:
 sys.settrace(None)
 (root/'execution.json').write_text(json.dumps({'selected':selected}))
'''

class PublicationCase:
 NAMES=()
 DATA=()
 HELPERS=()
 PROGRAM=''
 EXPECTED={}
 ARGS={}
 LATE_INPUT=''
 PROOF_ENV='PUMP_PUBLICATION_PROOF_OUT'
 CANDIDATE_REQUIRED=False

 def setUp(self):
  temporary=tempfile.TemporaryDirectory(prefix='real-publication-');self.addCleanup(temporary.cleanup)
  self.root=Path(temporary.name).resolve();(self.root/'scripts').mkdir()
  for path in (ROOT/'scripts').glob('*.py'):shutil.copyfile(path,self.root/'scripts'/path.name)
  for relative in self.DATA:
   target=self.root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)
  shutil.copyfile(self.root/self.PROGRAM,self.root/'candidate.so')
  self.inputs={path:path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
  self.output=self.root/'reports/result.json'

 def invoke(self,name,mode='bounded',output=None,cwd=None):
  env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
  options={'keep_case':getattr(self,'KEEP_CASE',{}).get(name),'args':self.ARGS.get(name,[]),'late_input':(self.LATE_INPUT.get(name) if isinstance(self.LATE_INPUT,dict) else self.LATE_INPUT) or self.PROGRAM}
  return subprocess.run([sys.executable,'-B','-c',DRIVER,str(self.root),name,mode,str(output or self.output),json.dumps(options)],cwd=cwd or self.root,env=env,text=True,capture_output=True,timeout=300)

 def report(self):
  raw=self.output.read_bytes();return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)

 def test_full_corpora(self):
  for name in self.NAMES:
   with self.subTest(script=name):
    result=self.invoke(name,'full');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    report=self.report();self.assertEqual(report['mismatches'],[])
    self.assertIn('case_count',report);self.assertEqual(report['case_count'],self.EXPECTED[name]);self.assertEqual(len(report['cases']),report['case_count'])
    if os.environ.get(self.PROOF_ENV):
     dest=Path(os.environ[self.PROOF_ENV]);dest.mkdir(parents=True,exist_ok=True)
     shutil.copyfile(self.output,dest/(name+'.json'))

 def test_all_input_aliases(self):
  for name in self.NAMES:
   for relative in (self.PROGRAM,'candidate.so',*getattr(self,'INPUTS',{}).get(name,self.DATA),*('scripts/'+x+'.py' for x in (name,*(self.HELPERS.get(name,()) if isinstance(self.HELPERS,dict) else self.HELPERS),'pump_differential_output'))):
    for kind in ('direct','symlink','hardlink'):
     with self.subTest(script=name,input=relative,kind=kind):
      source=self.root/relative;alias=self.root/'alias-output';alias.unlink(missing_ok=True)
      output=source
      if kind=='symlink':alias.symlink_to(source);output=alias
      elif kind=='hardlink':os.link(source,alias);output=alias
      result=self.invoke(name,output=output)
      self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
      self.assertIn('report output aliases an input',result.stderr)
      self.assertEqual(source.read_bytes(),self.inputs[source])
      self.assertEqual(json.loads((self.root/'execution.json').read_bytes())['selected'],0)

 def test_real_bounded_publication(self):
  for name in self.NAMES:
   for mode in (('bounded','late','failure','replace','recreate') if self.CANDIDATE_REQUIRED else ('bounded','original','late','failure','replace','recreate')):
    with self.subTest(script=name,mode=mode):
     self.output.parent.mkdir(exist_ok=True);self.output.unlink(missing_ok=True)
     if mode in ('failure','replace','recreate'):self.output.write_bytes(b'prior receipt')
     result=self.invoke(name,mode)
     self.assertEqual(json.loads((self.root/'execution.json').read_bytes())['selected'],2)
     if mode=='late':
      self.assertNotEqual(result.returncode,0);self.assertIn('report output aliases an input',result.stderr)
      p=self.root/((self.LATE_INPUT.get(name) if isinstance(self.LATE_INPUT,dict) else self.LATE_INPUT) or self.PROGRAM);self.assertEqual(p.read_bytes(),self.inputs[p])
     elif mode=='failure':
      self.assertNotEqual(result.returncode,0);self.assertIn('controlled fsync failure',result.stderr)
      self.assertEqual(self.output.read_bytes(),b'prior receipt')
     else:
      self.assertEqual(result.returncode,0,result.stdout+result.stderr)
      report=self.report();self.assertEqual(report.get('case_count',len(report['cases'])),2);self.assertEqual(report['mismatches'],[])
      if mode=='original':self.assertTrue(all(r.get('match') is None for r in report['cases']))
      if mode=='recreate':self.assertEqual(Path((self.root/'recreated.txt').read_text()).read_bytes(),b'later staging owner')
