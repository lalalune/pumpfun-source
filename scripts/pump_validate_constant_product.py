#!/usr/bin/env python3
"""Compare native recovered arithmetic with original sell-v3 reserve deltas."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse, hashlib, json, random, struct, subprocess
import pump_trade_fixture as f
from pump_differential_output import PumpReport
from native_host_receipt import run_host

p=argparse.ArgumentParser();p.add_argument('--host',type=f.pathlib.Path,required=True);p.add_argument('--output',type=f.pathlib.Path,required=True);a=p.parse_args()
report_output=PumpReport(a.output,f.R,a.host,__file__,extra_inputs=(f.R/'programs/pump/recovered/constant_product.rs',f.R/'programs/pump/recovered/constant_product_host.rs',*f.REPORT_INPUTS))
initial={key:f.vm.get_account(key) for key in f.msg.account_keys}
user=f.Keypair.from_seed(bytes([231])*32)
curve=f.Pubkey.from_string(f.x['accounts']['curve'])
curve_base=initial[curve]
base,quote=struct.unpack_from('<QQ',curve_base.data,8)
rng=random.Random(773104)
amounts=sorted(set([1,2,10,100,1000,10000,35766,35767,10**6,10**8,500000000,999999999,10**9]+[rng.randrange(1,10**9+1) for _ in range(100)]))
states=[(base,quote)]+[(b,q) for b in [1,100,1000000,base] for q in [1,100,20000]]
rows=[];inputs=[]
for vi,vq in states:
 for amount in amounts if (vi,vq)==(base,quote) else [1,1000,10**6,10**9]:
  for key,account in initial.items():
   if account is not None:f.vm.set_account(key,account)
  data=bytearray(curve_base.data);struct.pack_into('<QQ',data,8,vi,vq)
  f.vm.set_account(curve,f.Account(curve_base.lamports,bytes(data),curve_base.owner))
  ix=f.ixs[-1];trade=f.Instruction(ix.program_id,ix.data[:8]+struct.pack('<QQ',amount,0),ix.accounts)
  tx=f.Transaction.new_signed_with_payer([*f.ixs[:-1],trade],user.pubkey(),[user],f.vm.latest_blockhash())
  r=f.vm.send_transaction(tx)
  if isinstance(r,f.FailedTransactionMetadata):
   rows.append({'amount_in':amount,'reserve_in':vi,'reserve_out':vq,'error':str(r.err()),'logs':r.meta().logs(),'compared':False})
  else:
   out_data=f.vm.get_account(curve).data
   after_in,after_out=struct.unpack_from('<QQ',out_data,8)
   assert after_in==vi+amount
   observed=vq-after_out
   rows.append({'amount_in':amount,'reserve_in':vi,'reserve_out':vq,'observed_quote_out':observed,'compared':True})
   inputs.append(f'{amount},{vi},{vq}')
r,host_sha256=run_host(a.host,input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True)
outputs=r.stdout.splitlines();compared=[row for row in rows if row['compared']]
assert len(outputs)==len(compared)
for row,out in zip(compared,outputs):row['recovered_quote_out']=int(out);row['match']=int(out)==row['observed_quote_out']
failures=[i for i,row in enumerate(rows) if row.get('match') is False]
assert len(compared)>=100, 'too few successful original transactions'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
report={'scope':'Native recovered arithmetic against original sell_v3 reserve deltas with captured Token/Token2022/ATA dependencies. Four admin candidate and full trade reconstruction are separate. Synthetic reserve states do not imply reachable configurations; errors are recorded but not arithmetic comparisons.','source_sha256':sha(f.R/'programs/pump/recovered/constant_product.rs'),'host_source_sha256':sha(f.R/'programs/pump/recovered/constant_product_host.rs'),'host_sha256':host_sha256,'original_sha256':{name:sha(f.R/'evidence/original'/name/'deployed.so') for name in ['pump','pump_fees']},'dependency_sha256':{name:sha(f.R/'evidence/dependencies'/name/'deployed.so') for name in ['spl_token','spl_token_2022','associated_token']},'case_count':len(rows),'successful_comparisons':len(compared),'mismatches':failures,'cases':rows}
report_output.write((json.dumps(report,indent=2)+'\n').encode('utf-8'));print(json.dumps({k:report[k] for k in ['case_count','successful_comparisons','mismatches']}));assert not failures
