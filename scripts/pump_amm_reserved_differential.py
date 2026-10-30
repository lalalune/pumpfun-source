#!/usr/bin/env python3
"""Original/rebuilt reserved-recipient administration; local SBF only."""
import argparse,hashlib,json,pathlib
from pump_amm_admin_differential import *
DISC=bytes(next(x for x in IDL['instructions'] if x['name']=='set_reserved_fee_recipients')['discriminator'])
class ReservedHarness(Harness):
 def run(self,payload,keys,mutation=None):
  config_key=CONFIG_KEY if mutation!='noncanonical' else Pubkey.from_bytes(bytes([89])*32)
  self.vm.set_account(config_key,Account(CONFIG['lamports'],bytes(RAW),PROGRAM))
  admin=OUTSIDER if mutation=='outsider' else PAYER
  payer=OUTSIDER if mutation=='unsigned' else admin
  event=EVENT if mutation!='event' else OUTSIDER.pubkey()
  metas=[AccountMeta(config_key,False,mutation!='readonly'),AccountMeta(admin.pubkey(),mutation!='unsigned',False),AccountMeta(event,False,False),AccountMeta(PROGRAM,False,False)]
  for key in keys:
   if key not in [Pubkey.default(),PROGRAM,CONFIG_KEY,EVENT,PAYER.pubkey(),OUTSIDER.pubkey()]:self.vm.set_account(key,Account(10**9,b'',Pubkey.default()))
   metas.append(AccountMeta(key,False,False))
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,DISC+payload,metas)],payer.pubkey(),[payer],self.vm.latest_blockhash());r=self.vm.send_transaction(tx)
  failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
  return {'error':str(r.err()) if failed else None,'state_hex':bytes(self.vm.get_account(config_key).data).hex(),'events':[x for x in meta.logs() if x.startswith('Program data: ')]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 original=ROOT/'evidence/original/pump_amm/deployed.so';left,right=ReservedHarness(original),ReservedHarness(a.candidate)
 keys=[Pubkey.from_bytes(bytes([i+30])*32) for i in range(10)];sets=[keys[:n] for n in range(11)]+[list(reversed(keys[:8])),[Pubkey.default()]*8]
 for i in range(8):
  ks=keys[:8];ks[i]=Pubkey.default();sets.append(ks)
  for j in range(i):ks=keys[:8];ks[i]=ks[j];sets.append(ks)
 rows=[]
 def test(payload,ks,mutation=None):
  x,y=left.run(payload,ks,mutation),right.run(payload,ks,mutation)
  rows.append({'payload_hex':payload.hex(),'recipients':[str(k) for k in ks],'mutation':mutation,'original':x,'candidate':y,'match':x==y})
 for byte in [0,1,255]:
  for ks in sets:test(bytes([byte])*32,ks)
 for mutation in ['outsider','unsigned','readonly','event','noncanonical']:test(bytes(32),keys[:8],mutation)
 for length in [0,1,8,31,33]:test(bytes(length),keys[:8])
 failures=[i for i,x in enumerate(rows) if not x['match']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report={'scope':'SBF reserved-recipient handler only; not whole program equivalence.','original_sha256':left.sha256,'candidate_sha256':right.sha256,'script_sha256':sha(pathlib.Path(__file__)),'case_count':len(rows),'mismatches':failures,'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'case_count':len(rows),'mismatches':failures[:30],'mismatch_count':len(failures)}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
