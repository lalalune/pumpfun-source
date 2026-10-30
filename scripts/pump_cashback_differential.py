#!/usr/bin/env python3
"""Offline ordinary-signer cashback accounting reconstruction fixtures."""
import argparse,base64,gzip,hashlib,json,struct
from solders.rent import Rent
import pump_trade_fixture as f
R=f.R; P=f.Pubkey.from_string(f.x['program']);USER=f.Keypair.from_seed(bytes([229])*32);PAYER=f.Keypair.from_seed(bytes([228])*32)
TOKEN=f.Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=f.Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=f.Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');WSOL=f.Pubkey.from_string('So11111111111111111111111111111111111111112');QUOTE=f.Pubkey(bytes([71])*32)
IDL=json.loads((R/'evidence/upstream/pump.json').read_text(encoding='utf-8'));IX={x['name']:x for x in IDL['instructions']}
def run(c,binary=None):
 vm=f.LiteSVM().with_transaction_history(0).with_sigverify(True);vm.add_program_from_file(P,binary or R/'evidence/original/pump/deployed.so')
 for name in ['spl_token','spl_token_2022','associated_token']:
  cap=json.loads((R/f'evidence/dependencies/{name}/capture.json').read_text());vm.add_program_from_file(f.Pubkey.from_string(cap['program']),R/f'evidence/dependencies/{name}/deployed.so')
 user=USER.pubkey();vol=f.Pubkey.find_program_address([b'user_volume_accumulator',bytes(user)],P)[0];mint=QUOTE if c.get('token_quote') else WSOL;tp=TOKEN22 if c.get('token22') else TOKEN
 keys={'user':user,'user_volume_accumulator':vol,'system_program':f.Pubkey.default(),'event_authority':f.Pubkey.find_program_address([b'__event_authority'],P)[0],'program':P,'quote_mint':mint,'quote_token_program':tp,'associated_token_program':ATA,'associated_user_volume_accumulator':f.Pubkey.find_program_address([bytes(vol),bytes(tp),bytes(mint)],ATA)[0],'associated_quote_user':f.Pubkey.find_program_address([bytes(user),bytes(tp),bytes(mint)],ATA)[0]}
 vm.set_account(PAYER.pubkey(),f.Account(10**11,b'',f.Pubkey.default()));vm.set_account(user,f.Account(10**8,b'',f.Pubkey.default()))
 d=bytearray(hashlib.sha256(b'account:UserVolumeAccumulator').digest()[:8]+bytes(user)+bytes(66));struct.pack_into('<Q',d,74,c.get('earned',1000));struct.pack_into('<Q',d,82,c.get('claimed',200));struct.pack_into('<Q',d,90,c.get('stable_earned',3000));struct.pack_into('<Q',d,98,c.get('stable_claimed',400));vm.set_account(vol,f.Account(c.get('lamports',10000000),bytes(d),P))
 d=bytearray(82);struct.pack_into('<Q',d,36,10**12);d[44]=6;d[45]=1
 if 'transfer_fee_bps' in c:d.extend(bytes(83)+bytes([1])+struct.pack('<HH',1,108)+bytes(72)+struct.pack('<QQH',0,1000000,c['transfer_fee_bps'])*2)
 vm.set_account(mint,f.Account(10**9,bytes(d),tp))
 for name,auth,amount in [('associated_user_volume_accumulator',vol,c.get('token_balance',5000)),('associated_quote_user',user,100)]:
  d=bytearray(165);d[:32]=bytes(mint);d[32:64]=bytes(auth);struct.pack_into('<Q',d,64,amount);d[108]=1
  if 'transfer_fee_bps' in c:d.extend(bytes([2])+struct.pack('<HHQ',2,8,0))
  vm.set_account(keys[name],f.Account(10**8,bytes(d),tp))
 for name,spec in c.get('mutations',{}).items():
  key=keys[name];ac=vm.get_account(key);d=bytearray(ac.data)
  for off,val in spec.get('bytes',[]):d[off]=val
  for off,val in spec.get('u64',[]):struct.pack_into('<Q',d,off,val)
  d=d[:spec.get('length',len(d))];d.extend(bytes(max(0,spec.get('length',len(d))-len(d))));vm.set_account(key,f.Account(spec.get('lamports',ac.lamports),bytes(d),f.Pubkey.default() if spec.get('system_owner') else ac.owner,spec.get('executable',ac.executable)))
 for name in c.get('absent',[]):vm.set_account(keys[name],f.Account(0,b'',f.Pubkey.default()))
 ix=IX['claim_cashback_v2' if c.get('v2') else 'claim_cashback'];metas=[f.AccountMeta(keys[a['name']],a.get('signer',False),a.get('writable',False)) for a in ix['accounts']]
 for name in c.get('wrong_keys',[]):
  i=next(i for i,a in enumerate(ix['accounts']) if a['name']==name);old=metas[i];key=f.Pubkey(bytes([110+i])*32);ac=vm.get_account(old.pubkey)
  if ac and not ac.executable:vm.set_account(key,ac)
  metas[i]=f.AccountMeta(key,False,old.is_writable)
 for name in c.get('readonly',[]):
  i=next(i for i,a in enumerate(ix['accounts']) if a['name']==name);old=metas[i];metas[i]=f.AccountMeta(old.pubkey,old.is_signer,False)
 tx=f.Transaction.new_signed_with_payer([f.Instruction(P,bytes(ix['discriminator']),metas)],PAYER.pubkey(),[PAYER],vm.latest_blockhash());tx.verify();res=vm.send_transaction(tx);failed=isinstance(res,f.FailedTransactionMetadata);meta=res.meta() if failed else res
 def snap(a):return None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':None if a.executable else base64.b64encode(a.data).decode(),'executable':a.executable}
 return {'error':str(res.err()) if failed else None,'accounts':{str(k):snap(vm.get_account(k)) for k in tx.message.account_keys if k!=P},'events':[l[14:] for l in meta.logs() if l.startswith('Program data: ')],'inner':json.loads(meta.to_json())['inner_instructions'],'return_data':json.loads(meta.to_json()).get('return_data'),'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'signatures_verified':True}
def cases():
 out=[]
 for mode in [{},{'v2':True},{'v2':True,'token_quote':True},{'v2':True,'token_quote':True,'token22':True}]:
  for m in [{},{'earned':0},{'earned':100000000},{'claimed':2**64-1},{'lamports':0},{'lamports':100},{'lamports':1628640},{'token_balance':0},{'stable_earned':0},{'stable_claimed':2**64-1}]:out.append(dict(mode,**m,name=f'mode{mode}-state{m}'))
  for n in [0,7,8,40,73,74,81,82,89,90,97,98,105,106]:out.append(dict(mode,name=f'mode{mode}-len{n}',mutations={'user_volume_accumulator':{'length':n}}))
  for mut in [{'system_owner':True},{'bytes':[[0,0]]},{'bytes':[[8,99]]},{'bytes':[[40,2]]}]:out.append(dict(mode,name=f'mode{mode}-mut{mut}',mutations={'user_volume_accumulator':mut}))
  for name in ['user_volume_accumulator','event_authority','system_program']:out.append(dict(mode,name=f'mode{mode}-key{name}',wrong_keys=[name]))
  for name in ['user','user_volume_accumulator']:out.append(dict(mode,name=f'mode{mode}-readonly{name}',readonly=[name]))
 for mode in [{'v2':True},{'v2':True,'token_quote':True},{'v2':True,'token_quote':True,'token22':True}]:
  for name in ['quote_mint','quote_token_program','associated_token_program','associated_user_volume_accumulator','associated_quote_user']:
   out.append(dict(mode,name=f'v2key{mode}-{name}',wrong_keys=[name]))
   out.append(dict(mode,name=f'v2absent{mode}-{name}',absent=[name]))
  for name in ['quote_mint','associated_user_volume_accumulator','associated_quote_user']:
   for mut in [{'system_owner':True},{'length':0},{'bytes':[[32,99]]},{'bytes':[[0,99]]}]:out.append(dict(mode,name=f'v2mut{mode}-{name}-{mut}',mutations={name:mut}))
  for name in ['associated_user_volume_accumulator','associated_quote_user']:out.append(dict(mode,name=f'v2readonly{mode}-{name}',readonly=[name]))
 for mode in [{},{'v2':True},{'v2':True,'token_quote':True},{'v2':True,'token_quote':True,'token22':True}]:
  for n in [107,128,256]:out.append(dict(mode,name=f'extended{mode}-{n}',mutations={'user_volume_accumulator':{'length':n}}))
  out.append(dict(mode,name=f'zerobalanceoverflow{mode}',lamports=100,token_balance=0,claimed=2**64-1,stable_claimed=2**64-1))
  for n in [73,40]:out.append(dict(mode,name=f'badbool{mode}-{n}',mutations={'user_volume_accumulator':{'bytes':[[n,2]]}}))
 for mode in [{'v2':True,'token_quote':True},{'v2':True,'token_quote':True,'token22':True}]:
  for name in ['quote_mint','associated_quote_user']:
   for mut in [{'system_owner':True},{'length':0},{'bytes':[[32,99]]}]:out.append(dict(mode,name=f'zero-invalid-{mode}-{name}-{mut}',token_balance=0,mutations={name:mut}))
 for bps in [0,1,100,10000]:
  for amount in [0,1,5000]:out.append({'name':f'transferfee-{bps}-{amount}','v2':True,'token_quote':True,'token22':True,'transfer_fee_bps':bps,'token_balance':amount})
 # Exact accumulation boundaries, with zero transfers retaining the early return.
 for label,mode in [('native',{'v2':True}),('token',{'v2':True,'token_quote':True}),('token22',{'v2':True,'token_quote':True,'token22':True})]:
  for amount in [0,1,5000]:
   for claimed in sorted({0,2**64-1-amount,min(2**64-1,2**64-amount),2**64-1}):
    balance={'token_balance':amount,'stable_claimed':claimed} if mode.get('token_quote') else {'lamports':Rent.default().minimum_balance(106)+amount,'claimed':claimed}
    out.append({**mode,**balance,'name':f'counter-boundary-{label}-{amount}-{claimed}'})

 # Payment must fail before accumulation when both destinations overflow.
 for claimed in [0,2**64-1]:
  out.append({'name':f'payment-priority-native-{claimed}','v2':True,'claimed':claimed,'mutations':{'user':{'lamports':2**64-1}}})
 for token22 in [False,True]:
  out.append({'name':f'payment-priority-token-{token22}','v2':True,'token_quote':True,'token22':token22,'stable_claimed':2**64-1,'mutations':{'associated_quote_user':{'u64':[[64,2**64-1]]}}})
 return out

def panic_messages(result):
 return [line.split("\n",1)[-1] for line in result["logs"] if line.startswith("Program log: panicked at ")]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=f.pathlib.Path);ap.add_argument('--output',type=f.pathlib.Path,required=True);a=ap.parse_args();rows=[]
 for c in cases():
  o=run(c);r={'case':c,'original':o}
  if a.candidate:
   b=run(c,a.candidate);diff=[k for k in ['error','accounts','events','inner','return_data'] if o[k]!=b[k]]
   if panic_messages(o)!=panic_messages(b):diff.append('panic_message')
   r.update(candidate=b,match=not diff,different_fields=diff)
  rows.append(r)
 d={'scope':'Ordinary test payer signatures; synthetic offline cashback balances, genuine program CPIs; no incentive administration or token incentive claims. Byte identity unproven.','original_sha256':hashlib.sha256((R/'evidence/original/pump/deployed.so').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest() if a.candidate else None,'harness_sha256':hashlib.sha256(f.pathlib.Path(__file__).read_bytes()).hexdigest(),'case_count':len(rows),'cases':rows,'mismatches':[i for i,r in enumerate(rows) if r.get('match') is False]};a.output.parent.mkdir(parents=True,exist_ok=True);raw=(json.dumps(d,indent=2)+'\n').encode();a.output.write_bytes(gzip.compress(raw,mtime=0) if a.output.suffix=='.gz' else raw);print(json.dumps({'cases':len(rows),'mismatches':d['mismatches']}))
 if d['mismatches']:raise SystemExit(1)
if __name__=='__main__':main()
