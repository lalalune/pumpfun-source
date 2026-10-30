#!/usr/bin/env python3
"""Permissionless FeeConfig resizing using normally signed offline transactions."""
from fees_config_differential import *
class ExtendFixture(Fixture):
 def run(self,c):
  for wallet in [AUTH,OTHER,PAYER]:self.vm.set_account(wallet.pubkey(),Account(10**12,b'',Pubkey.default()))
  mutation=c.get('mutation','none');allocation=c.get('allocation',2512);data=bytearray(encode([(0,(1,2,3))],[(0,(4,5,6))]).ljust(allocation,b'\0')[:allocation]);owner=PROGRAM;key=CONFIG;config_program=CONFIG_PROGRAM;event=EVENT;program=PROGRAM;system=Pubkey.default();user=AUTH
  if mutation=='owner':owner=Pubkey.default()
  if mutation=='foreign_owner':owner=CONFIG_PROGRAM
  if mutation=='key':key=Pubkey.from_bytes(bytes([44])*32)
  if mutation=='noncanonical' and len(data)>8:
   for candidate_bump in range(256):
    if candidate_bump==BUMP:continue
    try:key=Pubkey.create_program_address([b'fee_config',bytes(CONFIG_PROGRAM),bytes([candidate_bump])],PROGRAM)
    except Exception:continue
    data[8]=candidate_bump;break
  if mutation=='bump' and len(data)>8:data[8]^=1
  if mutation=='discriminator' and data:data[0]^=1
  if mutation=='admin':user=OTHER
  if mutation=='config_program':config_program=OTHER.pubkey()
  if mutation=='event':event=OTHER.pubkey()
  if mutation=='program':program=Pubkey.default()
  if mutation=='system':system=OTHER.pubkey()
  if mutation=='malformed' and len(data)>=69:data[65:69]=bytes([255])*4
  self.vm.set_account(key,Account(c.get('lamports',10**9),bytes(data),owner));self.vm.set_account(CONFIG_PROGRAM,Account(10**9,b'',Pubkey.default()))
  if 'user_lamports' in c:self.vm.set_account(user.pubkey(),Account(c['user_lamports'],b'',Pubkey.default()))
  metas=[AccountMeta(key,False,mutation!='readonly'),AccountMeta(user.pubkey(),mutation!='unsigned',mutation!='user_readonly'),AccountMeta(config_program,False,False),AccountMeta(system,False,False),AccountMeta(event,False,False),AccountMeta(program,False,False)]
  if mutation.startswith('accounts:'):metas=metas[:int(mutation.split(':')[1])]
  disc=bytes(next(x['discriminator'] for x in IDL['instructions'] if x['name']=='extend_fee_config'));payload=disc+bytes.fromhex(c.get('arg',''))
  before=[(self.vm.get_account(k.pubkey()).lamports if self.vm.get_account(k.pubkey()) else 0) for k in [AUTH,OTHER,PAYER]];signers=[PAYER,user] if any(m.pubkey==user.pubkey() and m.is_signer for m in metas) else [PAYER]
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),signers,self.vm.latest_blockhash());result=self.vm.send_transaction(tx);failed=isinstance(result,FailedTransactionMetadata);meta=result.meta() if failed else result;after=self.vm.get_account(key)
  balances=[(self.vm.get_account(k.pubkey()).lamports if self.vm.get_account(k.pubkey()) else 0) for k in [AUTH,OTHER,PAYER]]
  return {'error':str(result.err()) if failed else None,'data_hex':after.data.hex() if after else None,'lamports':after.lamports if after else None,'owner':str(after.owner) if after else None,'balance_deltas':[a-b for a,b in zip(balances,before)],'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner_instructions':json.loads(meta.to_json())['inner_instructions'],'logs':meta.logs()}
def cases():
 out=[]
 for size in [0,7,8,9,40,65,69,96,97,137,177,2511,2512,2513,4072,4073,4096,4097,4098,5000]:
  for lamports in [0,1,10**6,10**9]:out.append({'name':f'size-{size}-funding-{lamports}','allocation':size,'lamports':lamports})
 for mutation in ['owner','foreign_owner','key','noncanonical','bump','discriminator','admin','config_program','event','program','system','readonly','user_readonly','unsigned','malformed']+['accounts:'+str(n) for n in range(6)]:
  for size in [8,2512,4073,4097,5000]:
   for lamports in [1,10**9]:out.append({'name':f'{mutation}-{size}-{lamports}','mutation':mutation,'allocation':size,'lamports':lamports})
 for funds in [0,1,10**6,29405999,29406000,10**9]:out.append({'name':f'user-funds-{funds}','user_lamports':funds,'lamports':1})
 out.append({'name':'extra-arguments','arg':'ff'*128})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();o=ExtendFixture(ROOT/'evidence/original/pump_fees/deployed.so');b=ExtendFixture(a.candidate) if a.candidate else None;rows=[];failures=[]
 for c in cases():
  x=o.run(c);y=b.run(c) if b else None;match=all(x[k]==y[k] for k in ['error','data_hex','lamports','owner','balance_deltas','events','inner_instructions']) if b else None;rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:failures.append(c['name'])
 report={'scope':'extend_fee_config, normally signed permissionless resizing in offline LiteSVM. State/errors/balances/events/inner CPI compared; no full identity or security sign-off.','original_sha256':o.program_sha256,'candidate_sha256':b.program_sha256 if b else None,'case_count':len(rows),'mismatches':failures,'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'case_count':len(rows),'mismatches':failures[:30]}));assert not failures
if __name__=='__main__':main()
