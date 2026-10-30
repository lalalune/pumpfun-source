#!/usr/bin/env python3
"""Compare original/candidate fee-recipient creation with captured CPI programs."""
import argparse,hashlib,json,pathlib
from mayhem_validate_admin import *
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN2022=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL=Pubkey.from_string('So11111111111111111111111111111111111111112')
DEPENDENCIES={'spl_token':TOKEN,'spl_token_2022':TOKEN2022,'associated_token':ATA}
class RecipientFixture:
 def __init__(self,binary):
  self.vm=LiteSVM().with_transaction_history(0)
  image=pathlib.Path(binary).read_bytes();self.sha256=hashlib.sha256(image).hexdigest();self.vm.add_program(PROGRAM,image)
  for name,key in DEPENDENCIES.items():self.vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 def execute(self,c):
  vm=self.vm;index=c.get('index',0);kind=c.get('kind','ok');token=TOKEN2022 if c.get('token2022') else TOKEN
  mint=OTHER if kind=='other_mint' else WSOL
  recipient,bump=Pubkey.find_program_address([b'fee-recipient',bytes([index])],PROGRAM)
  if kind=='wrong_recipient':recipient=Pubkey.from_bytes(bytes([4])*32)
  recipient_ata,_=Pubkey.find_program_address([bytes(recipient),bytes(token),bytes(mint)],ATA)
  if kind=='wrong_ata':recipient_ata=Pubkey.from_bytes(bytes([5])*32)
  data=bytearray(DISC+bytes(246));data[49:81]=bytes(ADMIN.pubkey())
  if kind=='wrong_admin':data[49:81]=bytes(OTHER)
  vm.set_account(GLOBAL,Account(10**9,bytes(data),PROGRAM))
  for key in [recipient,recipient_ata]:vm.set_account(key,Account(0,b'',Pubkey.default()))
  vm.set_account(mint,Account(10**9,bytes(44)+bytes([9,1])+bytes(36),Pubkey.default() if kind=='wrong_mint_owner' else token))
  for key in [ADMIN.pubkey(),PAYER.pubkey(),EVENT]:vm.set_account(key,Account(10**10,b'',Pubkey.default()))
  keys=[ADMIN.pubkey(),mint,recipient,recipient_ata,GLOBAL,Pubkey.default(),token,ATA]
  if kind=='wrong_system':keys[5]=EVENT
  if kind=='wrong_token':keys[6]=EVENT
  if kind=='wrong_associated_program':keys[7]=EVENT
  metas=[AccountMeta(key,i==0 and kind!='unsigned_admin',i in [0,2,3] or (i==4 and kind!='readonly_global')) for i,key in enumerate(keys)]
  if kind=='readonly_admin':metas[0]=AccountMeta(keys[0],True,False)
  if kind=='readonly_recipient':metas[2]=AccountMeta(keys[2],False,False)
  if kind=='readonly_ata':metas[3]=AccountMeta(keys[3],False,False)
  if kind.startswith('accounts_'):metas=metas[:int(kind.split('_')[1])]
  if kind=='extra_accounts':metas.extend([AccountMeta(EVENT,False,False),AccountMeta(PROGRAM,False,False)])
  payload=hashlib.sha256(b'global:initialize_fee_recipient').digest()[:8]+(b'' if kind=='missing_arg' else bytes([index]))+(b'\xff\x00' if kind=='trailing_args' else b'')
  ix=Instruction(PROGRAM,payload,metas);signers=[PAYER]+([ADMIN] if metas and metas[0].is_signer else [])
  r=vm.send_transaction(Transaction.new_signed_with_payer([ix],PAYER.pubkey(),signers,vm.latest_blockhash()));err=str(r.err()) if isinstance(r,FailedTransactionMetadata) else None;meta=r.meta() if err else r;raw=json.loads(meta.to_json())
  accounts={}
  for name,key in [('admin',ADMIN.pubkey()),('payer',PAYER.pubkey()),('global',GLOBAL),('recipient',recipient),('ata',recipient_ata),('mint',mint)]:
   account=vm.get_account(key);accounts[name]=None if account is None else {'data':account.data.hex(),'owner':str(account.owner),'lamports':account.lamports}
  return {'error':err,'accounts':accounts,'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner_instructions':raw['inner_instructions'],'return_data':raw['return_data'],'logs':meta.logs()}
def cases():
 rows=[{'name':f'index-{n}','index':n} for n in range(256)]
 for token2022 in [False,True]:
  for kind in ['ok','readonly_admin','unsigned_admin','readonly_recipient','readonly_ata','readonly_global','wrong_recipient','wrong_ata','wrong_admin','other_mint','wrong_mint_owner','wrong_system','wrong_token','wrong_associated_program','extra_accounts','missing_arg','trailing_args']+[f'accounts_{n}' for n in range(8)]:rows.append({'name':f'{"token2022" if token2022 else "token"}-{kind}','index':3,'kind':kind,'token2022':token2022})
 return rows
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);a=ap.parse_args()
 original=ROOT/'evidence/original/mayhem/deployed.so';o=RecipientFixture(original);b=RecipientFixture(a.candidate);rows=[];failures=[]
 for c in cases():
  x=o.execute(c);y=b.execute(c);equal=all(x[k]==y[k] for k in ['error','accounts','events','inner_instructions','return_data']);rows.append({'case':c,'original':x,'candidate':y,'equal':equal})
  if not equal:failures.append(c['name'])
 report={'scope':'Fee-recipient initialization against exact captured token/ATA dependency ELFs. Local synthetic state; program incomplete.','original_sha256':o.sha256,'candidate_sha256':b.sha256,'dependency_sha256':{name:hashlib.sha256((ROOT/f'evidence/dependencies/{name}/deployed.so').read_bytes()).hexdigest() for name in DEPENDENCIES},'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'programs/mayhem/Cargo.toml',ROOT/'programs/mayhem/Cargo.lock',ROOT/'programs/mayhem/src/lib.rs',pathlib.Path(__file__).resolve(),ROOT/'scripts/mayhem_validate_admin.py']},'case_count':len(rows),'mismatches':failures,'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'cases':len(rows),'mismatches':failures}));raise SystemExit(bool(failures))
