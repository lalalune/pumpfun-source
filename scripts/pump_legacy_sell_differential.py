#!/usr/bin/env python3
"""Offline legacy sell recovery: normally signed synthetic transactions, captured dependencies."""
import argparse,base64,hashlib,json,struct,gzip
import pump_trade_fixture as f
R=f.R;P=f.Pubkey.from_string(f.x['program']);USER=f.Keypair.from_seed(bytes([231])*32)
INITIAL={k:f.vm.get_account(k) for k in f.msg.account_keys}
CURVE=f.Pubkey.from_string(f.x['accounts']['curve']);GLOBAL=f.Pubkey.from_string(f.x['accounts']['global']);FEE=f.Pubkey.from_string(f.x['accounts']['fee_config'])
IDL=json.loads((R/'evidence/upstream/pump.json').read_text(encoding='utf-8'));IX=next(i for i in IDL['instructions'] if i['name']=='sell')
def run(c,binary=None):
 vm=f.LiteSVM().with_transaction_history(0)
 for name in ['pump','pump_fees']:
  cap=json.loads((R/f'evidence/original/{name}/capture.json').read_text());vm.add_program_from_file(f.Pubkey.from_string(cap['program']),binary if name=='pump' and binary else R/f'evidence/original/{name}/deployed.so')
 for name in ['spl_token','spl_token_2022','associated_token']:
  cap=json.loads((R/f'evidence/dependencies/{name}/capture.json').read_text());vm.add_program_from_file(f.Pubkey.from_string(cap['program']),R/f'evidence/dependencies/{name}/deployed.so')
 for k,a in INITIAL.items():
  if a is not None and not a.executable:vm.set_account(k,a)
 data=bytearray(INITIAL[CURVE].data)
 for off,val in c.get('curve_bytes',[]):data[off]=val
 for off,val in c.get('curve_u64',[]):struct.pack_into('<Q',data,off,val)
 vm.set_account(CURVE,f.Account(INITIAL[CURVE].lamports,bytes(data),P))
 creator=f.Pubkey(data[49:81]);vault=f.Pubkey.find_program_address([b'creator-vault',bytes(creator)],P)[0]
 recipient=f.Pubkey(INITIAL[GLOBAL].data[(483 if c.get('reserved') else 41):(515 if c.get('reserved') else 73)]);v3=f.ixs[-1].accounts
 keys={'global':GLOBAL,'fee_recipient':recipient,'mint':v3[1].pubkey,'bonding_curve':CURVE,'associated_bonding_curve':v3[6].pubkey,'associated_user':v3[9].pubkey,'user':USER.pubkey(),'system_program':f.Pubkey.default(),'creator_vault':vault,'token_program':v3[3].pubkey,'event_authority':f.Pubkey.find_program_address([b'__event_authority'],P)[0],'program':P,'fee_config':FEE,'fee_program':f.Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')}
 if c.get('legacy_token'):
  token=f.Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');keys['token_program']=token
  for name in ['mint','associated_bonding_curve','associated_user']:
   key=keys[name];ac=vm.get_account(key);d=ac.data[:82 if name=='mint' else 165]
   if name=='associated_bonding_curve':keys[name]=f.Pubkey.find_program_address([bytes(CURVE),bytes(token),bytes(keys['mint'])],f.Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'))[0]
   vm.set_account(keys[name],f.Account(ac.lamports,d,token))
 for name,spec in c.get('account_mutations',{}).items():
  key=keys[name];a=vm.get_account(key);d=bytearray(a.data)
  for off,val in spec.get('bytes',[]):d[off]=val
  for off,val in spec.get('u64',[]):struct.pack_into('<Q',d,off,val)
  d=d[:spec.get('length',len(d))]
  vm.set_account(key,f.Account(spec.get('lamports',a.lamports),bytes(d),f.Pubkey.default() if spec.get('system_owner') else a.owner))
 if 'recipient_slot' in c:
  gd=vm.get_account(GLOBAL).data;off=162+c['recipient_slot']*32;recipient=f.Pubkey(gd[off:off+32]);keys['fee_recipient']=recipient
 for k in [recipient,vault]:
  if vm.get_account(k) is None:vm.set_account(k,f.Account(10**7,b'',f.Pubkey.default()))
 metas=[f.AccountMeta(keys[a['name']],a.get('signer',False),a.get('writable',False)) for a in IX['accounts']]
 if c.get('cashback_account'):
  metas.append(f.AccountMeta(v3[11].pubkey,False,True))
 if c.get('remaining',True):
  v2=f.Pubkey.find_program_address([b'bonding-curve-v2',bytes(keys['mint'])],P)[0]
  vm.set_account(v2,f.Account(10**7,bytes(data)[:c.get('v2_len',len(data))],f.Pubkey.default() if c.get('v2_system') else P))
  metas.append(f.AccountMeta(v2,False,False))
  if not c.get('omit_buyback'):metas.append(f.AccountMeta(v3[13].pubkey,False,True))
 for name in c.get('wrong_keys',[]):
  idx=next(i for i,a in enumerate(IX['accounts']) if a['name']==name);old=metas[idx];key=f.Pubkey(bytes([77+idx])*32);ac=vm.get_account(old.pubkey)
  if ac is not None:vm.set_account(key,f.Account(10**7,ac.data,ac.owner,ac.executable) if ac.executable else ac)
  metas[idx]=f.AccountMeta(key,old.is_signer,old.is_writable)
 for name in c.get('readonly',[]):
  i=next(i for i,a in enumerate(IX['accounts']) if a['name']==name);metas[i]=f.AccountMeta(metas[i].pubkey,metas[i].is_signer,False)
 trade=f.Instruction(P,bytes(IX['discriminator'])+struct.pack('<QQ',c.get('amount',500000000),c.get('minimum',0)),metas)
 tx=f.Transaction.new_signed_with_payer([*f.ixs[:-1],trade],USER.pubkey(),[USER],vm.latest_blockhash());tx.verify()
 before={str(k):vm.get_account(k) for k in tx.message.account_keys if k!=P};res=vm.send_transaction(tx);failed=isinstance(res,f.FailedTransactionMetadata);meta=res.meta() if failed else res
 def snap(a):return None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':None if a.executable else base64.b64encode(a.data).decode(),'executable':a.executable}
 return {'error':str(res.err()) if failed else None,'accounts':{str(k):snap(vm.get_account(k)) for k in tx.message.account_keys if k!=P},'before':{k:snap(v) for k,v in before.items()},'events':[l[14:] for l in meta.logs() if l.startswith('Program data: ')],'return_data':json.loads(meta.to_json()).get('return_data'),'inner':json.loads(meta.to_json())['inner_instructions'],'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'signatures_verified':True}
def cases():
 base=[{'name':'base'},{'name':'zero','amount':0},{'name':'min','minimum':10**12},{'name':'complete','curve_bytes':[[48,1]]},{'name':'mayhem','curve_bytes':[[81,1]],'reserved':True},{'name':'cashback','curve_bytes':[[82,1]]},{'name':'holder','curve_bytes':[[124,1]]},{'name':'missing_remaining','remaining':False},{'name':'missing_buyback','omit_buyback':True}]
 base += [{'name':f'v2_len_{n}','v2_len':n} for n in [0,1,7,8,32,81]]
 base += [{'name':'cashback_valid','curve_bytes':[[82,1]],'cashback_account':True}]
 base += [{'name':'v2_system','v2_system':True},{'name':'insufficient_tokens','amount':10**9+1}]
 for amount in [1,2,100,10000,35767,10**9]:base.append({'name':f'amount_{amount}','amount':amount})
 for name in ['global','mint','bonding_curve','associated_bonding_curve','associated_user','fee_config']:
  for mut in [{'system_owner':True},{'length':0},{'bytes':[[0,0]]}]:base.append({'name':f'mutate_{name}_{mut}','account_mutations':{name:mut}})
 for name in ['fee_recipient','bonding_curve','associated_bonding_curve','associated_user','creator_vault']:
  base.append({'name':'readonly_'+name,'readonly':[name]})
 for name in ['global','fee_recipient','bonding_curve','associated_bonding_curve','associated_user','creator_vault','fee_config','fee_program','event_authority','program']:
  base.append({'name':'wrong_'+name,'wrong_keys':[name]})
 base += [{'name':'legacy_token','legacy_token':True},{'name':'legacy_cashback','legacy_token':True,'cashback_account':True,'curve_bytes':[[82,1]]}]
 for n in [48,49,80,81,82,83,114,115,123,124,125,140,141,165,166,180]:base.append({'name':f'curve_length_{n}','account_mutations':{'bonding_curve':{'length':n}}})
 for n in [8,40,64,100,2511,2512,4072,4073,4096,4097]:base.append({'name':f'fee_length_{n}','account_mutations':{'fee_config':{'length':n}}})
 for pb,cb,bb in [(0,0,0),(1,1,1),(95,30,10000),(3000,3000,9999),(6000,6000,5000),(10001,0,5000)]:
  base.append({'name':f'fees_{pb}_{cb}_{bb}','account_mutations':{'fee_config':{'u64':[[93,pb],[101,cb]]},'global':{'u64':[[997,bb]]}}})
 for off in [48,81,82,123,124]:base.append({'name':f'bad_bool_{off}','curve_bytes':[[off,2]]})
 base += [{'name':'creator_zero','curve_bytes':[[i,0] for i in range(49,81)]},{'name':'uninitialized_global','account_mutations':{'global':{'bytes':[[8,0]]}}}]
 base += [{'name':'short_curve_low_rent','amount':1,'account_mutations':{'bonding_curve':{'length':81,'lamports':100000}}},{'name':'short_curve_low_rent_trade','account_mutations':{'bonding_curve':{'length':81,'lamports':100000}}},{'name':'short_curve_low_rent_bad_min','minimum':10**12,'account_mutations':{'bonding_curve':{'length':81,'lamports':100000}}}]
 for slot in range(7):base.append({'name':f'recipient_slot_{slot}','recipient_slot':slot})
 for extra in [{'amount':0},{'wrong_keys':['fee_recipient']},{'curve_bytes':[[48,1]]}]:base.append({'name':'short_curve_precedence_'+str(extra),'account_mutations':{'bonding_curve':{'length':81,'lamports':100000}},**extra})
 for n in [141,166]:base.append({'name':f'curve_full_low_rent_{n}','amount':1,'account_mutations':{'bonding_curve':{'length':n,'lamports':100000}}})
 for quote in [f.Pubkey.from_string('So11111111111111111111111111111111111111112'),f.Pubkey(bytes([56])*32)]:base.append({'name':'quote_'+str(quote),'curve_bytes':[(83+i,v) for i,v in enumerate(bytes(quote))]})
 return base

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=f.pathlib.Path);ap.add_argument('--output',type=f.pathlib.Path,required=True);args=ap.parse_args();rows=[]
 for c in cases():
  o=run(c);r={'case':c,'original':o}
  if args.candidate:
   b=run(c,args.candidate);diff=[k for k in ['error','accounts','events','inner','return_data'] if o[k]!=b[k]];r.update(candidate=b,different_fields=diff,match=not diff)
  rows.append(r)
 d={'scope':'Normally signed offline synthetic legacy sell fixtures; full binary identity unproven.','original_sha256':hashlib.sha256((R/'evidence/original/pump/deployed.so').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(args.candidate.read_bytes()).hexdigest() if args.candidate else None,'harness_sha256':hashlib.sha256(f.pathlib.Path(__file__).read_bytes()).hexdigest(),'cases':rows,'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r.get('match') is False]};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(d,indent=2)+'\n');print([(r['case']['name'],r['original']['error'],r.get('different_fields')) for r in rows])
 if d['mismatches']:raise SystemExit(1)
if __name__=='__main__':main()
