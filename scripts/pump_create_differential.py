#!/usr/bin/env python3
"""Offline creation reconstruction with ordinary mint and payer signatures."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,base64,gzip,hashlib,json,struct
from pathlib import Path
from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
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
 if c.get('wrong'):names[c['wrong']]=OTHER.pubkey()
 metas=[AccountMeta(names[a['name']],a.get('signer',False) and c.get('unsigned')!=a['name'],a.get('writable',False) and c.get('readonly')!=a['name']) for a in ix['accounts']][:c.get('account_count',100)]
 payload=bytes(ix['discriminator'])+string(c.get('name','Synthetic Coin'))+string(c.get('symbol','SYNTH'))+string(c.get('uri','https://example.invalid/metadata.json'))+bytes(Pubkey.from_string(c.get('creator',str(USER.pubkey()))))
 if c.get('instruction')=='create_v2':payload+=bytes([0])+bytes.fromhex(c.get('optional_args',''))
 payload=(payload+bytes.fromhex(c.get('trailing','')))[:c.get('payload_length',100000)]
 for name,mut in c.get('mutations',{}).items():
  key=names[name];a=vm.get_account(key) or Account(0,b'',Pubkey.default());d=bytearray(a.data)
  for off,val in mut.get('patches',[]):d[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
  size=mut.get('length',len(d));d=(d+bytes(max(0,size-len(d))))[:size];vm.set_account(key,Account(mut.get('lamports',a.lamports),bytes(d),Pubkey.from_string(mut.get('owner',str(a.owner)))))
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
def cases():
 out=[{'case':'base'},{'case':'zero-creator','creator':str(Pubkey.default())},{'case':'other-creator','creator':str(OTHER.pubkey())},{'case':'uninitialized','global_patches':[(8,'00')]}]
 for name,limit in [('name',32),('symbol',10),('uri',200)]:
  for n in [0,limit,limit+1]:out.append({'case':name+'-'+str(n),name:'x'*n})
 for a in next(x for x in IDL['instructions'] if x['name']=='create')['accounts']:
  if not a.get('signer'):out.append({'case':'wrong-'+a['name'],'wrong':a['name']})
  if a.get('writable'):out.append({'case':'readonly-'+a['name'],'readonly':a['name']})
 out.append({'case':'unsigned-mint','unsigned':'mint'})
 for field in ['mint','bonding_curve','associated_bonding_curve','metadata']:
  for amount in [1,10000000]:out.append({'case':f'prefund-{field}-{amount}','mutations':{field:{'lamports':amount}}})
  out.append({'case':'existing-'+field,'mutations':{field:{'lamports':10000000,'length':82,'owner':str(TOKEN)}}})
 for amount in [0,1000,20000000,21000000]:out.append({'case':'user-funds-'+str(amount),'mutations':{'user':{'lamports':amount}}})
 for field in ['mint','mint_authority','bonding_curve','associated_bonding_curve','global','metadata','event_authority']:
  out.append({'case':'zero-creator-wrong-'+field,'creator':str(Pubkey.default()),'wrong':field})
 for off in [73,81,89,97]:
  for n in [0,1,2**64-1]:out.append({'case':f'global-u64-{off}-{n}','global_patches':[(off,struct.pack('<Q',n).hex())]})
 for n in range(14):out.append({'case':'accounts-'+str(n),'account_count':n})
 for n in [0,7,8,12,24,70]:out.append({'case':'payload-'+str(n),'payload_length':n})
 out.append({'case':'trailing','trailing':'ffff'})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 publisher=PumpReport(a.output,ROOT,a.candidate,__file__,extra_inputs=[ROOT/'evidence/dependencies/token_metadata/deployed.so',ROOT/'evidence/original/mayhem/deployed.so'])
 rows=[];bad=[]
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;diff=[k for k in ['before','after','error','events','inner','return'] if y is not None and x[k]!=y[k]];rows.append({'case':c,'original':x,'candidate':y,'diff':diff})
  if diff:bad.append(c)
 report={'original_sha256':hashlib.sha256(pin_program(ORIGINAL).read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'scope':'Normally signed synthetic offline creation, no byte identity claim.','cases':rows,'mismatches':bad,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};publisher.write((gzip.compress(json.dumps(report,indent=2).encode(),mtime=0) if a.output.suffix=='.gz' else json.dumps(report,indent=2).encode()));print(len(rows),'cases',len(bad),'mismatches')
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
