#!/usr/bin/env python3
"""Differentially execute Mayhem's permissionless account extension path locally."""
import argparse,hashlib,json,pathlib,random
from solders.clock import Clock
from mayhem_validate_admin import *
TYPES={'GlobalParams':318,'FeeRecipient':74,'MayhemState':170}
class ExtendFixture:
 def __init__(self,binary):
  self.vm=LiteSVM().with_transaction_history(0);image=pathlib.Path(binary).read_bytes();self.sha256=hashlib.sha256(image).hexdigest();self.vm.add_program(PROGRAM,image)
 def execute(self,c):
  vm=self.vm;kind=c.get('kind','ok');key=OTHER if kind=='other_address' else GLOBAL
  for k in [PAYER.pubkey(),ADMIN.pubkey(),OTHER,EVENT]:vm.set_account(k,Account(10**10,b'',Pubkey.default()))
  vm.set_account(key,Account(c.get('lamports',10**7),bytes.fromhex(c['data']),Pubkey.default() if kind=='wrong_owner' else PROGRAM))
  vm.set_clock(Clock(100,1,0,0,c.get('timestamp',0)))
  keys=[key,ADMIN.pubkey(),OTHER if kind=='wrong_system' else Pubkey.default(),OTHER if kind=='wrong_event' else EVENT,OTHER if kind=='wrong_program' else PROGRAM]
  metas=[AccountMeta(k,i==1 and kind!='unsigned_user',(i==0 and kind!='readonly_account') or (i==1 and kind!='readonly_user')) for i,k in enumerate(keys)]
  if kind.startswith('accounts_'):metas=metas[:int(kind.split('_')[1])]
  if kind=='extra_account':metas.append(AccountMeta(OTHER,False,False))
  payload=hashlib.sha256(b'global:extend_account').digest()[:8]+(b'\xff\x01\x02' if kind=='trailing' else b'')
  ix=Instruction(PROGRAM,payload,metas);signers=[PAYER]+([ADMIN] if len(metas)>1 and metas[1].is_signer else [])
  r=vm.send_transaction(Transaction.new_signed_with_payer([ix],PAYER.pubkey(),signers,vm.latest_blockhash()));err=str(r.err()) if isinstance(r,FailedTransactionMetadata) else None;meta=r.meta() if err else r;raw=json.loads(meta.to_json());accounts={}
  for name,k in [('account',key),('user',ADMIN.pubkey()),('payer',PAYER.pubkey())]:
   a=vm.get_account(k);accounts[name]=None if a is None else {'data':a.data.hex(),'owner':str(a.owner),'lamports':a.lamports}
  return {'error':err,'accounts':accounts,'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner_instructions':raw['inner_instructions'],'return_data':raw['return_data'],'logs':meta.logs()}
def cases():
 rng=random.Random(13579);rows=[]
 for name,target in TYPES.items():
  disc=hashlib.sha256(('account:'+name).encode()).digest()[:8]
  for size in sorted(set(range(0,12))|{target-1,target,target+1,1024}):
   data=(disc+rng.randbytes(1024))[:size]
   for lamports in [1,10**7]:rows.append({'name':f'{name}-size-{size}-balance-{lamports}','data':data.hex(),'lamports':lamports,'timestamp':rng.randrange(-10000000,10000000)})
  data=disc+rng.randbytes(8)
  for kind in ['readonly_account','readonly_user','unsigned_user','wrong_owner','wrong_system','wrong_event','wrong_program','other_address','trailing','extra_account']+[f'accounts_{n}' for n in range(5)]:
   for lamports in [1,10**7]:rows.append({'name':f'{name}-{kind}-{lamports}','data':data.hex(),'lamports':lamports,'kind':kind})
  for timestamp in [-(2**63),-1,0,1,2**63-1]:rows.append({'name':f'{name}-clock-{timestamp}','data':data.hex(),'timestamp':timestamp})
 for i in range(100):rows.append({'name':f'unknown-discriminator-{i}','data':rng.randbytes(32).hex()})
 return rows
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);a=ap.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,pathlib.Path(__file__),extra_inputs=REPORT_INPUTS);original=ROOT/'evidence/original/mayhem/deployed.so';o=ExtendFixture(original);b=ExtendFixture(a.candidate);rows=[];failures=[]
 for c in cases():
  x=o.execute(c);y=b.execute(c);equal=all(x[k]==y[k] for k in ['error','accounts','events','inner_instructions','return_data']);rows.append({'case':c,'original':x,'candidate':y,'equal':equal})
  if not equal:failures.append(c['name'])
 report={'scope':'Original-versus-rebuilt extension instruction; synthetic types, ownership, funding and clock. This is not full program identity.','original_sha256':o.sha256,'candidate_sha256':b.sha256,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'programs/mayhem/Cargo.toml',ROOT/'programs/mayhem/Cargo.lock',ROOT/'programs/mayhem/src/lib.rs',pathlib.Path(__file__).resolve(),ROOT/'scripts/mayhem_validate_admin.py']},'case_count':len(rows),'mismatches':failures,'cases':rows};publisher.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'cases':len(rows),'mismatches':failures}));raise SystemExit(bool(failures))
