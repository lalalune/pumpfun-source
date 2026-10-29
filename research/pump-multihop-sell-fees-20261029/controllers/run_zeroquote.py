from pathlib import Path
import hashlib,json,subprocess,sys,time,os
import solders,solders.solders
R=Path('/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-source');B=Path('/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-contribution-review/pump-multihop-sell-fees-20261029');I=B/'runtime-inputs';L=Path('/home/ahi200/pumpfun-work/20261029-pump-legacy-exact-sol');P=L/'multihop-tokens-quote/candidate.so';C=L/'multihop-sell-sub3/candidate.so';out=L/'multihop-sell-sub3/zeroquote-runtime-verified';assert not out.exists();out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[Path(__file__),P,C,B/'probe-inputs.json',B/'source.patch',L/'multihop-tokens-quote/launch.json',L/'multihop-tokens-quote/result.json',L/'multihop-sell-sub3/launch.json',L/'multihop-sell-sub3/result.json',R/'scripts/pump_captured_loader.py',R/'evidence/upstream/pump_amm.json',R/'evidence/original/pump/program-account.bin',R/'evidence/original/pump/programdata-account.bin',Path(sys.executable).resolve(),Path(solders.solders.__file__).resolve()]
inputs += [p for p in I.rglob('*')if p.is_file()];inputs += [B/'zeroquote-inputs/focused_zero_quote.py']
for family,names in [('original',['pump','pump_amm','pump_fees']),('dependencies',['spl_token','spl_token_2022','associated_token'])]:
 for name in names:
  for file in ['deployed.so','capture.json']:inputs.append(R/'evidence'/family/name/file)
inputs=list(dict.fromkeys(inputs));initial={str(p):dict(sha256=sha(p),bytes=p.stat().st_size)for p in inputs};commands=[('zeroquote',[sys.executable,str(B/'zeroquote-inputs/focused_zero_quote.py'),'--parent',str(P),'--proposal',str(C),'--output',str(out/'zeroquote-one.json.gz')])];record=dict(scope='One signed original/published1164/sell-sub3-candidate triple with documented maximum fee mutation',python=sys.version,python_executable=sys.executable,environment={k:os.environ.get(k)for k in ['PYTHONPATH','PYTHONSAFEPATH']},inputs=initial,commands=[dict(name=n,argv=c,cwd=str(R))for n,c in commands],results=[])
def save():(out/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
save()
for name,cmd in commands:
 start=time.time()
 with(out/(name+'.stdout.log')).open('wb')as stdout,(out/(name+'.stderr.log')).open('wb')as stderr:r=subprocess.run(cmd,cwd=R,stdout=stdout,stderr=stderr)
 record['results'].append(dict(name=name,returncode=r.returncode,elapsed_seconds=round(time.time()-start,3),stdout_sha256=sha(out/(name+'.stdout.log')),stderr_sha256=sha(out/(name+'.stderr.log'))));save();print(json.dumps(record['results'][-1]),flush=True)
 if r.returncode:sys.exit(r.returncode)
record['inputs_unchanged']={str(p):sha(p)==initial[str(p)]['sha256']for p in inputs};record['output_files']={p.name:dict(sha256=sha(p),bytes=p.stat().st_size)for p in out.iterdir()if p.is_file()and p.name!='execution.json'};save();assert all(record['inputs_unchanged'].values());print(str(out),flush=True)
