#!/usr/bin/env python3
"""Ordinary signed local migrate-v2 prerequisite probe; captured actual CPIs."""
from pathlib import Path
import json,base64,hashlib,sys
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
R=Path(__file__).resolve().parents[1];IDL=json.loads((R/'evidence/upstream/pump.json').read_text());P=Pubkey.from_string(IDL['address']);A=Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA');TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');T22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');WSOL=Pubkey.from_string('So11111111111111111111111111111111111111112');USER=Keypair.from_seed(bytes([212])*32);PAYER=Keypair.from_seed(bytes([213])*32);MINT=Pubkey.from_bytes(bytes([214])*32)
SAVED=json.loads((R/'research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json').read_text())['missing_boost']['before'];pda=lambda seeds,program:Pubkey.find_program_address(seeds,program)[0];ata=lambda w,m,t=TOKEN:pda([bytes(w),bytes(t),bytes(m)],ATA)
def run(c={},candidate=None):
 token=T22 if c.get('token22',True) else TOKEN;quote=Pubkey.from_bytes(bytes([217])*32) if c.get('stable') else WSOL;qt=T22 if c.get('quote22') else TOKEN
 vm=LiteSVM().with_sigverify(True).with_transaction_history(0).with_log_bytes_limit(200000);vm.set_clock(Clock(100,1234567890,0,0,1234567890));tracked=set()
 def put(k,a):tracked.add(k);vm.set_account(k,a)
 for pid,file in [(P,'original/pump'),(A,'original/pump_amm'),(TOKEN,'dependencies/spl_token'),(T22,'dependencies/spl_token_2022'),(ATA,'dependencies/associated_token')]:vm.add_program_from_file(pid,R/'evidence'/file/'deployed.so')
 curve=pda([b'bonding-curve',bytes(MINT)],P);pa=pda([b'pool-authority',bytes(MINT)],P);pool=pda([b'pool',bytes(2),bytes(pa),bytes(MINT),bytes(quote)],A);lp=pda([b'pool_lp_mint',bytes(pool)],A)
 gd=bytearray(base64.b64decode(SAVED['global']['data_base64']));withdraw=Pubkey.from_bytes(bytes(gd[113:145]));gd[145]=c.get('enable_migrate',1)
 names={'global':pda([b'global'],P),'withdraw_authority':withdraw,'base_mint':MINT,'quote_mint':quote,'bonding_curve':curve,'associated_base_bonding_curve':ata(curve,MINT,token),'associated_quote_bonding_curve':ata(curve,quote,qt),'user':USER.pubkey(),'system_program':Pubkey.default(),'base_token_program':token,'quote_token_program':qt,'pump_amm':A,'pool':pool,'pool_authority':pa,'pool_authority_mint_account':ata(pa,MINT,token),'pool_authority_quote_account':ata(pa,quote,qt),'amm_global_config':pda([b'global_config'],A),'lp_mint':lp,'user_pool_token_account':ata(pa,lp,T22),'pool_base_token_account':ata(pool,MINT,token),'pool_quote_token_account':ata(pool,quote,qt),'token_2022_program':T22,'associated_token_program':ATA,'pump_amm_event_authority':pda([b'__event_authority'],A),'event_authority':pda([b'__event_authority'],P),'program':P,'rent':Pubkey.from_string('SysvarRent111111111111111111111111111111111')}
 put(PAYER.pubkey(),Account(10**12,b'',Pubkey.default()));put(USER.pubkey(),Account(10**12,b'',Pubkey.default()));put(names['global'],Account(SAVED['global']['lamports'],bytes(gd),P))
 cd=bytearray(base64.b64decode(SAVED['curve']['data_base64']));cd[48]=c.get('complete',1);cd[49:81]=bytes(USER.pubkey());cd[81]=c.get('mayhem',0);put(curve,Account(SAVED['curve']['lamports'],bytes(cd),P))
 md=bytearray(base64.b64decode(SAVED['mint']['data_base64'])[:82]);put(MINT,Account(1461600,bytes(md),token))
 td=bytearray(base64.b64decode(SAVED['curve_base']['data_base64'])[:165]);td[:32]=bytes(MINT);td[32:64]=bytes(curve);put(names['associated_base_bonding_curve'],Account(2039280,bytes(td),token))
 wd=bytearray(82);wd[44]=6 if c.get('stable') else 9;wd[45]=1;put(quote,Account(1461600,bytes(wd),qt))
 ac=SAVED['amm_global_config'];put(names['amm_global_config'],Account(ac['lamports'],base64.b64decode(ac['data_base64']),A))
 if c.get('stable'):
  qd=bytearray(165);qd[:32]=bytes(quote);qd[32:64]=bytes(curve);qd[64:72]=(85005359063).to_bytes(8,'little');qd[108]=1;put(names['associated_quote_bonding_curve'],Account(2039280,bytes(qd),qt))
  cd[83:115]=bytes(quote);put(curve,Account(660837992,bytes(cd),P))
  gd[1013:1045]=bytes(quote);put(names['global'],Account(SAVED['global']['lamports'],bytes(gd),P))
 for name,mutation in c.get('mutations',{}).items():
  key=names[name];a=vm.get_account(key);data=bytearray(a.data if a else b'')
  for off,value in mutation.get('patches',[]):data[off:off+len(bytes.fromhex(value))]=bytes.fromhex(value)
  if 'length' in mutation:data=data[:mutation['length']]
  put(key,Account(mutation.get('lamports',a.lamports if a else 0),bytes(data),Pubkey.from_string(mutation.get('owner',str(a.owner if a else Pubkey.default()))),mutation.get('executable',False)))
 if candidate:vm.add_program_from_file(P,candidate)

 ix=next(i for i in IDL['instructions'] if i['name']=='migrate_v2');metas=[AccountMeta(names[x['name']],x.get('signer',False) and not c.get('unsigned'),(x.get('writable',False) or x['name'] in c.get('writable',[])) and x['name']!=c.get('readonly')) for x in ix['accounts']]
 if c.get('wrong'):
  idx=next(i for i,x in enumerate(ix['accounts']) if x['name']==c['wrong']);m=metas[idx];metas[idx]=AccountMeta(Pubkey.from_bytes(bytes([216])*32),m.is_signer,m.is_writable)
 if c.get('boost'):
  boost=pda([b'boost_vault',bytes(pool)],A);vault=ata(boost,quote,qt);names['boost_authority']=boost;names['boost_vault']=vault;metas += [AccountMeta(boost,False,False),AccountMeta(vault,False,not c.get('readonly_boost'))][:c.get('remaining_count',2)]
 def snap():
  out={}
  for k in tracked|set(names.values()):
   a=vm.get_account(k)
   if a and a.executable:continue
   out[str(k)]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
  return out
 before=snap();tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(P,bytes(ix['discriminator']),metas)],PAYER.pubkey(),[PAYER]+([] if c.get('unsigned') else [USER]),vm.latest_blockhash());assert all(tx.verify_with_results());r=vm.send_transaction(tx);
 if c.get('repeat') and not isinstance(r,FailedTransactionMetadata):r=vm.send_transaction(tx)
 failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 return {'case':c,'signature_verification':True,'transaction_base64':base64.b64encode(bytes(tx)).decode(),'error':str(r.err()) if failed else None,'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions'],'return':json.loads(meta.to_json()).get('return_data'),'before':before,'after':snap(),'names':{k:str(v) for k,v in names.items()},'account_keys':[str(k) for k in tx.message.account_keys]}
if __name__=='__main__':
 rows=[run(c) for c in [{'boost':True},{'boost':True,'token22':False},{'boost':True,'stable':True},{'boost':True,'stable':True,'quote22':True}]]
 write_json_report(R/'work/pump-migrate-v2-recovery/prerequisites.json',rows);print(json.dumps([{'case':r['case'],'error':r['error'],'logs':r['logs'][-5:]} for r in rows],indent=2))
