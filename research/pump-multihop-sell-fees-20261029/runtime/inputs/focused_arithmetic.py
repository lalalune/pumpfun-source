"""Two explicitly synthetic fee-cap variants of the retained multi-hop fixture."""
from pathlib import Path
import argparse,base64,gzip,hashlib,importlib.util,json,struct,sys,re
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('retained_focused',Path(__file__).parent/'focused.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
f=m.f
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--proposal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
images={'original':m.ROOT/'evidence/original/pump/deployed.so','parent':a.parent.resolve(),'proposal':a.proposal.resolve()}
cases=[dict(name='token2022_full_fee_small_buy',sell=False,extension='valid',bps=10000,correct_quote_address=True,token2022_flow=True,amount=3),dict(name='token2022_full_fee_ordinary_buy',sell=False,extension='valid',bps=10000,correct_quote_address=True,token2022_flow=True,amount=1000)]
rows=[];units=re.compile(r'^Program [1-9A-HJ-NP-Za-km-z]+ consumed [0-9]+ of [0-9]+ compute units$')
for c in cases:
 m.CASE.clear();m.CASE.update(c);f.VA=f.Pubkey.find_program_address([bytes(f.C_A),bytes(f.TOKEN22),bytes(f.A)],f.ATA)[0];f.VQA=m.OLD_VQA;f.VQB=f.Pubkey.find_program_address([bytes(f.C_B),bytes(f.TOKEN22),bytes(f.A)],f.ATA)[0];runs={};raw={}
 for name,path in images.items():
  m.SENDS.clear();m.loader.LOADS.clear();runs[name]=f.invoke(False,c['amount'],'exotic',1,path);assert len(m.SENDS)==1;raw[name]=m.SENDS[0]
 fields=['error','events','inner','return_data','before','after','transaction_base64','pump_calls','token_calls'];compare=lambda name:[k for k in fields if runs['original'][k]!=runs[name][k]];logs=lambda name:[l for l in runs[name]['logs']if not units.fullmatch(l)]
 row=dict(case=c,runs=runs,observations=raw,proposal_differences=compare('proposal'),parent_differences=compare('parent'),proposal_log_equal=logs('original')==logs('proposal'),parent_log_equal=logs('original')==logs('parent'));rows.append(row);print(json.dumps(dict(case=c['name'],errors={k:v['error']for k,v in runs.items()},proposal_differences=row['proposal_differences'],parent_differences=row['parent_differences'],proposal_log_equal=row['proposal_log_equal'],parent_log_equal=row['parent_log_equal'],diagnostics={k:[l for l in v['logs'] if 'Error' in l or 'failed' in l]for k,v in runs.items()})),flush=True)
a.output.write_bytes(gzip.compress(json.dumps(dict(scope=__doc__,images_sha256={k:hashlib.sha256(v.read_bytes()).hexdigest()for k,v in images.items()},producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(m.H.read_bytes()).hexdigest(),cases=rows),separators=(',',':')).encode(),mtime=0));assert all(not r['proposal_differences']and r['proposal_log_equal']for r in rows),'Candidate mismatch; raw outputs retained'
