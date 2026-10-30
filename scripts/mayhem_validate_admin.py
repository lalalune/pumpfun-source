#!/usr/bin/env python3
"""Local original-versus-rebuilt Mayhem admin instruction differential tests."""
import argparse, hashlib, json, pathlib, random, re
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.account import Account
from solders.instruction import Instruction, AccountMeta
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
ROOT=pathlib.Path(__file__).resolve().parents[1]
PROGRAM=Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
ADMIN=Keypair.from_seed(bytes([1])*32)
PAYER=Keypair.from_seed(bytes([2])*32)
OTHER=Pubkey.from_bytes(bytes([3])*32)
GLOBAL,BUMP=Pubkey.find_program_address([b'global-params'],PROGRAM)
EVENT,_=Pubkey.find_program_address([b'__event_authority'],PROGRAM)
DISC=hashlib.sha256(b'account:GlobalParams').digest()[:8]
OPS=['reset_sol_deployed','reset_stable_deployed','reset_state','stop_trading','resume_trading','update_admin','update_trader','update_max_sol_per_sweep','update_max_stable_per_sweep','update_global_params']
class Fixture:
 def __init__(self,binary):
  self.vm=LiteSVM().with_transaction_history(0)
  # Hash and load one byte snapshot, so the receipt names the executed image.
  image=pathlib.Path(binary).read_bytes();self.sha256=hashlib.sha256(image).hexdigest()
  self.vm.add_program(PROGRAM,image)
  for key in [ADMIN.pubkey(),PAYER.pubkey(),OTHER,EVENT]: self.vm.set_account(key,Account(10**10,b'',Pubkey.default()))
 def execute(self,c):
  data=bytes.fromhex(c['data']);kind=c.get('kind','ok');key=OTHER if kind=='wrong_pda' else GLOBAL
  uninitialized=c.get('uninitialized',False) or kind=='uninitialized'
  owner=Pubkey.default() if kind=='wrong_owner' or uninitialized else PROGRAM
  self.vm.set_account(key,Account(0 if uninitialized else 10**9,data,owner))
  sy=OTHER if kind=='wrong_system' else Pubkey.default()
  ev=OTHER if kind=='wrong_event' else EVENT
  pr=OTHER if kind=='wrong_program' else PROGRAM
  metas=[AccountMeta(ADMIN.pubkey(),kind!='unsigned_admin',kind!='readonly_admin'),AccountMeta(key,False,kind!='readonly_global'),AccountMeta(sy,False,False),AccountMeta(ev,False,False),AccountMeta(pr,False,False)]
  if kind.startswith('accounts_'):metas=metas[:int(kind.split('_')[1])]
  if kind=='extra_account':metas.append(AccountMeta(OTHER,False,False))
  payload=bytes.fromhex(c['payload']) if 'payload' in c else hashlib.sha256(('global:'+c['op']).encode()).digest()[:8]+bytes.fromhex(c.get('args',''))+bytes.fromhex(c.get('trailing',''))
  ix=Instruction(PROGRAM,payload,metas)
  signers=[PAYER]+([ADMIN] if metas and metas[0].is_signer else [])
  admin_before=self.vm.get_account(ADMIN.pubkey()).lamports
  payer_before=self.vm.get_account(PAYER.pubkey()).lamports
  r=self.vm.send_transaction(Transaction.new_signed_with_payer([ix],PAYER.pubkey(),signers,self.vm.latest_blockhash()))
  err=str(r.err()) if isinstance(r,FailedTransactionMetadata) else None
  logs=r.meta().logs() if err else r.logs()
  after=self.vm.get_account(key)
  metadata=json.loads((r.meta() if err else r).to_json())
  return {'error':err,'data':after.data.hex() if after else None,'lamports':after.lamports if after else None,'logs':logs,'owner':str(after.owner) if after else None,'admin_lamports_delta':self.vm.get_account(ADMIN.pubkey()).lamports-admin_before,'payer_lamports_delta':self.vm.get_account(PAYER.pubkey()).lamports-payer_before,'events':[l for l in logs if l.startswith('Program data:')],'inner_instructions':metadata['inner_instructions']}
def cases():
 rng=random.Random(20261024);rows=[]
 for op in OPS:
  for n in range(40):
   data=bytearray(rng.randbytes([254,255,512,1024][n%4]));data[:8]=DISC;data[48]=n%2;data[49:81]=bytes(ADMIN.pubkey())
   rows.append({'name':f'{op}-state-{n}','op':op,'data':data.hex()})
  base=bytearray(DISC+bytes(1016));base[49:81]=bytes(ADMIN.pubkey())
  for kind in ['readonly_admin','unsigned_admin','readonly_global','wrong_owner','uninitialized','wrong_pda','wrong_system','wrong_event','wrong_program','extra_account']+[f'accounts_{n}' for n in range(5)]:
   rows.append({'name':f'{op}-{kind}','op':op,'data':base.hex(),'kind':kind})
  for n in [0,1,7,8,48,49,80,253,254,255]:rows.append({'name':f'{op}-size-{n}','op':op,'data':base[:n].hex()})
  for label,offset,value in [('bad_discriminator',0,0),('bad_bool',48,2),('wrong_admin',49,0)]:
   data=bytearray(base);data[offset]=value;rows.append({'name':f'{op}-{label}','op':op,'data':data.hex()})
  rows.append({'name':f'{op}-trailing','op':op,'data':base.hex(),'trailing':'01ff0203'})
 base=bytearray(DISC+bytes(1016));base[49:81]=bytes(ADMIN.pubkey())
 for n in range(9):rows.append({'name':f'unknown-data-{n}','op':'unknown','data':base.hex(),'payload':bytes([255])*n and (bytes([255])*n).hex() or ''})
 for row in rows:
  if row['op']=='update_global_params':
   row['args']=bytes(16).hex()
  elif row['op'].startswith('update_'):
   size=32 if row['op'] in ['update_admin','update_trader'] else 8
   row['args']=rng.randbytes(size).hex()
 for op in OPS[5:9]:
  size=32 if op in ['update_admin','update_trader'] else 8
  for n in range(size):rows.append({'name':f'{op}-short-args-{n}','op':op,'data':base.hex(),'args':bytes(n).hex()})
  for val in [0,255]:rows.append({'name':f'{op}-extreme-{val}','op':op,'data':base.hex(),'args':bytes([val]*size).hex()})
 widths=[4,4,8,8,8,8,1,8,8,8,8,8,8,8,8,8]
 for n in range(160):
  args=b''.join(bytes([1])+rng.randbytes(width) if rng.randrange(2) else bytes([0]) for width in widths)
  data=bytearray(rng.randbytes([254,1024][n%2]));data[:8]=DISC;data[48]=n%2;data[49:81]=bytes(ADMIN.pubkey())
  rows.append({'name':f'update_global_params-options-{n}','op':'update_global_params','data':data.hex(),'args':args.hex()})
 for i,width in enumerate(widths):
  for value in [0,1,255]:
   args=bytes(i)+bytes([1])+bytes([value])*width+bytes(15-i)
   rows.append({'name':f'update_global_params-field-{i}-{value}','op':'update_global_params','data':base.hex(),'args':args.hex()})
  args=bytearray(16);args[i]=2
  rows.append({'name':f'update_global_params-bad-option-{i}','op':'update_global_params','data':base.hex(),'args':args.hex()})
 for value in [0,1,255,2**32-2,2**32-1]:
  data=bytearray(base);data[162:166]=value.to_bytes(4,'little')
  rows.append({'name':f'update_global_params-version-{value}','op':'update_global_params','data':data.hex(),'args':(bytes([1])+bytes([255])*4+bytes(15)).hex()})
 for n in range(16):rows.append({'name':f'update_global_params-short-{n}','op':'update_global_params','data':base.hex(),'args':bytes(n).hex()})
 for kind in ['ok','readonly_admin','unsigned_admin','readonly_global','wrong_pda','wrong_system','wrong_event','wrong_program','extra_account']+[f'accounts_{n}' for n in range(5)]:
  rows.append({'name':f'initialize_global_params-{kind}','op':'initialize_global_params','data':'','uninitialized':True,'kind':kind})
 for n in [0,8,254,1024]:
  rows.append({'name':f'initialize_global_params-existing-{n}','op':'initialize_global_params','data':base[:n].hex()})
 rows.append({'name':'initialize_global_params-trailing','op':'initialize_global_params','data':'','uninitialized':True,'trailing':'010203ff'})
 return rows
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);a=ap.parse_args()
 original=ROOT/'evidence/original/mayhem/deployed.so';o=Fixture(original);b=Fixture(a.candidate);rows=[];mismatches=[]
 for c in cases():
  x=o.execute(c);y=b.execute(c);equal=all(x[k]==y[k] for k in ['error','data','lamports','events','inner_instructions','owner','admin_lamports_delta','payer_lamports_delta'])
  rows.append({'case':c,'original':x,'candidate':y,'equal':equal})
  if not equal:mismatches.append(c['name'])
 report={'scope':'Eleven complete admin instruction paths; other instructions absent. Local synthetic state; compared error, account data, lamports, emitted events and inner instructions, not complete log byte identity or full program identity.','original_sha256':o.sha256,'candidate_sha256':b.sha256,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'programs/mayhem/Cargo.toml',ROOT/'programs/mayhem/Cargo.lock',ROOT/'programs/mayhem/src/lib.rs',pathlib.Path(__file__).resolve()]},'case_count':len(rows),'mismatches':mismatches,'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'cases':len(rows),'mismatches':mismatches}));raise SystemExit(bool(mismatches))
