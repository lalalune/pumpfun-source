#!/usr/bin/env python3
"""Original-only normally signed offline referral withdraw probes."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,hashlib,base64
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from pump_differential_output import PumpReport
from fees_admin_differential import IDL,PROGRAM,EVENT,AUTH,OTHER,PAYER
from solders.account import Account
from solders.clock import Clock
from solders.pubkey import Pubkey
from solders.instruction import AccountMeta,Instruction
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from solders.compute_budget import set_compute_unit_limit
from solders.litesvm import LiteSVM
IX=next(x for x in IDL['instructions'] if x['name']=='withdraw')
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');WSOL=Pubkey.from_string('So11111111111111111111111111111111111111112')
MINT=Pubkey.from_bytes(bytes([61])*32);ORIGINAL=ROOT/'evidence/original/pump_fees/deployed.so'
VAULT,BUMP=Pubkey.find_program_address([b'referral-vault',bytes(AUTH.pubkey())],PROGRAM)
def run(c,image):
 vm=LiteSVM().with_transaction_history(0);vm.add_program(PROGRAM,image);vm.set_clock(Clock(1000,0,0,0,1700000000))
 for name,key in [('spl_token',TOKEN),('spl_token_2022',TOKEN22),('associated_token',ATA)]:vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 for kp in [AUTH,OTHER,PAYER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 vm.set_account(VAULT,Account(c.get('native',1000000),bytes(c.get('vault_length',0)),Pubkey.from_string(c.get('vault_owner',str(Pubkey.default())))))
 token=TOKEN22 if c.get('token22') else TOKEN;mint=Pubkey.from_string(c.get('mint',str(MINT)))
 md=bytearray(82);md[44]=c.get('decimals',6);md[45]=c.get('mint_initialized',1)
 length=c.get('mint_length',len(md));md=(md+bytearray(max(0,length-len(md))))[:length]
 vm.set_account(mint,Account(10**9,bytes(md),Pubkey.from_string(c.get('mint_owner',str(token)))))
 source=Pubkey.find_program_address([bytes(VAULT),bytes(token),bytes(mint)],ATA)[0];dest=Pubkey.find_program_address([bytes(AUTH.pubkey()),bytes(token),bytes(mint)],ATA)[0]
 if c.get('arbitrary_source'):source=Pubkey.from_bytes(bytes([55])*32)
 if c.get('arbitrary_dest'):dest=Pubkey.from_bytes(bytes([56])*32)
 for side,key,authority,amount in [('source',source,VAULT,c.get('tokens',12345)),('dest',dest,AUTH.pubkey(),77)]:
  vm.set_account(key,Account(0,b'',Pubkey.default()))
  if not c.get(side+'_absent'):
   td=bytearray(165);td[:32]=bytes(mint);td[32:64]=bytes(authority);td[64:72]=amount.to_bytes(8,'little');td[108]=1
   for off,val in c.get(side+'_patches',[]):td[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
   vm.set_account(key,Account(vm.minimum_balance_for_rent_exemption(165),bytes(td),Pubkey.from_string(c.get(side+'_owner',str(token)))))
 names={'user':AUTH.pubkey(),'referral_vault':VAULT,'quote_mint':mint,'vault_ata':source,'user_ata':dest,'token_program':token,'system_program':Pubkey.default(),'event_authority':EVENT,'program':PROGRAM}
 optional=['quote_mint','vault_ata','user_ata','token_program']
 for name in optional:
  if not c.get('token_mode') or name in c.get('omit',[]):names[name]=PROGRAM
 if c.get('wrong'):names[c['wrong']]=OTHER.pubkey()
 metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and c.get('readonly')!=a['name'] and names[a['name']]!=PROGRAM) for a in IX['accounts']]
 metas=metas[:c.get('account_count',len(metas))]
 payload=bytes(IX['discriminator'])+bytes.fromhex(c.get('trailing',''))
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[PAYER]+([AUTH] if any(m.is_signer and m.pubkey==AUTH.pubkey() for m in metas) else []),vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  result={}
  for name,key in {**names,'transaction_payer':PAYER.pubkey(),'actual_vault':VAULT,'actual_source':source,'actual_dest':dest}.items():
   a=vm.get_account(key)
   if a and a.executable:continue
   result[name]=None if a is None else {'data':a.data.hex(),'owner':str(a.owner),'lamports':a.lamports}
  return result
 before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r;raw=json.loads(meta.to_json())
 return {'case':c,'error':str(r.err()) if failed else None,'before':before,'after':snap(),'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw['return_data'],'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode()}
def cases():
 rows=[{'name':'native'},{'name':'native-zero','native':0},{'name':'native-one','native':1},{'name':'native-owned-fees','vault_owner':str(PROGRAM)},{'name':'native-data','vault_length':8},{'name':'token','token_mode':True},{'name':'token22','token_mode':True,'token22':True},{'name':'token-zero','token_mode':True,'tokens':0},{'name':'token-no-native','token_mode':True,'native':0},{'name':'wsol','token_mode':True,'mint':str(WSOL)},{'name':'source-absent','token_mode':True,'source_absent':True},{'name':'dest-absent','token_mode':True,'dest_absent':True}]
 rows += [{'name':'omit-'+name,'token_mode':True,'omit':[name]} for name in ['quote_mint','vault_ata','user_ata','token_program']]
 rows += [{'name':'wrong-'+name,'wrong':name} for name in ['referral_vault','system_program','event_authority','program']]
 rows += [{'name':'unsigned','unsigned':True},{'name':'readonly-user','readonly':'user'},{'name':'readonly-vault','readonly':'referral_vault'}]
 rows += [{'name':'options-'+str(n),'token_mode':True,'omit':[name for i,name in enumerate(['quote_mint','vault_ata','user_ata','token_program']) if not n & (1<<i)]} for n in range(16)]
 rows += [{'name':'rent-'+str(n),'native':n} for n in [890879,890880,890881,1000000000]]
 rows += [{'name':'arbitrary-source','token_mode':True,'arbitrary_source':True},{'name':'arbitrary-dest','token_mode':True,'arbitrary_dest':True},{'name':'token-vault-owned-fees','token_mode':True,'vault_owner':str(PROGRAM)},{'name':'token-vault-data','token_mode':True,'vault_length':8}]
 for side in ['source','dest']:
  for off,label,val in [(0,'mint',bytes(32)),(32,'authority',bytes(32)),(108,'frozen',bytes([2])),(108,'uninitialized',bytes([0]))]:rows.append({'name':side+'-'+label,'token_mode':True,side+'_patches':[(off,val.hex())]})
  rows.append({'name':side+'-owner','token_mode':True,side+'_owner':str(PROGRAM)})
 rows += [{'name':'mint-length-'+str(n),'token_mode':True,'mint_length':n} for n in [0,81,82,83]]
 rows += [{'name':'mint-uninitialized','token_mode':True,'mint_initialized':0},{'name':'mint-owner','token_mode':True,'mint_owner':str(PROGRAM)},{'name':'mint22-tokenlegacy','token_mode':True,'mint_owner':str(TOKEN22)},{'name':'mintlegacy-token22','token_mode':True,'token22':True,'mint_owner':str(TOKEN)}]
 rows += [{'name':'readonly-'+a['name'],'token_mode':True,'readonly':a['name']} for a in IX['accounts'] if a.get('writable')]
 rows += [{'name':'wrong-token-'+name,'token_mode':True,'wrong':name} for name in ['quote_mint','vault_ata','user_ata','token_program','program']]
 rows += [{'name':'extra-arguments','trailing':'01ff'},{'name':'token-zero-bad-authority','token_mode':True,'tokens':0,'source_patches':[(32,bytes(32).hex())]}]
 rows += [{'name':'source-token22-tokenlegacy','token_mode':True,'source_owner':str(TOKEN22)},{'name':'dest-token22-tokenlegacy','token_mode':True,'dest_owner':str(TOKEN22)},{'name':'source-legacy-token22','token_mode':True,'token22':True,'source_owner':str(TOKEN)},{'name':'dest-legacy-token22','token_mode':True,'token22':True,'dest_owner':str(TOKEN)}]
 rows += [{'name':'token-amount-'+str(n),'token_mode':True,'tokens':n} for n in [1,2**32,2**63,2**64-1]]
 rows += [{'name':'native-amount-'+str(n),'native':n} for n in [2**32,2**63,2**64-1]]
 rows += [{'name':'zero-missing-dest','token_mode':True,'tokens':0,'dest_absent':True},{'name':'zero-frozen-source','token_mode':True,'tokens':0,'source_patches':[(108,'02')]},{'name':'noquote-bad-token-program','token_mode':True,'omit':['quote_mint','vault_ata','user_ata'],'wrong':'token_program'},{'name':'native-rent-data','vault_length':200,'native':10000000}]
 rows += [{'name':'account-count-'+str(n),'account_count':n} for n in range(9)]
 rows += [{'name':'token-account-count-'+str(n),'token_mode':True,'account_count':n} for n in range(9)]
 rows += [{'name':'source-mint-and-authority','token_mode':True,'source_patches':[(0,bytes(64).hex())]}, {'name':'source-authority-and-program','token_mode':True,'source_patches':[(32,bytes(32).hex())],'source_owner':str(TOKEN22)}, {'name':'native-zero-bad-event','native':0,'wrong':'event_authority'},{'name':'token-zero-frozen-dest','token_mode':True,'tokens':0,'dest_patches':[(108,'02')]}]
 return rows
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__);rows=[];bad=[]
 # Read each image once, so every case and the receipt use the same bytes.
 original=ORIGINAL.read_bytes();candidate=a.candidate.read_bytes() if a.candidate else None
 for c in cases():
  x=run(c,original);y=run(c,candidate) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','before','after','events','inner','return']) if y else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 report={'scope':'Synthetic normally signed local withdraw fixtures, not full byte identity.','original_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':hashlib.sha256(candidate).hexdigest() if a.candidate else None,'cases':rows,'mismatches':bad}
 publisher.write((json.dumps(report,indent=2)+'\n').encode('utf-8'));print('Cases',len(rows),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
