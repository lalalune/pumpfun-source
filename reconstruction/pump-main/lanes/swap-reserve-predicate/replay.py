#!/usr/bin/env python3
import json,gzip,hashlib,importlib.util,inspect,sys,argparse,tempfile
from pathlib import Path
parser=argparse.ArgumentParser(description='Compare the compiled reserve-predicate candidate with the original on 256 synthetic hop cases.');parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
if args.output.exists():parser.error('output already exists')
repo=Path(__file__).resolve().parents[4];p=repo/'tests/test_multi_hop_hop_captured.py';spec=importlib.util.spec_from_file_location('hop_fixtures',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original=m.PUMP_ELF;temporary=tempfile.TemporaryDirectory(prefix='swap-reserve-replay-');candidate=Path(temporary.name)/'candidate.so';candidate.write_bytes(args.candidate.read_bytes());m.DEFAULTS['vault_base_extra']=0
inputs={str(p.relative_to(repo)):p,**{str(path.relative_to(repo)):path for path in m.ELF_SHA256}}
input_hashes={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in inputs.items()}
for path,expected in m.ELF_SHA256.items():
 if input_hashes[str(path.relative_to(repo))]!=expected:raise SystemExit('captured input hash mismatch')
source=inspect.getsource(m.run_captured).replace("token_data(MINT, CURVE, item['rtr'])","token_data(MINT, CURVE, item['rtr']+item['vault_base_extra'])")
old="return {'error': str(result.err()) if failed else None, 'curve': bytes(curve.data),"
new="""meta=result.meta() if failed else result
    raw=json.loads(meta.to_json())
    snapshots={}
    for key in set(state)|{meta.pubkey for meta in metas}:
        account=vm.get_account(key)
        if account and account.executable:continue
        snapshots[str(key)]=None if account is None else {'lamports':account.lamports,'owner':str(account.owner),'data':bytes(account.data).hex()}
    return {'accounts':snapshots,'events':[line for line in meta.logs() if line.startswith('Program data:')], 'inner':raw['inner_instructions'],'return_data':raw['return_data'],'error': str(result.err()) if failed else None, 'curve': bytes(curve.data),"""
assert old in source;source=source.replace(old,new);exec(compile(source,str(p),'exec'),m.__dict__)
def canon(x):
 if isinstance(x,dict):return {str(k):canon(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [canon(v) for v in x]
 if isinstance(x,bytes):return x.hex()
 if x is None or isinstance(x,(str,int,float,bool)):return x
 return str(x)
cases=[('inherited',c) for c in m.fixed_cases()+m.random_cases(80)]
for quote in ['sol','spl']:
 for flag in range(4):
  for amount in [999999,1000000,1010000,2000000,100000000,1000000000]:
   for extra in [0,200000000]:
    cases.append(('crossing',m.case(quote=quote,flags=(flag,),amount=amount,vtr=1000000000,vqr=1000000000,rtr=1000000,rqr=1000000000,vault_base_extra=extra)))
rows=[]
for i,(family,c) in enumerate(cases):
 m.PUMP_ELF=original;a=canon(m.run_captured(c,i));m.PUMP_ELF=candidate;b=canon(m.run_captured(c,i));diff=[k for k in a if a[k]!=b[k]];rows.append({'index':i,'family':family,'case':canon(c),'original':a,'candidate':b,'diff':diff})
 if i%50==0:print(i,'cases',flush=True)
if input_hashes!={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in inputs.items()}:raise SystemExit('input changed during replay')
r={'input_sha256':input_hashes,'scope':'Synthetic single-hop SOL/SPL cases, including reserve crossings. Compares errors, non-executable account snapshots, events, inner calls and return data. Signature checking is disabled for the AMM PDA fixture. This is not general runtime identity or a two-hop test.','fixture_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'extension_sha256':hashlib.sha256(source.encode()).hexdigest(),'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'count':len(rows),'mismatches':[x['index'] for x in rows if x['diff']],'crossing_successes':sum(x['family']=='crossing' and x['original']['error'] is None for x in rows),'crossing_successes_with_events':sum(x['family']=='crossing' and x['original']['error'] is None and len(x['original']['events'])>=3 for x in rows),'cases':rows}
args.output.parent.mkdir(parents=True,exist_ok=True)
with args.output.open('xb') as stream:stream.write(gzip.compress(json.dumps(r).encode(),mtime=0))
print({k:v for k,v in r.items() if k not in ('cases','input_sha256')},flush=True)
temporary.cleanup()
raise SystemExit(bool(r['mismatches']))
