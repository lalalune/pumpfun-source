#!/usr/bin/env python3
"""Offline creation reconstruction with ordinary mint and payer signatures."""
import argparse,base64,gzip,hashlib,json,struct
from pathlib import Path
from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_amm_reusable_harness import pin_program
ROOT=Path(__file__).resolve().parents[1];IDL=json.loads((ROOT/'evidence/upstream/pump.json').read_text(encoding='utf-8'));PROGRAM=Pubkey.from_string(IDL['address']);ORIGINAL=ROOT/'evidence/original/pump/deployed.so'
USER=Keypair.from_seed(bytes([211])*32);MINT=Keypair.from_seed(bytes([212])*32);OTHER=Keypair.from_seed(bytes([213])*32)
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');META=Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s');GLOBAL=Pubkey.find_program_address([b'global'],PROGRAM)[0];CURVE=Pubkey.find_program_address([b'bonding-curve',bytes(MINT.pubkey())],PROGRAM)[0];MA=Pubkey.find_program_address([b'mint-authority'],PROGRAM)[0];EVENT=Pubkey.find_program_address([b'__event_authority'],PROGRAM)[0]
CAPTURE=next(x for x in json.loads((ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name']=='pump')
def string(s):
 b=s.encode();return struct.pack('<I',len(b))+b

def run(c,binary=ORIGINAL):
 vm=LiteSVM().with_transaction_history(0);vm.add_program_from_file(PROGRAM,pin_program(binary))
 for name,key in [('spl_token',TOKEN),('spl_token_2022',TOKEN22),('associated_token',ATA),('token_metadata',META)]:vm.add_program_from_file(key,ROOT/'evidence/dependencies'/name/'deployed.so')
 vm.set_clock(Clock(100,1700000000,0,0,1700000000));vm.airdrop(USER.pubkey(),10**12)
 data=bytearray(base64.b64decode(CAPTURE['data_base64']))
 for off,hexdata in c.get('global_patches',[]):data[off:off+len(bytes.fromhex(hexdata))]=bytes.fromhex(hexdata)
 vm.set_account(GLOBAL,Account(10**9,bytes(data),PROGRAM))
 ix=next(x for x in IDL['instructions'] if x['name']==c.get('instruction','create'))
 names={'mint':MINT.pubkey(),'mint_authority':MA,'bonding_curve':CURVE,'associated_bonding_curve':Pubkey.find_program_address([bytes(CURVE),bytes(TOKEN),bytes(MINT.pubkey())],ATA)[0],'global':GLOBAL,'mpl_token_metadata':META,'metadata':Pubkey.find_program_address([b'metadata',bytes(META),bytes(MINT.pubkey())],META)[0],'user':USER.pubkey(),'system_program':Pubkey.default(),'token_program':TOKEN,'associated_token_program':ATA,'rent':Pubkey.from_string('SysvarRent111111111111111111111111111111111'),'event_authority':EVENT,'program':PROGRAM}
 if c.get('instruction')=='create_v2':
  mayhem=Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e');vm.add_program_from_file(mayhem,ROOT/'evidence/original/mayhem/deployed.so')
  names.update(token_program=TOKEN22,associated_bonding_curve=Pubkey.find_program_address([bytes(CURVE),bytes(TOKEN22),bytes(MINT.pubkey())],ATA)[0],mayhem_program_id=mayhem,global_params=Pubkey.find_program_address([b'global-params'],mayhem)[0],sol_vault=Pubkey.find_program_address([b'sol-vault'],mayhem)[0],mayhem_state=Pubkey.find_program_address([b'mayhem-state',bytes(MINT.pubkey())],mayhem)[0],mayhem_token_vault=OTHER.pubkey())
 if c.get('quote'):
  quote=OTHER.pubkey();qt=TOKEN22 if c.get('quote_token22') else TOKEN
  mint_data=struct.pack('<I',1)+bytes(USER.pubkey())+struct.pack('<Q',10**15)+bytes([6,1])+bytes(36)
  if c.get('quote_extensions'):
   mint_data+=bytes(83)+bytes([1])+b''.join(struct.pack('<HH',t,len(bytes.fromhex(v)))+bytes.fromhex(v) for t,v in c['quote_extensions'])
  vm.set_account(quote,Account(10000000,mint_data,qt))
  if c.get('quote_whitelisted',True):
   gd=bytearray(vm.get_account(GLOBAL).data);gd[1013:1045]=bytes(quote);vm.set_account(GLOBAL,Account(10**9,bytes(gd),PROGRAM))
  names.update(quote_mint=quote,associated_quote_bonding_curve=Pubkey.find_program_address([bytes(CURVE),bytes(qt),bytes(quote)],ATA)[0],quote_token_program=qt)
 if c.get('quote_control'):
  control=Pubkey.find_program_address([b'quote-control'],PROGRAM)[0]
  entries=c.get('control_entries',[(str(OTHER.pubkey()),c.get('control_reserves',123456789))])
  blob=hashlib.sha256(b'account:QuoteControl').digest()[:8]+bytes(USER.pubkey())*2+bytes(32)+struct.pack('<I',len(entries))+b''.join(bytes(Pubkey.from_string(k))+struct.pack('<Q',n) for k,n in entries)
  vm.set_account(control,Account(10**9,blob,PROGRAM));names['quote_control']=control
 if c.get('nested'):
  names['quote_bonding_curve']=Pubkey.find_program_address([b'bonding-curve',bytes(OTHER.pubkey())],PROGRAM)[0]
 if c.get('wrong'):names[c['wrong']]=USER.pubkey() if c.get('quote') and c['wrong'].startswith('quote_') else OTHER.pubkey()
 metas=[AccountMeta(names[a['name']],a.get('signer',False) and c.get('unsigned')!=a['name'],a.get('writable',False) and c.get('readonly')!=a['name']) for a in ix['accounts']][:c.get('account_count',100)]
 if c.get('quote'):metas += [AccountMeta(names['quote_mint'],False,False),AccountMeta(names['associated_quote_bonding_curve'],False,c.get('readonly')!='associated_quote_bonding_curve'),AccountMeta(names['quote_token_program'],False,False)][:c.get('quote_count',3)]
 if c.get('quote_control'):metas.append(AccountMeta(names['quote_control'],False,False))
 if c.get('nested'):metas.append(AccountMeta(names['quote_bonding_curve'],False,False))
 payload=bytes(ix['discriminator'])+string(c.get('name','Synthetic Coin'))+string(c.get('symbol','SYNTH'))+string(c.get('uri','https://example.invalid/metadata.json'))+bytes(Pubkey.from_string(c.get('creator',str(USER.pubkey()))))
 if c.get('instruction')=='create_v2':payload+=bytes([0])+bytes.fromhex(c.get('optional_args',''))
 payload=(payload+bytes.fromhex(c.get('trailing','')))[:c.get('payload_length',100000)]
 for name,mut in c.get('mutations',{}).items():
  key=names[name];a=vm.get_account(key) or Account(0,b'',Pubkey.default());d=bytearray(a.data)
  for off,val in mut.get('patches',[]):d[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
  size=mut.get('length',len(d));d=(d+bytes(max(0,size-len(d))))[:size];vm.set_account(key,Account(mut.get('lamports',a.lamports),bytes(d),Pubkey.from_string(mut.get('owner',str(a.owner)))))
 if c.get('bootstrap_accounts'):
  for key,value in c['bootstrap_accounts'].items():
   if value is not None:vm.set_account(Pubkey.from_string(key),Account(value['lamports'],bytes.fromhex(value['data']),Pubkey.from_string(value['owner'])))
 signers={a.pubkey for a in metas if a.is_signer}|{USER.pubkey()};tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PROGRAM,payload,metas)],USER.pubkey(),[k for k in [USER,MINT,OTHER] if k.pubkey() in signers],vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for key in set(names.values()):
   a=vm.get_account(key)
   if a and a.executable:continue
   out[str(key)]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
  return out
 before=snap();r=vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);m=r.meta() if fail else r;raw=json.loads(m.to_json())
 return {'before':before,'after':snap(),'error':str(r.err()) if fail else None,'logs':m.logs(),'events':[l for l in m.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw.get('return_data'),'transaction_base64':base64.b64encode(bytes(tx)).decode()}
