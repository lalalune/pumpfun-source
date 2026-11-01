"""Actual matrix/resume CLIs with contradictory owned saved receipts."""
import argparse,hashlib,json,pathlib,subprocess,sys,tempfile
P=pathlib.Path
RUNNER='reconstruction/harness/experiment_runner.py'
SUPERVISOR='reconstruction/harness/process_supervisor.py'
CODE="from pathlib import Path;import sys;data=Path(sys.argv[1],'value').read_bytes();Path(sys.argv[2],'result').write_bytes(data);print(data.decode().strip());raise SystemExit(int(sys.argv[3]))"
CASES={'clean-pass':0,'clean-fail':1,'pass-on-failure':1,'fail-on-success':0,'boolean-code':0,'float-code':0,'wrong-code':0,'missing-code':0,'error-reason':0,'changed-inputs':0,'missing-inputs':0,'wrong-schema':0,'changed-input-type':0}
def sha(b):return hashlib.sha256(b).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
def mutate(name,row):
 if name=='pass-on-failure':row['status']='pass'
 elif name=='fail-on-success':row['status']='fail'
 elif name=='boolean-code':row['returncode']=False
 elif name=='float-code':row['returncode']=0.0
 elif name=='wrong-code':row['returncode']=2
 elif name=='missing-code':del row['returncode']
 elif name=='error-reason':row['reason']='post-run validation failed: owned changed input'
 elif name=='changed-inputs':row['inputs']['timeout']=301
 elif name=='changed-input-type':row['inputs']['source']['value']['executable']=0
 elif name=='missing-inputs':del row['inputs']
 elif name=='wrong-schema':row['schema']='not-an-experiment-result'
def brief(row):
 return {k:row.get(k) for k in ('status','returncode','reason','reused','schema')}
def run(repo,revision=None):
 raw=subprocess.check_output(['git','-C',str(repo),'show',revision+':'+RUNNER]) if revision else (repo/RUNNER).read_bytes()
 result={'runner_sha256':sha(raw),'cases':{}}
 with tempfile.TemporaryDirectory(prefix='experiment-receipt-proof-') as temporary:
  root=P(temporary).resolve();runner=root/'runner.py';runner.write_bytes(raw)
  if b'process_supervisor.py' in raw:
   supervisor_raw=subprocess.check_output(['git','-C',str(repo),'show',revision+':'+SUPERVISOR]) if revision else (repo/SUPERVISOR).read_bytes()
   (root/'process_supervisor.py').write_bytes(supervisor_raw);result['supervisor_sha256']=sha(supervisor_raw)
  source=root/'source';source.mkdir();(source/'value').write_bytes(b'bounded resumable experiment input\n');before_source=inventory(source)
  matrix=root/'matrix.json';out=root/'out';matrix.write_text(json.dumps([{'name':n,'source':str(source),'command':[sys.executable,'-c',CODE,'{source}','{out}',str(code)]} for n,code in CASES.items()]))
  def cli():
   c=subprocess.run([sys.executable,'-I','-B',str(runner),str(matrix),'--out',str(out)],capture_output=True,timeout=60)
   assert c.returncode==0,c.stderr.decode();return json.loads(c.stdout)
  first=cli();warm=cli();old={n:inventory(out/n/row['attempt']) for n,row in first.items()}
  assert all(warm[n]['reused'] and warm[n]['attempt']==first[n]['attempt'] for n in CASES)
  for name in CASES:
   path=out/name/'latest.json';row=json.loads(path.read_bytes());mutate(name,row);path.write_text(json.dumps(row))
  resumed=cli();again=cli()
  for name,code in CASES.items():
   row=resumed[name];identity=row.get('inputs')
   result['cases'][name]={'expected_status':'pass' if code==0 else 'fail','expected_returncode':code,'first':brief(first[name]),'warm':brief(warm[name]),'resumed':brief(row),'same_attempt_reused':row['attempt']==first[name]['attempt'],'current_admission_matches_saved':identity==first[name]['inputs'],'key_binds_saved_inputs':isinstance(identity,dict) and sha(json.dumps(identity,sort_keys=True).encode())==row['key'],'next_resume_reuses_same':again[name]['reused'] and again[name]['attempt']==row['attempt'],'old_attempt_preserved':inventory(out/name/first[name]['attempt'])==old[name],'result_sha256':sha((out/name/row['attempt']/'output/result').read_bytes())}
  result['source_preserved']=inventory(source)==before_source;result['runner_preserved']=runner.read_bytes()==raw;result['actual_matrix_clis']=4
 return result

def validate(result,expect):
 fixed=expect=='fixed'
 for name,row in result['cases'].items():
  good=name.startswith('clean-');r=row['resumed']
  assert row['warm']['reused']
  assert r['reused']==(good or not fixed)
  assert row['same_attempt_reused']==(good or not fixed)
  assert row['old_attempt_preserved'] and row['next_resume_reuses_same']
  if good or fixed:
   assert r['status']==row['expected_status'] and type(r['returncode']) is int and r['returncode']==row['expected_returncode']
   assert r['reason'] is None and r['schema']=='experiment-result-v1'
   assert row['current_admission_matches_saved'] and row['key_binds_saved_inputs']
 assert result['source_preserved'] and result['runner_preserved']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=P,required=True);p.add_argument('--revision');p.add_argument('--expect',choices=('base','fixed'),required=True);p.add_argument('--output',type=P,required=True);a=p.parse_args();r=run(a.repo.resolve(),a.revision);validate(r,a.expect);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'matrix_clis':r['actual_matrix_clis'],'cases':len(r['cases']),'reused':sum(x['resumed']['reused'] for x in r['cases'].values())}))
