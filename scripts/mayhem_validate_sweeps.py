#!/usr/bin/env python3
"""Differential tests of both Mayhem sweep paths using captured dependencies."""
import argparse
from mayhem_validate_fee_recipient import *
from solders.clock import Clock
class SweepFixture:
 def __init__(self,binary):
  self.vm=LiteSVM().with_transaction_history(0);image=pathlib.Path(binary).read_bytes();self.sha256=hashlib.sha256(image).hexdigest();self.vm.add_program(PROGRAM,image)
  for name,key in DEPENDENCIES.items():self.vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 def execute(self,c):
  vm=self.vm;kind=c.get('kind','ok');token=TOKEN2022 if c.get('token2022') else TOKEN;mint=WSOL if c.get('native',True) else OTHER;op=c.get('op','sweep_fees')
  vm.set_clock(Clock(100,0,0,0,c.get('timestamp',100)))
  for key in [PAYER.pubkey(),ADMIN.pubkey(),EVENT]:vm.set_account(key,Account(10**10,b'',Pubkey.default()))
  data=bytearray(DISC+bytes(246));data[49:81]=bytes(OTHER if kind=='wrong_admin' else ADMIN.pubkey());data[81:113]=bytes(OTHER if kind=='wrong_trader' else ADMIN.pubkey());data[174:182]=c.get('limit',1000000).to_bytes(8,'little');data[246:254]=c.get('limit',1000000).to_bytes(8,'little')
  
  if 'global_offset' in c:data[c['global_offset']:c['global_offset']+8]=c.get('global_value',200000).to_bytes(8,'little')
  vm.set_account(GLOBAL,Account(10**9,bytes(data),PROGRAM));vm.set_account(mint,Account(10**9,bytes(44)+bytes([9,1])+bytes(36),token))
  remaining=[]
  for index in range(9):
   owner,bump=Pubkey.find_program_address([b'fee-recipient',bytes([index])],PROGRAM)
   if index==8:owner=ADMIN.pubkey()
   else:
    d=hashlib.sha256(b'account:FeeRecipient').digest()[:8]+bytes([bump,index])+bytes.fromhex(c.get('opaque',bytes(32).hex()))
    vm.set_account(owner,Account(c.get('lamports',10000000),d,PROGRAM))
   key,_=Pubkey.find_program_address([bytes(owner),bytes(token),bytes(mint)],ATA);td=bytearray(165);td[:32]=bytes(mint);td[32:64]=bytes(owner);td[108]=1
   amount=(c.get('tokens',0)+index*c.get('token_step',0)) if index<8 else 0;td[64:72]=amount.to_bytes(8,'little')
   if mint==WSOL:td[109:113]=(1).to_bytes(4,'little');td[113:121]=(2039280).to_bytes(8,'little')
   vm.set_account(key,Account(2039280+amount if mint==WSOL else 2039280,bytes(td),token))
   if index<8:remaining.extend([owner,key])
   else:destination=key
  if kind=='duplicate_pair':remaining=remaining[:2]*8
  if kind=='swapped_pairs':remaining=remaining[2:4]+remaining[:2]+remaining[4:]
  if kind in ['wrong_bump','wrong_index','wrong_disc','short','wrong_owner','bad_last']:
   key=remaining[14 if kind=='bad_last' else 0];a=vm.get_account(key);d=bytearray(a.data);owner=a.owner
   if kind=='wrong_bump':d[8]^=1
   if kind=='wrong_index':d[9]=7
   if kind in ['wrong_disc','bad_last']:d[0]^=1
   if kind=='short':d=d[:9]
   if kind=='wrong_owner':owner=Pubkey.default()
   vm.set_account(key,Account(a.lamports,bytes(d),owner))
  if kind in ['wrong_token_mint','wrong_token_owner','wrong_token_program','uninitialized_token','short_token']:
   key=remaining[1];a=vm.get_account(key);d=bytearray(a.data);owner=a.owner
   if kind=='wrong_token_mint':d[:32]=bytes(EVENT)
   if kind=='wrong_token_owner':d[32:64]=bytes(ADMIN.pubkey())
   if kind=='wrong_token_program':owner=PROGRAM
   if kind=='uninitialized_token':d[108]=0
   if kind=='short_token':d=d[:164]
   vm.set_account(key,Account(a.lamports,bytes(d),owner))
  if kind=='missing_destination':vm.set_account(destination,Account(0,b'',Pubkey.default()))
  keys=[ADMIN.pubkey(),GLOBAL,mint,destination,Pubkey.default(),token,ATA,EVENT,PROGRAM]+remaining
  metas=[AccountMeta(k,i==0 and kind!='unsigned_admin',(i in [0,1,3] or i>=9) and kind!=f'readonly_{i}') for i,k in enumerate(keys)]
  if kind.startswith('accounts_'):metas=metas[:int(kind.split('_')[1])]
  r=vm.send_transaction(Transaction.new_signed_with_payer([Instruction(PROGRAM,hashlib.sha256(('global:'+op).encode()).digest()[:8],metas)],PAYER.pubkey(),[PAYER]+([ADMIN] if metas and metas[0].is_signer else []),vm.latest_blockhash()));err=str(r.err()) if isinstance(r,FailedTransactionMetadata) else None;meta=r.meta() if err else r;raw=json.loads(meta.to_json())
  return dict(error=err,accounts={str(k):None if vm.get_account(k) is None else vm.get_account(k).to_json() for k in keys if k not in [PROGRAM,TOKEN,TOKEN2022,ATA]},events=[x for x in meta.logs() if x.startswith('Program data:')],inner=raw['inner_instructions'],return_data=raw['return_data'],logs=meta.logs())
rows=[]
for op in ['sweep_fees','sweep_fees_admin']:
 for native in [False,True]:
  for tokens in [0,100000,2000000]:
   for limit in [0,1,1000000,2**64-1]:rows.append(dict(op=op,native=native,tokens=tokens,limit=limit))
 for kind in ['wrong_admin','wrong_trader','unsigned_admin','duplicate_pair','swapped_pairs','wrong_bump','wrong_index','wrong_disc','short','wrong_owner','bad_last','missing_destination']+[f'readonly_{n}' for n in [0,1,3,9,10]]+[f'accounts_{n}' for n in range(26)]:rows.append(dict(op=op,kind=kind))
 for lamports in [0,1,1183199,1183200,1183201]:rows.append(dict(op=op,lamports=lamports))
 for native in [False,True]:rows.append(dict(op=op,native=native,token2022=True,tokens=100000))
for op in ['sweep_fees','sweep_fees_admin']:
 for native in [False,True]:
  for offset in [16,24,32,40,129,146,154,166,174,182,190,198,222,230,246]:rows.append(dict(op=op,native=native,global_offset=offset))
  for offset in [0,8,16,24]:
   for value in [0,1,99,100,101,2**63,2**64-1]:
    d=bytearray(32);d[offset:offset+8]=value.to_bytes(8,'little');rows.append(dict(op=op,native=native,opaque=d.hex()))
import random
rng=random.Random(2929)
for op in ['sweep_fees','sweep_fees_admin']:
 for native in [False,True]:
  for kind in ['wrong_token_mint','wrong_token_owner','wrong_token_program','uninitialized_token','short_token','wrong_bump','wrong_index','bad_last','duplicate_pair']:
   for tokens in [0,100000]:rows.append(dict(op=op,native=native,kind=kind,tokens=tokens))
  for n in range(75):rows.append(dict(op=op,native=native,opaque=rng.randbytes(32).hex(),timestamp=rng.randrange(-1000,1000),limit=rng.randrange(10000000),tokens=rng.randrange(2000000),token_step=rng.randrange(20000),lamports=rng.randrange(100000,10000000)))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);a=ap.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,pathlib.Path(__file__),extra_inputs=REPORT_INPUTS)
 original=ROOT/'evidence/original/mayhem/deployed.so';o=SweepFixture(original);b=SweepFixture(a.candidate);results=[];failures=[]
 for index,c in enumerate(rows):
  x=o.execute(c);y=b.execute(c);equal=all(x[k]==y[k] for k in ['error','accounts','events','inner','return_data']);results.append(dict(case=c,original=x,candidate=y,equal=equal))
  if not equal:failures.append(index)
 report={'scope':'Both sweep paths with exact captured dependency ELFs; synthetic accounts and configuration. Partial program reconstruction.','original_sha256':o.sha256,'candidate_sha256':b.sha256,'dependency_sha256':{name:hashlib.sha256((ROOT/f'evidence/dependencies/{name}/deployed.so').read_bytes()).hexdigest() for name in DEPENDENCIES},'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'programs/mayhem/Cargo.toml',ROOT/'programs/mayhem/Cargo.lock',ROOT/'programs/mayhem/src/lib.rs',pathlib.Path(__file__).resolve(),ROOT/'scripts/mayhem_validate_admin.py',ROOT/'scripts/mayhem_validate_fee_recipient.py']},'case_count':len(results),'mismatches':failures,'cases':results}
 publisher.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'cases':len(results),'mismatches':failures}));raise SystemExit(bool(failures))
