#!/usr/bin/env python3
"""FeeConfig administration transfer with ordinary signatures and synthetic state."""
from fees_config_differential import *
class TransferFixture(Fixture):
 def run(self,c):
  data=bytearray(encode([(0,(1,2,3))],[(0,(4,5,6))]).ljust(c.get('allocation',4097),b'\0'));owner=PROGRAM;key=CONFIG;config_program=CONFIG_PROGRAM;admin=AUTH;event=EVENT;program=PROGRAM;mutation=c.get('mutation','none')
  if mutation=='owner':owner=Pubkey.default()
  if mutation=='key':key=Pubkey.from_bytes(bytes([44])*32)
  if mutation=='bump':data[8]^=1
  if mutation=='discriminator':data[0]^=1
  if mutation=='admin':admin=OTHER
  if mutation=='config_program':config_program=OTHER.pubkey()
  if mutation=='event':event=OTHER.pubkey()
  if mutation=='program':program=Pubkey.default()
  if mutation.startswith('length:'):data=data[:int(mutation.split(':')[1])]
  if mutation.startswith('normal_count:'):data[65:69]=int(mutation.split(':')[1]).to_bytes(4,'little')
  self.vm.set_account(key,Account(10**9,bytes(data),owner));self.vm.set_account(CONFIG_PROGRAM,Account(10**9,b'',Pubkey.default()))
  new_admin=Pubkey.from_string(c['new_admin'])
  metas=[AccountMeta(admin.pubkey(),mutation!='unsigned',False),AccountMeta(key,False,mutation!='readonly'),AccountMeta(new_admin,False,False),AccountMeta(config_program,False,False),AccountMeta(event,False,False),AccountMeta(program,False,False)]
  if mutation.startswith('accounts:'):metas=metas[:int(mutation.split(':')[1])]
  disc=bytes(next(i['discriminator'] for i in IDL['instructions'] if i['name']=='update_admin'));before=self.vm.get_account(PAYER.pubkey()).lamports;signers=[PAYER,admin] if any(m.pubkey==admin.pubkey() and m.is_signer for m in metas) else [PAYER]
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,disc+bytes.fromhex(c.get('arg','')),metas)],PAYER.pubkey(),signers,self.vm.latest_blockhash());result=self.vm.send_transaction(tx);failed=isinstance(result,FailedTransactionMetadata);meta=result.meta() if failed else result;after=self.vm.get_account(key)
  return {'error':str(result.err()) if failed else None,'data_hex':after.data.hex() if after else None,'lamports':after.lamports if after else None,'owner':str(after.owner) if after else None,'payer_delta':self.vm.get_account(PAYER.pubkey()).lamports-before,'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner_instructions':json.loads(meta.to_json())['inner_instructions'],'logs':meta.logs()}
def cases():
 out=[]
 for new in [Pubkey.default(),AUTH.pubkey(),OTHER.pubkey(),PAYER.pubkey(),CONFIG,PROGRAM]:
  for size in [2512,4073,4097]:out.append({'name':str(new)+'-allocation-'+str(size),'new_admin':str(new),'allocation':size})
 for mutation in ['owner','key','bump','discriminator','admin','config_program','event','program','unsigned','readonly']+['accounts:'+str(n) for n in range(6)]+['length:'+str(n) for n in [0,7,8,9,40,69,2511,2512,4072,4073,4096,4097]]+['normal_count:'+str(n) for n in [0,1,60,2**32-1]]:
  out.append({'name':mutation,'new_admin':str(OTHER.pubkey()),'mutation':mutation})
 for n in [1,2,8,32,64,256]:out.append({'name':'extra-args-'+str(n),'new_admin':str(OTHER.pubkey()),'arg':'ff'*n})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();orig=ROOT/'evidence/original/pump_fees/deployed.so';o=TransferFixture(orig);b=TransferFixture(a.candidate) if a.candidate else None;rows=[];bad=[]
 for c in cases():
  x=o.run(c);y=b.run(c) if b else None;match=all(x[k]==y[k] for k in ['error','data_hex','lamports','owner','payer_delta','events','inner_instructions']) if b else None;rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 report={'scope':'update_admin on synthetic FeeConfig with actual local signatures, errors/state/balances/events/inner instructions. No historical authority control or byte identity claimed.','original_sha256':o.program_sha256,'candidate_sha256':b.program_sha256 if b else None,'case_count':len(rows),'mismatches':bad,'cases':rows};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'case_count':len(rows),'mismatches':bad}))
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
