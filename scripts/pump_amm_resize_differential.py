#!/usr/bin/env python3
"""Original/rebuilt SBF global-config resize and system-CPI differential."""
import argparse,hashlib,json,pathlib,struct
from pump_amm_admin_differential import *
class ResizeHarness(Harness):
 def run(self,instruction,payload=b'',length=949,lamports=None,new_key=None,mutation=None):
  config=bytes(RAW[:length]).ljust(length,b'\0');admin=PAYER
  if mutation=='outsider':admin=OUTSIDER
  key=Pubkey.from_bytes(new_key if new_key is not None else bytes([90])*32)
  if key not in [PROGRAM,EVENT,CONFIG_KEY,Pubkey.default(),PAYER.pubkey(),OUTSIDER.pubkey()]:self.vm.set_account(key,Account(10**9,b'',Pubkey.default()))
  self.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'] if lamports is None else lamports,config,PROGRAM))
  system=Pubkey.default() if mutation!='system' else OUTSIDER.pubkey()
  event=EVENT if mutation!='event' else OUTSIDER.pubkey()
  # Separate fee payer allows checking the admin's actual writable/signature requirements.
  payer=OUTSIDER if mutation in ['admin-readonly','unsigned'] else admin
  accounts=[AccountMeta(admin.pubkey(),mutation!='unsigned',instruction=='update_creator_fee_config' and mutation!='admin-readonly'),AccountMeta(CONFIG_KEY,False,mutation!='readonly')]
  if instruction=='set_boost_authority':accounts.append(AccountMeta(key,False,False))
  accounts.extend([AccountMeta(system,False,False),AccountMeta(event,False,False),AccountMeta(PROGRAM,False,False)])
  ix=next(x for x in IDL['instructions'] if x['name']==instruction)
  before=[self.vm.get_account(k).lamports for k in [PAYER.pubkey(),OUTSIDER.pubkey(),CONFIG_KEY]]
  signers=[payer] if payer.pubkey()==admin.pubkey() or mutation=='unsigned' else [payer,admin]
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,bytes(ix['discriminator'])+payload,accounts)],payer.pubkey(),signers,self.vm.latest_blockhash())
  r=self.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
  after=[self.vm.get_account(k).lamports for k in [PAYER.pubkey(),OUTSIDER.pubkey(),CONFIG_KEY]]
  return {'error':str(r.err()) if failed else None,'state_hex':bytes(self.vm.get_account(CONFIG_KEY).data).hex(),'lamport_deltas':[a-b for a,b in zip(after,before)],'events':[x for x in meta.logs() if x.startswith('Program data: ')],'logs':meta.logs()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--creator',action='store_true');a=p.parse_args()
 original=ROOT/'evidence/original/pump_amm/deployed.so';left,right=ResizeHarness(original),ResizeHarness(a.candidate);rows=[]
 def test(**kwargs):
  x,y=left.run(**kwargs),right.run(**kwargs);same=all(x[k]==y[k] for k in ['error','state_hex','lamport_deltas','events'])
  rows.append({'input':{k:v.hex() if isinstance(v,bytes) else v for k,v in kwargs.items()},'original':x,'candidate':y,'match':same})
 for length in [906,907,908,939,940,941,948,949,950,1024]:
  for lamports in [10**6,CONFIG['lamports'],10**9]:
   test(instruction='set_boost_authority',length=length,lamports=lamports)
 for b in [0,1,255]:test(instruction='set_boost_authority',new_key=bytes([b])*32)
 for length in [907,949]:
  for mutation in ['outsider','unsigned','readonly','admin-readonly','system','event']:
   test(instruction='set_boost_authority',length=length,lamports=10**6,mutation=mutation)
 test(instruction='set_boost_authority',payload=b'ignored')
 if a.creator:
  for enabled in [0,1]:
   for bps in [0,1,999,1000,1001,10000,2**64-1]:
    for length in [907,940,949]:test(instruction='update_creator_fee_config',payload=bytes([enabled])+struct.pack('<Q',bps),length=length,lamports=10**6)
  for mutation in ['outsider','unsigned','readonly','admin-readonly','system','event']:
   test(instruction='update_creator_fee_config',payload=b'\1'+struct.pack('<Q',1000),mutation=mutation)
  for payload in [b'',b'\0'+bytes(7),b'\2'+bytes(8),b'\1'+bytes(8)+b'ignored']:test(instruction='update_creator_fee_config',payload=payload)
 failures=[i for i,x in enumerate(rows) if not x['match']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report={'scope':'SBF resize-enabled administrative paths and system CPI; not full program equivalence.','original_sha256':left.sha256,'candidate_sha256':right.sha256,'script_sha256':sha(pathlib.Path(__file__)),'case_count':len(rows),'mismatches':failures,'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'case_count':len(rows),'mismatches':failures[:30],'mismatch_count':len(failures)}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
