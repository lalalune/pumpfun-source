#!/usr/bin/env python3
"""Verify two deprecated dispatches reject all tested account/payload shapes."""
from fees_admin_differential import *
from pump_differential_output import PumpReport
import random
class DeprecatedFixture(Fixture):
 def run(self,c):
  keys=[Pubkey.from_bytes(bytes([i+80])*32) for i in range(c['count'])]
  for k in keys:self.vm.set_account(k,Account(10**9,bytes(range(128)),PROGRAM))
  disc=bytes(next(i['discriminator'] for i in IDL['instructions'] if i['name']==c['instruction']))
  payload=disc+bytes.fromhex(c['arg']);metas=[AccountMeta(k,False,True) for k in keys]
  before=self.vm.get_account(PAYER.pubkey()).lamports
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[PAYER],self.vm.latest_blockhash());result=self.vm.send_transaction(tx);failed=isinstance(result,FailedTransactionMetadata);meta=result.meta() if failed else result
  return {'error':str(result.err()) if failed else None,'accounts':[(self.vm.get_account(k).data.hex(),self.vm.get_account(k).lamports,str(self.vm.get_account(k).owner)) for k in keys],'payer_delta':self.vm.get_account(PAYER.pubkey()).lamports-before,'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner_instructions':json.loads(meta.to_json())['inner_instructions']}
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__);orig=ROOT/'evidence/original/pump_fees/deployed.so';o=DeprecatedFixture(orig);b=DeprecatedFixture(a.candidate);rows=[];mismatches=[];rng=random.Random(446)
 for name in ['revoke_fee_sharing_authority','transfer_fee_sharing_authority']:
  for length in [0,1,2,4,8,16,32,64,128,256]:
   for count in [0,1,4,8]:
    c={'instruction':name,'count':count,'arg':rng.randbytes(length).hex()};x=o.run(c);y=b.run(c);match=x==y;rows.append({'case':c,'original':x,'candidate':y,'match':match})
    if not match:mismatches.append(len(rows)-1)
 r={'scope':'Two deprecated dispatches: tested payload/account shapes reject with6023, no effects. Historical successful implementations are not claimed.','original_sha256':o.program_sha256,'candidate_sha256':b.program_sha256,'case_count':len(rows),'mismatches':mismatches,'cases':rows};publisher.write((json.dumps(r,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'case_count':len(rows),'mismatches':mismatches}))
 if mismatches:raise SystemExit(1)
if __name__=='__main__':main()
