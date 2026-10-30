#!/usr/bin/env python3
"""Compare complete Mayhem SOL admin withdrawal calls with the original."""
import argparse,hashlib,json,pathlib,random
from mayhem_validate_admin import *
from solders.clock import Clock
VAULT,BUMP=Pubkey.find_program_address([b'sol-vault'],PROGRAM)
class WithdrawFixture:
 def __init__(self,binary):
  self.vm=LiteSVM().with_transaction_history(0);image=pathlib.Path(binary).read_bytes();self.sha256=hashlib.sha256(image).hexdigest();self.vm.add_program(PROGRAM,image)
 def execute(self,c):
  vm=self.vm;vm.set_clock(Clock(100,0,0,0,c.get('timestamp',0)));kind=c.get('kind','ok');key=OTHER if kind=='wrong_vault' else VAULT
  for k in [PAYER.pubkey(),ADMIN.pubkey(),OTHER,EVENT]:vm.set_account(k,Account(10**10,b'',Pubkey.default()))
  data=bytearray.fromhex(c['data'])
  if kind=='wrong_admin':data[49:81]=bytes(OTHER)
  vm.set_account(GLOBAL,Account(10**9,bytes(data),Pubkey.default() if kind=='wrong_global_owner' else PROGRAM))
  vm.set_account(key,Account(c.get('balance',10**9),b'\x01' if kind=='vault_has_data' else b'',PROGRAM if kind=='wrong_vault_owner' else Pubkey.default()))
  keys=[ADMIN.pubkey(),GLOBAL,key,OTHER if kind=='wrong_system' else Pubkey.default()]
  metas=[AccountMeta(k,i==0 and kind!='unsigned_admin',i<3 and kind!=['readonly_admin','readonly_global','readonly_vault'][i]) for i,k in enumerate(keys)]
  if kind.startswith('accounts_'):metas=metas[:int(kind.split('_')[1])]
  if kind=='extra_accounts':metas.extend([AccountMeta(EVENT,False,False),AccountMeta(PROGRAM,False,False)])
  payload=hashlib.sha256(b'global:withdraw_admin').digest()[:8]+c.get('amount',1).to_bytes(8,'little')[:c.get('arg_length',8)]+(b'\xff\x01' if kind=='trailing' else b'')
  ix=Instruction(PROGRAM,payload,metas);signers=[PAYER]+([ADMIN] if metas and metas[0].is_signer else [])
  r=vm.send_transaction(Transaction.new_signed_with_payer([ix],PAYER.pubkey(),signers,vm.latest_blockhash()));err=str(r.err()) if isinstance(r,FailedTransactionMetadata) else None;meta=r.meta() if err else r;raw=json.loads(meta.to_json());accounts={}
  for name,k in [('global',GLOBAL),('vault',key),('admin',ADMIN.pubkey()),('payer',PAYER.pubkey())]:
   a=vm.get_account(k);accounts[name]=None if a is None else {'data':a.data.hex(),'owner':str(a.owner),'lamports':a.lamports}
  return {'error':err,'accounts':accounts,'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner_instructions':raw['inner_instructions'],'return_data':raw['return_data'],'logs':meta.logs()}
def cases():
 rng=random.Random(24680);rows=[];base=bytearray(DISC+bytes(246));base[49:81]=bytes(ADMIN.pubkey())
 for balance in [0,1,890879,890880,10**9,2**63]:
  for amount in sorted({0,1,max(0,balance-1),balance,balance+1,2**64-1}):rows.append({'name':f'balance-{balance}-amount-{amount}','data':base.hex(),'balance':balance,'amount':amount})
 for n in range(100):
  data=bytearray(rng.randbytes([254,1024][n%2]));data[:8]=DISC;data[48]=n%2;data[49:81]=bytes(ADMIN.pubkey());rows.append({'name':f'random-state-{n}','data':data.hex(),'amount':rng.randrange(2*10**9)})
 for kind in ['readonly_admin','readonly_global','readonly_vault','unsigned_admin','wrong_admin','wrong_global_owner','wrong_vault','wrong_vault_owner','vault_has_data','wrong_system','extra_accounts','trailing']+[f'accounts_{n}' for n in range(4)]:
  for amount in [0,1]:rows.append({'name':f'{kind}-{amount}','data':base.hex(),'kind':kind,'amount':amount})
 for n in range(8):rows.append({'name':f'short-args-{n}','data':base.hex(),'arg_length':n})
 for last in [-(2**63),-1,0,1,2**63-1]:
  for interval in [-(2**63),-1,0,1,2**63-1]:
   for now in [-1,0,1,2**63-1]:
    data=bytearray(base);data[138:146]=last.to_bytes(8,'little',signed=True);data[154:162]=interval.to_bytes(8,'little',signed=True)
    rows.append({'name':f'rate-{last}-{interval}-{now}','data':data.hex(),'timestamp':now,'amount':0})
 for now in [14,15,16]:
  data=bytearray(base);data[138:146]=(5).to_bytes(8,'little',signed=True);data[154:162]=(10).to_bytes(8,'little',signed=True)
  rows.append({'name':f'rate-boundary-{now}','data':data.hex(),'timestamp':now})
 return rows
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);a=ap.parse_args();original=ROOT/'evidence/original/mayhem/deployed.so';o=WithdrawFixture(original);b=WithdrawFixture(a.candidate);rows=[];failures=[]
 for c in cases():
  x=o.execute(c);y=b.execute(c);equal=all(x[k]==y[k] for k in ['error','accounts','events','inner_instructions','return_data']);rows.append({'case':c,'original':x,'candidate':y,'equal':equal})
  if not equal:failures.append(c['name'])
 report={'scope':'Original-versus-rebuilt SOL withdrawal; System CPI, synthetic authorization, balances and account state. Not full program identity.','original_sha256':o.sha256,'candidate_sha256':b.sha256,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'programs/mayhem/Cargo.toml',ROOT/'programs/mayhem/Cargo.lock',ROOT/'programs/mayhem/src/lib.rs',pathlib.Path(__file__).resolve(),ROOT/'scripts/mayhem_validate_admin.py']},'case_count':len(rows),'mismatches':failures,'cases':rows};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'cases':len(rows),'mismatches':failures}));raise SystemExit(bool(failures))
