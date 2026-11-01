"""Actual retained hotness CLI report writes under a bounded OS failure."""
import argparse, hashlib, json, os, pathlib, subprocess, sys, tempfile
P = pathlib.Path
RUN = 'reconstruction/diagnostics/census-portability/run.py'
LANE = 'reconstruction/pump-main/lanes/callgraph-census/'
SOURCES = [RUN] + ['reconstruction/harness/'+n+'.py' for n in ('score','llvm_tools','original_input','score_admission','win','coords','elf_symbols','instruction_stream')] + [LANE+n+'.py' for n in ('census','callid_audit','dataref_audit','blocksim','hotness')]
INPUTS = ['evidence/original/pump/deployed.so','reconstruction/base/functions.tsv',LANE+'NOTES.md',LANE+'CENSUS.json']
DRIVER = r"""import os,pathlib,resource,runpy,signal,sys
entry,mode,marker,*arguments=sys.argv[1:]
def observe(frame,event,arg):
 if event=='call' and frame.f_code.co_name=='exclusive_report' and frame.f_code.co_filename==entry:
  sys.setprofile(None)
  path=pathlib.Path(frame.f_locals['path'])
  pathlib.Path(marker).write_text('real report write reached')
  if mode=='limited':
   resource.setrlimit(resource.RLIMIT_CORE,(0,0));signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
   resource.setrlimit(resource.RLIMIT_FSIZE,(64,64))
  elif mode=='late':path.write_bytes(b'late retained report\n')
sys.setprofile(observe)
sys.argv=[entry,*arguments]
runpy.run_path(entry,run_name='__main__')
"""
def sha(data):return hashlib.sha256(data).hexdigest()
def run(repo,revision=None):
 sources={n:subprocess.check_output(['git','-C',str(repo),'show',revision+':'+n]) if revision else (repo/n).read_bytes() for n in SOURCES}
 inputs={n:(repo/n).read_bytes() for n in INPUTS}
 result={'source_sha256':{n:sha(b) for n,b in sources.items()},'input_sha256':{n:sha(b) for n,b in inputs.items()},'cases':{}}
 with tempfile.TemporaryDirectory(prefix='census-output-proof-') as temporary:
  root=P(temporary).resolve();cohort=root/'repo'
  for name,data in {**sources,**inputs}.items():
   path=cohort/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  entry=cohort/RUN
  def cli(name,path,flag,mode='normal'):
   parent=path.parent;parent.mkdir(parents=True,exist_ok=True);marker=root/(name+'.marker')
   arguments=['hotness','--remarks',str(cohort/(LANE+'NOTES.md')),'--census',str(cohort/(LANE+'CENSUS.json')),flag,str(path)]
   completed=subprocess.run([sys.executable,'-I','-B','-X','utf8','-c',DRIVER,str(entry),mode,str(marker),*arguments],capture_output=True,timeout=90)
   data=path.read_bytes() if path.is_file() else None
   row={'returncode':completed.returncode,'report_write_reached':marker.exists(),'exists':path.exists(),'symlink':path.is_symlink(),'bytes':len(data) if data is not None else None,'sha256':sha(data) if data is not None else None,'file_size_error':b'File too large' in completed.stderr,'staging_leftovers':[x.name for x in parent.iterdir() if x.name.startswith('.')],'stdout_sha256':sha(completed.stdout),'stderr_tail':completed.stderr.decode('utf-8',errors='replace').replace(str(root),'OWNED')[-700:]}
   if data is not None and flag.startswith('--j'):
    try:row['targets']=len(json.loads(data))
    except ValueError:row['targets']=None
   result['cases'][name]=row;return row
  for flag,ext in [('--json','json'),('--md','md')]:
   normal=cli('normal_'+ext,root/'out'/('normal.'+ext),flag);assert normal['returncode']==0,normal
   path=root/'out'/('limited.'+ext)
   cli('limited_'+ext,path,flag,'limited');cli('retry_'+ext,path,flag)
   path=root/'out'/('late.'+ext);cli('late_'+ext,path,flag,'late')
   assert path.read_bytes()==b'late retained report\n'
  assert all((cohort/n).read_bytes()==b for n,b in {**sources,**inputs}.items())
  result['inputs_preserved']=True
 return result
def validate(result,expect):
 fixed=expect=='fixed'
 for ext in ('json','md'):
  normal,limited,retry,late=[result['cases'][name+'_'+ext] for name in ('normal','limited','retry','late')]
  assert normal['returncode']==0 and normal['report_write_reached']
  assert limited['returncode']==1 and limited['file_size_error'] and limited['report_write_reached']
  assert limited['exists']==(not fixed)
  assert retry['returncode']==(0 if fixed else 2)
  assert retry['sha256']==(normal['sha256'] if fixed else limited['sha256'])
  assert late['returncode']==2 and late['sha256']==sha(b'late retained report\n')
  if not fixed:assert limited['bytes']==64
 assert result['cases']['normal_json']['targets']==16
 assert all(not row['staging_leftovers'] for row in result['cases'].values())
 assert result['inputs_preserved']

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=P,required=True);p.add_argument('--revision');p.add_argument('--expect',choices=('base','fixed'),required=True);p.add_argument('--output',type=P,required=True);a=p.parse_args();r=run(a.repo.resolve(),a.revision);validate(r,a.expect);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({n:{k:v for k,v in row.items() if k!='stderr_tail'} for n,row in r['cases'].items()},indent=2))
