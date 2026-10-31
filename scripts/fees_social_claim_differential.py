#!/usr/bin/env python3
"""Normally signed synthetic offline social fee claims, original/candidate comparison."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,base64,hashlib,json,pathlib,sys
from fees_admin_differential import IDL,PROGRAM,GLOBAL,EVENT,AUTH,OTHER,PAYER,BASE
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta,Instruction
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport
IX=next(x for x in IDL['instructions'] if x['name']=='claim_social_fee_pda')
class Fixture:
 def __init__(self,binary):
  self.vm=LiteSVM().with_transaction_history(0);self.vm.add_program_from_file(PROGRAM,binary)
 def run(self,c):
  self.vm.set_clock(Clock(1000,0,0,0,c.get('time',1700000000)))
  uid=c.get('user_id','12345').encode();platform=c.get('platform',0)
  social,bump=Pubkey.find_program_address([b'social-fee-pda',uid,bytes([platform])],PROGRAM)
  state=hashlib.sha256(b'account:SocialFeePda').digest()[:8]+bytes([bump,c.get('version',1)])+len(uid).to_bytes(4,'little')+uid+bytes([platform])+c.get('total',0).to_bytes(8,'little')+c.get('last',0).to_bytes(8,'little')+c.get('stable_total',0).to_bytes(8,'little')+bytes(120)
  state=bytearray(state.ljust(c.get('allocation',179),b'\0'))
  for offset,value in c.get('patches',[]):state[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  state=state[:c.get('length',len(state))]
  self.vm.set_account(social,Account(self.vm.minimum_balance_for_rent_exemption(179)+c.get('amount',1000000),bytes(state),Pubkey.from_string(c.get('owner',str(PROGRAM)))))
  gd=bytearray(BASE);gd[41]=c.get('flags',0);gd[42:74]=bytes(AUTH.pubkey());gd[74:82]=c.get('rate',60).to_bytes(8,'little')
  for offset,value in c.get('global_patches',[]):gd[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  self.vm.set_account(GLOBAL,Account(10**9,bytes(gd),Pubkey.from_string(c.get('global_owner',str(PROGRAM)))))
  for kp in [PAYER,AUTH,OTHER]:self.vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
  authority=OTHER if c.get('wrong_authority') else AUTH
  names={'recipient':OTHER.pubkey(),'social_fee_pda':social,'fee_program_global':GLOBAL,'social_claim_authority':authority.pubkey(),'event_authority':EVENT,'program':PROGRAM}
  if c.get('wrong'):names[c['wrong']]=Pubkey.from_bytes(bytes([77])*32)
  if c.get('recipient_program'):names['recipient']=PROGRAM
  if c.get('recipient_alias'):names['recipient']=names[c['recipient_alias']]
  metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and c.get('readonly')!=a['name']) for a in IX['accounts']]
  metas=metas[:c.get('account_count',len(metas))]
  payload=bytes(IX['discriminator'])+len(uid).to_bytes(4,'little')+uid+bytes([platform])+bytes.fromhex(c.get('trailing',''))
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[PAYER]+([authority] if any(m.pubkey==authority.pubkey() and m.is_signer for m in metas) else []),self.vm.latest_blockhash());assert all(tx.verify_with_results())
  def snapshot():
   out={}
   for name,key in {**names,'transaction_payer':PAYER.pubkey()}.items():
    a=self.vm.get_account(key)
    if a and a.executable:continue
    out[name]=None if a is None else {'data':a.data.hex(),'owner':str(a.owner),'lamports':a.lamports}
   return out
  before=snapshot();result=self.vm.send_transaction(tx);failed=isinstance(result,FailedTransactionMetadata);meta=result.meta() if failed else result;raw=json.loads(meta.to_json())
  return {'error':str(result.err()) if failed else None,'before':before,'after':snapshot(),'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw.get('return_data'),'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode()}
def cases():
 out=[{'name':'base'},{'name':'zero','amount':0},{'name':'one','amount':1},{'name':'below-rent','amount':-1}]
 out += [{'name':'flags-'+str(n),'flags':n} for n in range(256)]
 out += [{'name':'last-'+str(n),'last':n} for n in [1699999939,1699999940,1699999941,1699999999,1700000000,1700000001,2**64-1]]
 out += [{'name':'rate-'+str(n),'rate':n} for n in [0,1,2**64-1]]
 out += [{'name':'version-'+str(n),'version':n} for n in [0,2,255]]
 out += [{'name':'total-overflow','total':2**64-1},{'name':'negative-clock','time':-1}]
 out += [{'name':'wrong-'+a['name'],'wrong':a['name']} for a in IX['accounts'] if a['name']!='social_claim_authority']
 out += [{'name':'unsigned','unsigned':True},{'name':'recipient-program','recipient_program':True},{'name':'stable-total','stable_total':99}]
 out += [{'name':'recipient-alias-'+n,'recipient_alias':n} for n in ['social_fee_pda','fee_program_global','social_claim_authority']]
 out += [{'name':'readonly-'+n,'readonly':n} for n in ['recipient','social_fee_pda']]
 out += [{'name':'last-rate-'+str(last)+'-'+str(rate),'last':last,'rate':rate} for last in [1,1700000000,1700000001,2**64-1] for rate in [0,1,2**64-1]]
 out += [{'name':'length-'+str(n),'length':n} for n in [0,7,8,9,10,14,19,20,43,44,163,164,178,179]]
 out += [{'name':'allocation-'+str(n),'allocation':n} for n in [180,200,300]]
 out += [{'name':'patch-'+str(offset),'patches':[(offset,'00')]} for offset in [0,8,9,14,19]]
 out += [{'name':'userid-'+str(i),'user_id':uid} for i,uid in enumerate(['','abc','x'*20,'x'*21,'x'*32,'é'*10])]
 out += [{'name':'platform-'+str(n),'platform':n} for n in [1,2,3,127,255]]
 out += [{'name':'wrong-authority','wrong_authority':True},{'name':'global-owner','global_owner':str(Pubkey.default())}]
 out += [{'name':'global-patch-'+str(n),'global_patches':[(n,'00')]} for n in [0,8,42]]
 out += [{'name':'accounts-'+str(n),'account_count':n} for n in range(6)]
 out += [{'name':'trailing-arguments','trailing':'ff01'},{'name':'zero-and-disabled','amount':0,'flags':2},{'name':'zero-and-rate','amount':0,'last':1700000000}]
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__);orig=pin_program(ROOT/'evidence/original/pump_fees/deployed.so');o=Fixture(orig);b=Fixture(pin_program(a.candidate)) if a.candidate else None;rows=[];bad=[]
 for c in cases():
  x=o.run(c);y=b.run(c) if b else None;match=all(x[k]==y[k] for k in ['error','before','after','events','inner','return']) if b else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 report={'scope':'Synthetic local signed social claim fixtures. No full byte identity claim.','original_sha256':hashlib.sha256(orig.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'cases':rows,'mismatches':bad}
 publisher.write((json.dumps(report,indent=2)+'\n').encode('utf-8'));print('Cases',len(rows),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
