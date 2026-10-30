#!/usr/bin/env python3
"""Local SBF account creation/closure differential, including signed system CPI."""
import argparse,hashlib,json,pathlib
from solders.clock import Clock
from pump_amm_admin_differential import *
from pump_differential_output import PumpReport
DISC=bytes(next(x for x in IDL['accounts'] if x['name']=='UserVolumeAccumulator')['discriminator'])
class AccumulatorHarness(Harness):
 def run(self,instruction,user_bytes=None,mutation=None,length=137,offset=None,value=None,prefund=0):
  self.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
  for k in [PAYER,OUTSIDER]:self.vm.set_account(k.pubkey(),Account(10**12,b'',Pubkey.default()))
  user=Pubkey.from_bytes(user_bytes) if user_bytes is not None else PAYER.pubkey()
  accumulator=Pubkey.find_program_address([b'user_volume_accumulator',bytes(user)],PROGRAM)[0]
  if mutation=='pda':accumulator=Pubkey.from_bytes(bytes([88])*32)
  raw=(DISC+bytes(user)+bytes(97))[:length].ljust(length,b'\0')
  owner=PROGRAM if instruction.startswith('close') or mutation=='existing' else Pubkey.default()
  if instruction.startswith('init') and mutation!='existing':raw=b''
  if mutation=='stored-user':raw=raw[:8]+bytes(OUTSIDER.pubkey())+raw[40:]
  if mutation=='owner':owner=Pubkey.default()
  if mutation=='discriminator':raw=bytes([raw[0]^1])+raw[1:]
  if offset is not None:raw=raw[:offset]+value+raw[offset+len(value):]
  self.vm.set_account(accumulator,Account(10**9 if instruction.startswith('close') or mutation=='existing' else prefund,raw,owner))
  event=EVENT if mutation!='event' else OUTSIDER.pubkey();program=PROGRAM if mutation!='program' else OUTSIDER.pubkey()
  if instruction.startswith('init'):
   payer=OUTSIDER if mutation=='payer-readonly' else PAYER
   accounts=[AccountMeta(PAYER.pubkey(),True,mutation!='payer-readonly'),AccountMeta(user,False,False),AccountMeta(accumulator,False,mutation!='readonly'),AccountMeta(Pubkey.default(),False,False),AccountMeta(event,False,False),AccountMeta(program,False,False)]
   signers=[PAYER] if payer==PAYER else [payer,PAYER]
  else:
   payer=OUTSIDER if mutation=='unsigned' else PAYER
   accounts=[AccountMeta(user,mutation!='unsigned',True),AccountMeta(accumulator,False,mutation!='readonly'),AccountMeta(event,False,False),AccountMeta(program,False,False)]
   signers=[payer]
  keys=[PAYER.pubkey(),OUTSIDER.pubkey(),accumulator];before=[self.vm.get_account(k).lamports if self.vm.get_account(k) else 0 for k in keys]
  data=bytes(next(x for x in IDL['instructions'] if x['name']==instruction)['discriminator'])
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,accounts)],payer.pubkey(),signers,self.vm.latest_blockhash());r=self.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
  after=[self.vm.get_account(k).lamports if self.vm.get_account(k) else 0 for k in keys];state=self.vm.get_account(accumulator)
  return {'error':str(r.err()) if failed else None,'state':None if state is None else {'owner':str(state.owner),'data_hex':bytes(state.data).hex(),'lamports':state.lamports},'lamport_deltas':[a-b for a,b in zip(after,before)],'events':[x for x in meta.logs() if x.startswith('Program data: ')],'logs':meta.logs()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();output=PumpReport(a.output,ROOT,a.candidate,__file__);original=ROOT/'evidence/original/pump_amm/deployed.so'
 left,right=AccumulatorHarness(original),AccumulatorHarness(a.candidate);rows=[]
 def test(**kwargs):
  x,y=left.run(**kwargs),right.run(**kwargs);same=all(x[k]==y[k] for k in ['error','state','lamport_deltas','events'])
  rows.append({'input':{k:v.hex() if isinstance(v,bytes) else v for k,v in kwargs.items()},'original':x,'candidate':y,'match':same})
 init='init_user_volume_accumulator';close='close_user_volume_accumulator'
 for user in [PAYER.pubkey(),OUTSIDER.pubkey(),Pubkey.default(),PROGRAM]:
  for prefund in [0,1,10**6,10**9]:test(instruction=init,user_bytes=bytes(user),prefund=prefund)
 for mutation in ['existing','pda','readonly','payer-readonly','event','program']:test(instruction=init,mutation=mutation)
 for length in [0,7,8,40,41,72,73,74,82,89,90,136,137,138]:test(instruction=close,length=length)
 for mutation in ['pda','readonly','unsigned','event','program','owner','discriminator','stored-user']:test(instruction=close,mutation=mutation)
 for offset,size in [(40,1),(41,8),(49,8),(57,8),(65,8),(73,1),(74,8),(82,8)]:
  for v in [1,2] if size==1 else [1,2**64-1]:test(instruction=close,offset=offset,value=v.to_bytes(size,'little'))
 for offset,size in [(40,1),(41,8),(49,8),(57,8),(65,8),(73,1),(74,8),(82,8)]:
  test(instruction=init,mutation='existing',offset=offset,value=(1).to_bytes(size,'little'))
 test(instruction=init,mutation='existing',offset=8,value=bytes(OUTSIDER.pubkey()))
 for length in [73,74,89,90,136,137,138]:test(instruction=init,mutation='existing',length=length)
 failures=[i for i,x in enumerate(rows) if not x['match']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report={'scope':'SBF init/close volume accumulator only, including actual local system CPI. Not whole program equivalence.','original_sha256':left.sha256,'candidate_sha256':right.sha256,'script_sha256':sha(pathlib.Path(__file__)),'case_count':len(rows),'mismatches':failures,'cases':rows}
 output.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'case_count':len(rows),'mismatches':failures[:30],'mismatch_count':len(failures)}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
