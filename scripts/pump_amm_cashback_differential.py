import sys,struct,json,base64,pathlib,hashlib
sys.path.insert(0,'scripts')
from pump_amm_liquidity_differential import *
from pump_amm_reusable_harness import pin_program
from solders.transaction import Transaction
ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');USER=OUTSIDER.pubkey();U=Pubkey.find_program_address([b'user_volume_accumulator',bytes(USER)],PROGRAM)[0];DEST=Pubkey.from_bytes(bytes([237])*32)
ORIGINAL=ROOT/'evidence/original/pump_amm/deployed.so'
def run(c,binary=ORIGINAL):
 h=acquire_harness(pin_program(binary));vm=h.vm;vm.with_sigverify(True);vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,n in [(TOKEN,'spl_token'),(TOKEN22,'spl_token_2022')]:vm.add_program_from_file(pid,ROOT/'evidence/dependencies'/n/'deployed.so')
 tp=TOKEN22 if c.get('token22') else TOKEN;mint=quote if not c.get('non_native') else base;v=Pubkey.find_program_address([bytes(U),bytes(tp),bytes(mint)],ATA)[0]
 row=f['accounts']['quote_mint' if mint==quote else 'base_mint'];vm.set_account(mint,Account(row['lamports'],base64.b64decode(row['data_base64']),tp))
 ud=hashlib.sha256(b'account:UserVolumeAccumulator').digest()[:8]+bytes(USER)+struct.pack('<BQQQqBQQ',1,5,7,20,0,1,c.get('earned',11),c.get('claimed',13))
 vm.set_account(U,Account(c.get('accumulator_lamports',10**9),ud.ljust(137,b'\0'),PROGRAM));amount=c.get('amount',1000)
 vm.set_account(v,Account(min(2**64-1,amount+2039280),token(mint,U,amount,mint==quote),tp));vm.set_account(DEST,Account(2039280,token(mint,USER,0,mint==quote),tp))
 ix=next(i for i in IDL['instructions'] if i['name']=='claim_cashback');keys=[USER,U,mint,tp,v,DEST,Pubkey.default(),EVENT,PROGRAM];metas=[AccountMeta(k,bool(a.get('signer')),bool(a.get('writable'))) for k,a in zip(keys,ix['accounts'])]
 if c.get('stored_other_user'):
  a=vm.get_account(U);d=bytearray(a.data);d[8:40]=bytes(PAYER.pubkey());vm.set_account(U,Account(a.lamports,bytes(d),a.owner))
 if 'mutate_index' in c:
  key=keys[c['mutate_index']];a=vm.get_account(key);d=bytearray(a.data)
  if 'offset' in c:
   value=bytes.fromhex(c['value']);d[c['offset']:c['offset']+len(value)]=value
  if 'length' in c:d=d[:c['length']]+bytes(max(0,c['length']-len(d)))
  vm.set_account(key,Account(c.get('lamports',a.lamports),bytes(d),Pubkey.from_string(c.get('owner',str(a.owner)))))
 if 'wrong_index' in c:
  i=c['wrong_index'];old=keys[i];new=Pubkey.from_bytes(bytes([238])*32);a=vm.get_account(old)
  if a:vm.set_account(new,a)
  metas[i]=AccountMeta(new,False,metas[i].is_writable);keys.append(new)
 if 'readonly' in c:
  i=c['readonly'];metas[i]=AccountMeta(metas[i].pubkey,False,False)
 metas=metas[:c.get('account_count',len(metas))]
 def snap():
  out={}
  for k in keys+[PAYER.pubkey()]:
   a=vm.get_account(k)
   if a is None or not a.executable:out[str(k)]=None if a is None else {'data':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
  return out
 before=snap();data=bytes(ix['discriminator'])+bytes.fromhex(c.get('trailing',''));data=data[:c.get('payload_length',len(data))];tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,metas)],PAYER.pubkey(),[PAYER],vm.latest_blockhash());assert all(tx.verify_with_results());r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);m=r.meta() if failed else r
 return {'case':c,'error':str(r.err()) if failed else None,'before':before,'after':snap(),'logs':m.logs(),'inner':json.loads(m.to_json())['inner_instructions'],'tx':base64.b64encode(bytes(tx)).decode(),'signature_verified':True,'events':[l for l in m.logs() if l.startswith('Program data: ')]}

def cases():
 out=[{}, {'stored_other_user':True}]
 for field,values in [('amount',[0,1,1000,10**12,2**64-2039281,2**64-1]),('earned',[0,1,2**64-1]),('claimed',[0,1,2**64-1]),('accumulator_lamports',[0,1,2000000])]:
  for val in values:out.append({field:val})
 for native in [False,True]:
  for token22 in [False,True]:
   for amount in [0,1,1000]:out.append({'non_native':native,'token22':token22,'amount':amount})
 for i,lengths in [(1,[0,7,8,40,41,73,74,81,82,89,90,136,137,200]),(2,[0,7,81,82,83]),(4,[0,7,164,165,166,200]),(5,[0,7,164,165,166,200])]:
  for length in lengths:out.append({'mutate_index':i,'length':length})
  for owner in [Pubkey.default(),PROGRAM,TOKEN,TOKEN22]:out.append({'mutate_index':i,'owner':str(owner)})
 for i in [1,4,5]:
  for off,value in ([(0,bytes(8)),(8,bytes(32)),(40,b'\2'),(73,b'\2')] if i==1 else [(0,bytes(32)),(32,bytes(32)),(64,bytes(8)),(108,b'\0'),(108,b'\2')]):
   for amount in [0,1000]:out.append({'mutate_index':i,'offset':off,'value':value.hex(),'amount':amount})
 for owner in [Pubkey.default(),PROGRAM,TOKEN]:out.append({'mutate_index':0,'owner':str(owner)})
 for length in [0,1,100]:out.append({'mutate_index':0,'length':length})
 for i in range(9):out.append({'wrong_index':i});out.append({'readonly':i})
 for n in range(9):out.append({'account_count':n})
 for n in range(8):out.append({'payload_length':n})
 out.append({'trailing':'010203'})
 return out
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();rows=[]
 for c in cases():
  x,y=run(c),run(c,a.candidate);diff=[k for k in x if k!='logs' and x[k]!=y[k]];rows.append({'case':c,'original':x,'candidate':y,'diff':diff})
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 d={'scope':'Bounded normal-signature AMM cashback fixtures; compare full recorded state, inner calls, events and errors; no original-program identity/security claim.','original_sha256':sha(pin_program(ORIGINAL)),'candidate_sha256':sha(pin_program(a.candidate)),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['diff']],'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in d.items() if k!='cases'}));assert not d['mismatches']
