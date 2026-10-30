#!/usr/bin/env python3
"""Offline legacy buy recovery: normally signed synthetic transactions, captured dependencies."""
import argparse,base64,hashlib,json,struct,gzip
import pump_trade_fixture as f
from solders.clock import Clock
R=f.R;P=f.Pubkey.from_string(f.x['program']);USER=f.Keypair.from_seed(bytes([231])*32)
INITIAL={k:f.vm.get_account(k) for k in f.msg.account_keys}
CURVE=f.Pubkey.from_string(f.x['accounts']['curve']);GLOBAL=f.Pubkey.from_string(f.x['accounts']['global']);FEE=f.Pubkey.from_string(f.x['accounts']['fee_config'])
IDL=json.loads((R/'evidence/upstream/pump.json').read_text(encoding='utf-8'));IX=next(i for i in IDL['instructions'] if i['name']=='buy')
def run(c,binary=None):
 IX=next(i for i in IDL['instructions'] if i['name']==c.get('kind','buy'))
 vm=f.LiteSVM().with_transaction_history(0)
 if 'unix_timestamp' in c:vm.set_clock(Clock(1,0,0,0,c['unix_timestamp']))
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
 gv=f.Pubkey.find_program_address([b'global_volume_accumulator'],P)[0];uv=f.Pubkey.find_program_address([b'user_volume_accumulator',bytes(USER.pubkey())],P)[0]
 keys.update(global_volume_accumulator=gv,user_volume_accumulator=uv)
 gd=bytearray(600);gd[:8]=bytes(next(a['discriminator'] for a in IDL['accounts'] if a['name']=='GlobalVolumeAccumulator'));struct.pack_into('<qqq',gd,8,1000,10000,86400)
 
 for off,val in c.get('global_volume_i64',[]):struct.pack_into('<q',gd,off,val)
 vm.set_account(gv,f.Account(10**8,bytes(gd),P))
 ud=bytearray(137);ud[:8]=bytes(next(a['discriminator'] for a in IDL['accounts'] if a['name']=='UserVolumeAccumulator'));ud[8:40]=bytes(USER.pubkey())
 
 for off,val in c.get('user_volume_i64',[]):struct.pack_into('<q',ud,off,val)
 vm.set_account(uv,f.Account(10**8,bytes(ud),P))
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
  if ac is not None:vm.set_account(key,ac)
  metas[idx]=f.AccountMeta(key,old.is_signer,old.is_writable)
 for name in c.get('readonly',[]):
  i=next(i for i,a in enumerate(IX['accounts']) if a['name']==name);metas[i]=f.AccountMeta(metas[i].pubkey,metas[i].is_signer,False)
 trade=f.Instruction(P,bytes(IX['discriminator'])+struct.pack('<QQ',c.get('amount',500000000),c.get('minimum',10**12))+bytes(c.get('trailing',[])),metas)
 tx=f.Transaction.new_signed_with_payer([*f.ixs[:-1],trade],USER.pubkey(),[USER],vm.latest_blockhash());tx.verify()
 before={str(k):vm.get_account(k) for k in tx.message.account_keys if k!=P};res=vm.send_transaction(tx);failed=isinstance(res,f.FailedTransactionMetadata);meta=res.meta() if failed else res
 def snap(a):return None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':None if a.executable else base64.b64encode(a.data).decode(),'executable':a.executable}
 return {'error':str(res.err()) if failed else None,'accounts':{str(k):snap(vm.get_account(k)) for k in tx.message.account_keys if k!=P},'before':{k:snap(v) for k,v in before.items()},'events':[l[14:] for l in meta.logs() if l.startswith('Program data: ')],'return_data':json.loads(meta.to_json()).get('return_data'),'inner':json.loads(meta.to_json())['inner_instructions'],'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'signatures_verified':True}
def cases():
 rows=[]
 for kind in ['buy','buy_exact_sol_in']:
  for amount in [0,1,1000,500000000,10**9]:
   for trailing in [[],[0,0],[1,0],[0,1]]:
    rows.append({'name':f'{kind}_{amount}_{trailing}','kind':kind,'amount':amount,'minimum':10**12 if kind=='buy' else 1,'trailing':trailing})
 for kind in ['buy','buy_exact_sol_in']:
  base={'kind':kind,'amount':10**9,'minimum':10**12 if kind=='buy' else 1}
  for flags in [[],[[81,1]],[[82,1]],[[124,1]]]:
   for trailing in [[],[1,0],[0,1]]:rows.append({**base,'name':f'flags_{flags}_{trailing}','curve_bytes':flags,'reserved':flags==[[81,1]],'trailing':trailing})
  for trailing in [[],[1,0],[0,1],[1,1]]:
   for fields in [[[8,-1],[16,10000],[24,100]],[[8,-100],[16,10000],[24,100]],[[8,-1],[16,10000],[24,0]]]:rows.append({**base,'name':f'active_volume_{trailing}_{fields}','trailing':trailing,'global_volume_i64':fields})
  for name in ['global_volume_accumulator','user_volume_accumulator']:
   for mutation in [{'system_owner':True},{'length':0},{'length':8},{'bytes':[[0,0]]}]:rows.append({**base,'name':f'mutate_{name}_{mutation}','account_mutations':{name:mutation}})
  for amount in ([793099000000000,793099000000001,10**15] if kind=='buy' else [10**11,10**12]):
   for partial in [0,1]:rows.append({**base,'name':f'completion_{amount}_{partial}','amount':amount,'trailing':[0,partial]})
 for kind in ['buy','buy_exact_sol_in']:
  base={'kind':kind,'amount':10**9,'minimum':10**12 if kind=='buy' else 1}
  for track in [0,1]:
   for start in [-1,-100,-101]:
    for last in [0,-101]:
     rows.append({**base,'name':f'campaign_{track}_{start}_{last}','trailing':[track,0],'global_volume_i64':[[8,start],[16,10000],[24,100],[64,10**12],[72,10**12]],'user_volume_i64':[[65,last]]})
  for mutation in ['creator_zero','missing_remaining','missing_buyback']:
   changes={'curve_bytes':[[off,0] for off in range(49,81)]} if mutation=='creator_zero' else {'remaining':False} if mutation=='missing_remaining' else {'omit_buyback':True}
   rows.append({**base,'name':mutation,**changes})
 for kind in ['buy','buy_exact_sol_in']:
  for bps in [1,500,10000,10001,2**64-1]:
   for flag in [None,81,82,124]:
    rows.append({'kind':kind,'name':f'creator_override_{bps}_{flag}','amount':10**9,'minimum':10**12 if kind=='buy' else 1,'curve_u64':[[115,bps]],'curve_bytes':[] if flag is None else [[flag,1]],'reserved':flag==81})
 for kind in ['buy','buy_exact_sol_in']:
  for track in [0,1]:
   for now in [0,1,500,10000,10001]:
    rows.append({'kind':kind,'name':f'positive_clock_{track}_{now}','amount':10**9,'minimum':10**12 if kind=='buy' else 1,'trailing':[track,0],'unix_timestamp':now,'global_volume_i64':[[8,1],[16,10000],[24,100]]+[[off,10**12] for off in range(64,304,8)],'user_volume_i64':[[65,1]]})
 for bps in [2**63,2**64-10000,2**64-96,2**64-95,2**64-1]:
  for spend in [1,1000,10000,19999,20000,10**9]:
   rows.append({'kind':'buy_exact_sol_in','name':f'extreme_override_{bps}_{spend}','amount':spend,'minimum':1,'curve_u64':[[115,bps]]})
 mint=bytes(f.ixs[-1].accounts[1].pubkey)
 for kind in ['buy','buy_exact_sol_in']:
  for track in [0,1]:
   for now,last in [(1000,999),(1001,1000),(1050,1001),(1101,1001),(4999,4900),(5000,4900)]:
    for claim in [0,1]:
     rows.append({'kind':kind,'name':f'nonzero_volume_{kind}_{track}_{now}_{last}_{claim}','amount':10**9,'minimum':10**12 if kind=='buy' else 1,'trailing':[track,0],'unix_timestamp':now,'global_volume_i64':[[8,1000],[16,5000],[24,100]],'user_volume_i64':[[65,last]],'account_mutations':{'global_volume_accumulator':{'bytes':[[32+i,v] for i,v in enumerate(mint)],'u64':[[o,10**12] for o in range(64,304,8)]+[[o,10**9] for o in range(304,544,8)]},'user_volume_accumulator':{'bytes':[[40,claim],[73,1]],'u64':[[41,100],[49,200],[57,1110]]}}})
 for spend in [1,10**9]:rows.append({'kind':'buy_exact_sol_in','name':f'zero_creator_extreme_{spend}','amount':spend,'minimum':1,'curve_u64':[[115,2**64-1]],'curve_bytes':[[o,0] for o in range(49,81)]})
 return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=f.pathlib.Path);ap.add_argument('--output',type=f.pathlib.Path,required=True);args=ap.parse_args();rows=[]
 for c in cases():
  o=run(c);r={'case':c,'original':o}
  if args.candidate:
   b=run(c,args.candidate);diff=[k for k in ['error','accounts','events','inner','return_data'] if o[k]!=b[k]];r.update(candidate=b,different_fields=diff,match=not diff)
  rows.append(r)
 d={'scope':'Normally signed offline synthetic legacy buy fixtures; full binary identity unproven.','original_sha256':hashlib.sha256((R/'evidence/original/pump/deployed.so').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(args.candidate.read_bytes()).hexdigest() if args.candidate else None,'script_sha256':hashlib.sha256(f.pathlib.Path(__file__).read_bytes()).hexdigest(),'harness_sha256':hashlib.sha256(f.pathlib.Path(__file__).read_bytes()).hexdigest(),'cases':rows,'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r.get('match') is False]};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'case_count':len(rows),'mismatches':d['mismatches']}));assert not d['mismatches']
if __name__=='__main__':main()
