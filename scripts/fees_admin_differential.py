#!/usr/bin/env python3
"""Pump Fees administration: independent original/candidate local SBF execution."""
import argparse,hashlib,json,pathlib,struct
from solders.account import Account
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_differential_output import PumpReport
ROOT=pathlib.Path(__file__).resolve().parents[1]
IDL=json.loads((ROOT/'evidence/upstream/pump_fees.json').read_text())
PROGRAM=Pubkey.from_string(IDL['address']);GLOBAL,BUMP=Pubkey.find_program_address([b'fee-program-global'],PROGRAM);EVENT=Pubkey.find_program_address([b'__event_authority'],PROGRAM)[0]
AUTH=Keypair.from_seed(bytes([213])*32);OTHER=Keypair.from_seed(bytes([214])*32);PAYER=Keypair.from_seed(bytes([215])*32)
DISC=bytes(next(x['discriminator'] for x in IDL['accounts'] if x['name']=='FeeProgramGlobal'))
BASE=DISC+bytes([BUMP])+bytes(AUTH.pubkey())+bytes([17])+bytes([44])*32+(123).to_bytes(8,'little')+bytes(256)
class Fixture:
 def __init__(self,binary):
  image=pathlib.Path(binary).read_bytes()
  self.program_sha256=hashlib.sha256(image).hexdigest()
  self.vm=LiteSVM().with_transaction_history(0);self.vm.add_program(PROGRAM,image)
  for key in [AUTH,OTHER,PAYER]:self.vm.airdrop(key.pubkey(),10**12)
 def run(self,c):
  data=bytearray(BASE);owner=PROGRAM;key=GLOBAL;authority=AUTH;sign=True;write=True;authority_write=True;event=EVENT;program=PROGRAM;lamports=10**9
  mutation=c.get('mutation','none')
  if mutation=='owner':owner=Pubkey.default()
  if mutation=='discriminator':data[0]^=1
  if mutation=='bump':data[8]^=1
  if mutation=='key':key=Pubkey.from_bytes(bytes([45])*32)
  if mutation=='authority':authority=OTHER
  if mutation=='unsigned':sign=False
  if mutation=='readonly':write=False
  if mutation=='authority_readonly':authority_write=False
  if mutation=='event':event=Pubkey.from_bytes(bytes([46])*32)
  if mutation=='program':program=Pubkey.default()
  if mutation=='zero_lamports':lamports=0
  if mutation.startswith('length:'):data=data[:int(mutation.split(':')[1])]
  self.vm.set_account(key,Account(lamports,bytes(data),owner))
  metas=[AccountMeta(authority.pubkey(),sign,authority_write),AccountMeta(key,False,write),AccountMeta(event,False,False),AccountMeta(program,False,False)]
  if mutation.startswith('accounts:'):metas=metas[:int(mutation.split(':')[1])]
  disc=bytes(next(x['discriminator'] for x in IDL['instructions'] if x['name']==c['instruction']))
  payload=disc+bytes.fromhex(c['arg'])
  payer_before=self.vm.get_account(PAYER.pubkey()).lamports
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[PAYER,authority] if sign and metas else [PAYER],self.vm.latest_blockhash())
  result=self.vm.send_transaction(tx);failed=isinstance(result,FailedTransactionMetadata);meta=result.meta() if failed else result;after=self.vm.get_account(key)
  md=json.loads(meta.to_json())
  return {'error':str(result.err()) if failed else None,'data_hex':after.data.hex() if after else None,'lamports':after.lamports if after else None,'owner':str(after.owner) if after else None,'payer_delta':self.vm.get_account(PAYER.pubkey()).lamports-payer_before,'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner_instructions':md['inner_instructions'],'logs':meta.logs()}
def cases():
 out=[]
 for name,values in [('set_authority',[bytes(32),bytes(AUTH.pubkey()),bytes(OTHER.pubkey())]),('set_social_claim_authority',[bytes(32),bytes([44])*32,bytes(OTHER.pubkey())]),('set_disable_flags',[bytes([n]) for n in range(256)]),('set_claim_rate_limit',[n.to_bytes(8,'little') for n in [0,1,123,2**32,2**64-1]])]:
  for i,value in enumerate(values):out.append({'name':name+'-'+str(i),'instruction':name,'arg':value.hex()})
  for mutation in ['owner','discriminator','bump','key','authority','unsigned','readonly','authority_readonly','event','program','zero_lamports']+['accounts:'+str(n) for n in range(4)]+['length:'+str(n) for n in [0,7,8,9,40,73,81,82,337,338]]:
   out.append({'name':name+'-'+mutation,'instruction':name,'arg':values[-1].hex(),'mutation':mutation})
  for n in range(len(values[0])):out.append({'name':name+'-arglength-'+str(n),'instruction':name,'arg':values[0][:n].hex()})
  out.append({'name':name+'-extra-args','instruction':name,'arg':(values[-1]+bytes([255])*16).hex()})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__)
 orig=ROOT/'evidence/original/pump_fees/deployed.so';o=Fixture(orig);b=Fixture(a.candidate) if a.candidate else None;rows=[];failures=[]
 for c in cases():
  x=o.run(c);y=b.run(c) if b else None
  matched=all(x[k]==y[k] for k in ['error','data_hex','lamports','owner','payer_delta','events','inner_instructions']) if b else None
  rows.append({'case':c,'original':x,'candidate':y,'match':matched})
  if matched is False:failures.append(c['name'])
 report={'scope':'Four administrative handlers only; local synthetic accounts, errors/state/lamports/events/inner instructions compared. No full byte identity or audit completion.','original_sha256':o.program_sha256,'candidate_sha256':b.program_sha256 if b else None,'case_count':len(rows),'mismatches':failures,'cases':rows}
 publisher.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'case_count':len(rows),'mismatches':failures}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
