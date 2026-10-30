#!/usr/bin/env python3
"""Original/candidate SBF buyback configuration behavior, entirely in LiteSVM."""
import argparse,hashlib,json,pathlib,struct
from pump_amm_admin_differential import Harness,ROOT,PROGRAM,EVENT,PAYER,OUTSIDER,CONFIG_KEY,CONFIG,RAW,IDL,Account,AccountMeta,Instruction,Transaction,Pubkey,FailedTransactionMetadata
from pump_differential_output import PumpReport
DISC=bytes(next(x for x in IDL['instructions'] if x['name']=='update_buyback_config')['discriminator'])
class BuybackHarness(Harness):
 def run(self,payload,keys,mutation=None):
  self.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'],bytes(RAW),PROGRAM))
  admin=OUTSIDER if mutation=='outsider' else PAYER
  metas=[AccountMeta(admin.pubkey(),True,False),AccountMeta(CONFIG_KEY,False,mutation!='readonly'),AccountMeta(EVENT,False,False),AccountMeta(PROGRAM,False,False)]
  for key in keys:
   if key not in [Pubkey.default(),PROGRAM,CONFIG_KEY,EVENT,PAYER.pubkey(),OUTSIDER.pubkey()]:self.vm.set_account(key,Account(10**9,b'',Pubkey.default()))
   metas.append(AccountMeta(key,False,False))
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,DISC+payload,metas)],admin.pubkey(),[admin],self.vm.latest_blockhash())
  r=self.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
  return {'error':str(r.err()) if failed else None,'state_hex':bytes(self.vm.get_account(CONFIG_KEY).data).hex(),'events':[x for x in meta.logs() if x.startswith('Program data: ')]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 output=PumpReport(a.output,ROOT,a.candidate,__file__)
 original=ROOT/'evidence/original/pump_amm/deployed.so';left,right=BuybackHarness(original),BuybackHarness(a.candidate)
 keys=[Pubkey.from_bytes(bytes([i+30])*32) for i in range(10)]
 key_sets=[keys[:n] for n in range(11)]+[list(reversed(keys[:8]))]
 for i in range(8):
  changed=keys[:8];changed[i]=Pubkey.default();key_sets.append(changed)
  for j in range(i):changed=keys[:8];changed[i]=changed[j];key_sets.append(changed)
 key_sets.extend([[Pubkey.default()]*8,[PROGRAM,CONFIG_KEY,EVENT,PAYER.pubkey(),OUTSIDER.pubkey(),*keys[:3]]])
 rows=[]
 def test(payload,ks,mutation=None):
  x,y=left.run(payload,ks,mutation),right.run(payload,ks,mutation)
  rows.append({'payload_hex':payload.hex(),'recipients':[str(k) for k in ks],'mutation':mutation,'original':x,'candidate':y,'match':x==y})
 for bps in [None,0,1,9999,10000,10001,2**64-1]:
  payload=b'\0' if bps is None else b'\1'+struct.pack('<Q',bps)
  for ks in key_sets:test(payload,ks)
  for mutation in ['outsider','readonly']:test(payload,keys[:8],mutation)
 for payload in [b'',b'\2',b'\0ignored',b'\1'+bytes(7),b'\1'+bytes(8)+b'ignored']:test(payload,keys[:8])
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 failures=[i for i,x in enumerate(rows) if not x['match']]
 report={'scope':'SBF buyback-config handler differential only; not whole-program equivalence.','original_sha256':left.sha256,'candidate_sha256':right.sha256,'script_sha256':sha(pathlib.Path(__file__)),'case_count':len(rows),'mismatches':failures,'cases':rows}
 output.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'))
 print(json.dumps({'case_count':len(rows),'mismatches':failures[:20],'mismatch_count':len(failures)}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
