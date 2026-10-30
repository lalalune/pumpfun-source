#!/usr/bin/env python3
"""Local normal-signature holder fee payout fixture, no network writes."""
import json,base64,hashlib,struct
from pathlib import Path
from solders.litesvm import LiteSVM
from solders.account import Account
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.instruction import Instruction,AccountMeta
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from solders.compute_budget import set_compute_unit_limit
from solders.clock import Clock
from probe_report import write_json_report
ROOT=Path(__file__).resolve().parents[1];IDL=json.loads((ROOT/'evidence/upstream/pump.json').read_text());PUMP=Pubkey.from_string(IDL['address']);TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');WSOL=Pubkey.from_string('So11111111111111111111111111111111111111112');AUTH=Keypair.from_seed(bytes([218])*32);PAYER=Keypair.from_seed(bytes([219])*32);OTHER=Keypair.from_seed(bytes([220])*32);MINT=Pubkey.from_bytes(bytes([221])*32);STABLE=Pubkey.from_bytes(bytes([222])*32);pda=lambda seeds,p=PUMP:Pubkey.find_program_address(seeds,p)[0];ata=lambda wallet,mint,token=TOKEN:pda([bytes(wallet),bytes(token),bytes(mint)],ATA);GLOBAL=pda([b'global']);HOLDER=pda([b'holder-rewards',bytes(MINT)]);EVENT=pda([b'__event_authority']);SAVED=json.loads((ROOT/'research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json').read_text())['missing_boost']['before']['global']
def token_data(mint,owner,amount,native=False):
 d=bytearray(165);d[:32]=bytes(mint);d[32:64]=bytes(owner);d[64:72]=amount.to_bytes(8,'little');d[108]=1
 if native:d[109:113]=(1).to_bytes(4,'little');d[113:121]=(2039280).to_bytes(8,'little')
 return bytes(d)
def run(c={},candidate=None):
 vm=LiteSVM().with_sigverify(True).with_transaction_history(0).with_log_bytes_limit(200000);vm.set_clock(Clock(100,1234567890,0,0,1234567890));tracked=set()
 def put(k,a):tracked.add(k);vm.set_account(k,a)
 for pid,file in [(PUMP,'original/pump'),(TOKEN,'dependencies/spl_token'),(TOKEN22,'dependencies/spl_token_2022'),(ATA,'dependencies/associated_token')]:vm.add_program_from_file(pid,ROOT/'evidence'/file/'deployed.so')
 if candidate:vm.add_program_from_file(PUMP,candidate)
 quote=STABLE if c.get('stable') else WSOL;token=TOKEN22 if c.get('token22') else TOKEN;source=ata(HOLDER,quote,token) if c.get('source',c.get('stable',False)) else PUMP
 gd=bytearray(base64.b64decode(SAVED['data_base64']));gd[1054:1086]=bytes(AUTH.pubkey());put(GLOBAL,Account(SAVED['lamports'],bytes(gd),PUMP));put(AUTH.pubkey(),Account(10**12,b'',Pubkey.default()));put(PAYER.pubkey(),Account(10**12,b'',Pubkey.default()));put(OTHER.pubkey(),Account(10**9,b'',Pubkey.default()));put(HOLDER,Account(c.get('holder_lamports',20_000_000),b'',Pubkey.default()))
 md=bytearray(82);md[44]=6;md[45]=1;put(MINT,Account(1461600,bytes(md),TOKEN));md[44]=6 if c.get('stable') else 9;put(quote,Account(1461600,bytes(md),token))
 if c.get('alternate_source') and source!=PUMP:source=Pubkey.from_bytes(bytes([224])*32)
 if source!=PUMP:
  amount=c.get('source_amount',10**9);native=not c.get('stable');put(source,Account(2039280+(amount if native else 0),token_data(quote,HOLDER,amount,native),token))
 amounts=c.get('amounts',[1000]);owners=[Pubkey.from_string(k) for k in c.get('owners',[str(OTHER.pubkey())]*len(amounts))];dest=[ata(k,quote,token) for k in owners]
 if c.get('alternate_dest'):dest=[Pubkey.from_bytes(bytes([225+i])*32) for i in range(len(owners))]
 if c.get('existing_dest'):
  for k,w in zip(dest,owners):put(k,Account(2039280,token_data(quote,w,c.get('dest_amount',0)),token))
 names={'global':GLOBAL,'holder_reward_claim_authority':AUTH.pubkey(),'mint':MINT,'holder_rewards':HOLDER,'holder_rewards_token_account':source,'quote_mint':quote,'quote_token_program':token,'associated_token_program':ATA,'system_program':Pubkey.default(),'event_authority':EVENT,'program':PUMP}
 if c.get('swap_token_program'):names['quote_token_program']=TOKEN if token==TOKEN22 else TOKEN22
 for name,mutation in c.get('mutations',{}).items():
  key=dest[0] if name=='dest' else owners[0] if name=='owner' else names[name];a=vm.get_account(key);data=bytearray(a.data if a else b'')
  for off,val in mutation.get('patches',[]):data[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
  if 'length'in mutation:data=data[:mutation['length']];data.extend(bytes(max(0,mutation['length']-len(data))))
  put(key,Account(mutation.get('lamports',a.lamports if a else 0),bytes(data),Pubkey.from_string(mutation.get('owner',str(a.owner if a else Pubkey.default()))),mutation.get('executable',False)))
 spec=next(x for x in IDL['instructions'] if x['name']=='distribute_fee_to_holders');metas=[AccountMeta(names[x['name']],x.get('signer',False) and not c.get('unsigned'),(x.get('writable',False) or x['name'] in c.get('writable',[])) and x['name']!=c.get('readonly')) for x in spec['accounts']]
 if c.get('wrong'):
  i=next(i for i,x in enumerate(spec['accounts']) if x['name']==c['wrong']);m=metas[i];metas[i]=AccountMeta(Pubkey.from_bytes(bytes([223])*32),m.is_signer,m.is_writable)
 remaining=[]
 for wallet,d in zip(owners,dest):remaining += [AccountMeta(wallet,False,not c.get('readonly_owner')),AccountMeta(d,False,not c.get('readonly_dest'))]
 remaining += [AccountMeta(OTHER.pubkey(),False,True)]*c.get('extra_remaining',0)
 metas += remaining[:c.get('remaining_count',len(remaining))];payload=bytes(spec['discriminator'])+len(amounts).to_bytes(4,'little')+b''.join(n.to_bytes(8,'little') for n in amounts)
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PUMP,payload,metas)],PAYER.pubkey(),[PAYER]+([] if c.get('unsigned') else [AUTH]),vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for k in tracked|set(tx.message.account_keys):
   a=vm.get_account(k)
   if a and a.executable:continue
   out[str(k)]=None if a is None else {'lamports':a.lamports,'data':a.data.hex(),'owner':str(a.owner)}
  return out
 before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r;raw=json.loads(meta.to_json());return {'case':c,'signature_verification':True,'transaction_base64':base64.b64encode(bytes(tx)).decode(),'error':str(r.err()) if failed else None,'logs':meta.logs(),'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw.get('return_data'),'before':before,'after':snap(),'names':{k:str(v) for k,v in names.items()},'account_keys':[str(k) for k in tx.message.account_keys]}
if __name__=='__main__':
 rows=[run(c) for c in [{},{'source':True},{'stable':True},{'stable':True,'token22':True}]];write_json_report(ROOT/'work/pump-holder-distribution-recovery/prerequisites.json',rows);print(json.dumps([{'case':r['case'],'error':r['error'],'logs':r['logs'][-5:]} for r in rows],indent=2))
