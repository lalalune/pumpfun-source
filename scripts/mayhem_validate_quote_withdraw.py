#!/usr/bin/env python3
"""Compare Mayhem quote withdrawals with captured token/ATA dependencies."""
import argparse,random
from mayhem_validate_fee_recipient import *
from solders.clock import Clock
VAULT,BUMP=Pubkey.find_program_address([b'sol-vault'],PROGRAM)
class QuoteWithdrawFixture:
 def __init__(self,binary):
  self.vm=LiteSVM().with_transaction_history(0);image=pathlib.Path(binary).read_bytes();self.sha256=hashlib.sha256(image).hexdigest();self.vm.add_program(PROGRAM,image)
  for name,key in DEPENDENCIES.items():self.vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 def execute(self,c):
  vm=self.vm;kind=c.get('kind','ok');token=TOKEN2022 if c.get('token2022') else TOKEN;mint=WSOL if c.get('native',True) else OTHER
  vm.set_clock(Clock(100,0,0,0,c.get('timestamp',100)))
  for key in [PAYER.pubkey(),ADMIN.pubkey(),EVENT,VAULT]:vm.set_account(key,Account(10**10,b'',Pubkey.default()))
  data=bytearray.fromhex(c['data']) if 'data' in c else bytearray(DISC+bytes(246));data[49:81]=bytes(OTHER if kind=='wrong_admin' else ADMIN.pubkey());data[238:246]=c.get('last',0).to_bytes(8,'little',signed=True);data[230:238]=c.get('interval',0).to_bytes(8,'little',signed=True)
  vm.set_account(GLOBAL,Account(10**9,bytes(data),PROGRAM));vm.set_account(mint,Account(10**9,bytes(44)+bytes([9,1])+bytes(36),token))
  ac=[]
  for owner in [VAULT,ADMIN.pubkey()]:
   key,_=Pubkey.find_program_address([bytes(owner),bytes(token),bytes(mint)],ATA);td=bytearray(165);td[:32]=bytes(mint);td[32:64]=bytes(owner);td[108]=1
   amount=c.get('balance',1000000) if owner==VAULT else 0;td[64:72]=amount.to_bytes(8,'little')
   if mint==WSOL:td[109:113]=(1).to_bytes(4,'little');td[113:121]=(2039280).to_bytes(8,'little')
   vm.set_account(key,Account(2039280+amount if mint==WSOL else 2039280,bytes(td),token));ac.append(key)
  keys=[ADMIN.pubkey(),GLOBAL,VAULT,mint,*ac,token,ATA,Pubkey.default()]
  if kind=='missing_admin_ata':vm.set_account(ac[1],Account(0,b'',Pubkey.default()))
  if kind=='missing_vault_ata':vm.set_account(ac[0],Account(0,b'',Pubkey.default()))
  if kind=='wrong_vault':keys[2]=EVENT
  if kind=='wrong_system':keys[8]=EVENT
  if kind=='wrong_ata_program':keys[7]=EVENT
  if kind in ['wrong_vault_ata','wrong_admin_ata']:
   idx=4 if kind=='wrong_vault_ata' else 5;a=vm.get_account(keys[idx]);vm.set_account(EVENT,a);keys[idx]=EVENT
  metas=[AccountMeta(k,i==0 and kind!='unsigned_admin',i in [0,1,2,4,5] and kind!=f'readonly_{i}') for i,k in enumerate(keys)]
  if kind.startswith('accounts_'):metas=metas[:int(kind.split('_')[1])]
  payload=hashlib.sha256(b'global:withdraw_quote_admin').digest()[:8]+c.get('amount',1000).to_bytes(8,'little')[:c.get('arg_length',8)]
  r=vm.send_transaction(Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[PAYER]+([ADMIN] if metas and metas[0].is_signer else []),vm.latest_blockhash()));err=str(r.err()) if isinstance(r,FailedTransactionMetadata) else None;meta=r.meta() if err else r;raw=json.loads(meta.to_json())
  return dict(error=err,accounts={str(k):None if vm.get_account(k) is None else vm.get_account(k).to_json() for k in keys[:6]},events=[x for x in meta.logs() if x.startswith('Program data:')],inner=raw['inner_instructions'],return_data=raw['return_data'],logs=meta.logs())
rows=[]
for token2022 in [False,True]:
 for native in [False,True]:
  for kind in ['ok','wrong_admin','unsigned_admin','wrong_vault','wrong_system','wrong_ata_program','missing_admin_ata','missing_vault_ata','wrong_vault_ata','wrong_admin_ata']+[f'readonly_{n}' for n in range(9)]+[f'accounts_{n}' for n in range(9)]:rows.append(dict(kind=kind,token2022=token2022,native=native))
for last in [-(2**63),-1,0,1,2**63-1]:
 for interval in [-(2**63),-1,0,1,2**63-1]:
  for now in [-1,0,1,2**63-1]:rows.append(dict(last=last,interval=interval,timestamp=now,amount=0))
for amount in [0,1,999999,1000000,1000001,2**64-1]:rows.append(dict(amount=amount))
for n in range(8):rows.append(dict(arg_length=n))
rng=random.Random(159)
for n in range(100):
 data=bytearray(rng.randbytes([254,512,1024][n%3]));data[:8]=DISC;data[48]=n%2
 rows.append(dict(data=data.hex(),amount=rng.randrange(2000000),last=rng.randrange(-100,100),interval=rng.randrange(-100,100),timestamp=rng.randrange(-100,100)))
for now in [14,15,16]:rows.append(dict(last=5,interval=10,timestamp=now))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);a=ap.parse_args()
 original=ROOT/'evidence/original/mayhem/deployed.so';o=QuoteWithdrawFixture(original);b=QuoteWithdrawFixture(a.candidate);results=[];failures=[]
 for index,c in enumerate(rows):
  x=o.execute(c);y=b.execute(c);equal=all(x[k]==y[k] for k in ['error','accounts','events','inner','return_data']);results.append(dict(case=c,original=x,candidate=y,equal=equal))
  if not equal:failures.append(index)
 report={'scope':'Quote withdrawal with exact captured dependency ELFs; synthetic accounts and configuration. Partial program reconstruction.','original_sha256':o.sha256,'candidate_sha256':b.sha256,'dependency_sha256':{name:hashlib.sha256((ROOT/f'evidence/dependencies/{name}/deployed.so').read_bytes()).hexdigest() for name in DEPENDENCIES},'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'programs/mayhem/Cargo.toml',ROOT/'programs/mayhem/Cargo.lock',ROOT/'programs/mayhem/src/lib.rs',pathlib.Path(__file__).resolve(),ROOT/'scripts/mayhem_validate_admin.py',ROOT/'scripts/mayhem_validate_fee_recipient.py']},'case_count':len(results),'mismatches':failures,'cases':results}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'cases':len(results),'mismatches':failures}));raise SystemExit(bool(failures))
