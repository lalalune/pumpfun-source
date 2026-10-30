#!/usr/bin/env python3
"""Normally signed, synthetic offline legacy sell_v2 recovery."""
import argparse,base64,hashlib,json,struct
import pump_trade_fixture as f
R=f.R;P=f.Pubkey.from_string(f.x['program']);USER=f.Keypair.from_seed(bytes([231])*32)
INITIAL={k:f.vm.get_account(k) for k in f.msg.account_keys};CURVE=f.Pubkey.from_string(f.x['accounts']['curve']);GLOBAL=f.Pubkey.from_string(f.x['accounts']['global']);FEE=f.Pubkey.from_string(f.x['accounts']['fee_config'])
FEES=f.Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ');TOKEN=f.Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=f.Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=f.Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');WSOL=f.Pubkey.from_string('So11111111111111111111111111111111111111112');USDC=f.Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
IX=next(i for i in json.loads((R/'evidence/upstream/pump.json').read_text(encoding='utf-8'))['instructions'] if i['name']=='sell_v2')
def run(c,binary=None):
 vm=f.LiteSVM().with_transaction_history(0).with_sigverify(True)
 for name in ['pump','pump_fees']:
  cap=json.loads((R/f'evidence/original/{name}/capture.json').read_text());vm.add_program_from_file(f.Pubkey.from_string(cap['program']),binary if name=='pump' and binary else R/f'evidence/original/{name}/deployed.so')
 for name in ['spl_token','spl_token_2022','associated_token']:
  cap=json.loads((R/f'evidence/dependencies/{name}/capture.json').read_text());vm.add_program_from_file(f.Pubkey.from_string(cap['program']),R/f'evidence/dependencies/{name}/deployed.so')
 for k,a in INITIAL.items():
  if a is not None and not a.executable:vm.set_account(k,a)
 v3=f.ixs[-1].accounts;data=bytearray(INITIAL[CURVE].data);quote=(f.Pubkey(bytes([56])*32) if c.get('exotic') else USDC) if c.get('token_quote') else WSOL;token=TOKEN22 if c.get('token22') else TOKEN
 if c.get('token_quote'):data[83:115]=bytes(quote)
 if c.get('sharing'):
  sharing=f.Pubkey.find_program_address([b'sharing-config',bytes(v3[1].pubkey)],FEES)[0];data[49:81]=bytes(sharing)
 for off,val in c.get('curve_bytes',[]):data[off]=val
 vm.set_account(CURVE,f.Account(INITIAL[CURVE].lamports,bytes(data),P));creator=f.Pubkey(data[49:81]);vault=f.Pubkey.find_program_address([b'creator-vault',bytes(creator)],P)[0];recipient=f.Pubkey(INITIAL[GLOBAL].data[483:515] if c.get('reserved') else INITIAL[GLOBAL].data[41:73]);sharing=f.Pubkey.find_program_address([b'sharing-config',bytes(v3[1].pubkey)],FEES)[0]
 keys={'global':GLOBAL,'base_mint':v3[1].pubkey,'quote_mint':quote,'base_token_program':v3[3].pubkey,'quote_token_program':token,'associated_token_program':ATA,'fee_recipient':recipient,'buyback_fee_recipient':v3[13].pubkey,'bonding_curve':CURVE,'associated_base_bonding_curve':v3[6].pubkey,'user':USER.pubkey(),'associated_base_user':v3[9].pubkey,'creator_vault':vault,'sharing_config':sharing,'user_volume_accumulator':v3[11].pubkey,'fee_config':FEE,'fee_program':FEES,'system_program':f.Pubkey.default(),'event_authority':f.Pubkey.find_program_address([b'__event_authority'],P)[0],'program':P}
 for k in [recipient,vault,sharing]:
  if vm.get_account(k) is None:vm.set_account(k,f.Account(10**7,b'',f.Pubkey.default()))
 if c.get('sharing') or c.get('sharing_data_only'):
  shared=hashlib.sha256(b'account:SharingConfig').digest()[:8]+bytes([255,2,1])+bytes(v3[1].pubkey)+bytes(USER.pubkey())+bytes([0])+struct.pack('<I',1)+bytes(USER.pubkey())+struct.pack('<H',10000)
  vm.set_account(sharing,f.Account(10**7,shared,FEES))
 mint=bytearray(82);struct.pack_into('<Q',mint,36,10**15);mint[44]=6 if c.get('token_quote') else 9;mint[45]=1;vm.set_account(quote,f.Account(10**9,bytes(mint),token))
 for name,authority in [('associated_quote_fee_recipient',recipient),('associated_quote_buyback_fee_recipient',keys['buyback_fee_recipient']),('associated_quote_bonding_curve',CURVE),('associated_quote_user',USER.pubkey()),('associated_creator_vault',vault),('associated_user_volume_accumulator',keys['user_volume_accumulator'])]:
  key=f.Pubkey.find_program_address([bytes(authority),bytes(token),bytes(quote)],ATA)[0];keys[name]=key;d=bytearray(165);d[:32]=bytes(quote);d[32:64]=bytes(authority);struct.pack_into('<Q',d,64,10**12);d[108]=1;vm.set_account(key,f.Account(10**9,bytes(d),token))
 if c.get('transfer_fee_bps') is not None:
  ac=vm.get_account(quote);conf=bytes(72)+struct.pack('<QQH',0,c.get('max_fee',2**64-1),c['transfer_fee_bps'])+struct.pack('<QQH',0,c.get('max_fee',2**64-1),c['transfer_fee_bps'])
  blob=ac.data[:82]+bytes(83)+bytes([1])+struct.pack('<HH',1,len(conf))+conf
  vm.set_account(quote,f.Account(ac.lamports,blob,ac.owner))
  for name in ['associated_quote_fee_recipient','associated_quote_buyback_fee_recipient','associated_quote_bonding_curve','associated_quote_user','associated_creator_vault','associated_user_volume_accumulator']:
   key=keys[name];ac=vm.get_account(key);blob=ac.data[:165]+bytes([2])+struct.pack('<HHQ',2,8,0);vm.set_account(key,f.Account(ac.lamports,blob,ac.owner))
 for name,spec in c.get('account_mutations',{}).items():
  key=keys[name];ac=vm.get_account(key);d=bytearray(ac.data)
  for off,val in spec.get('bytes',[]):d[off]=val
  for off,val in spec.get('u64',[]):struct.pack_into('<Q',d,off,val)
  d=d[:spec.get('length',len(d))];vm.set_account(key,f.Account(spec.get('lamports',ac.lamports),bytes(d),f.Pubkey.default() if spec.get('system_owner') else ac.owner))
 for name in c.get('absent',[]):vm.set_account(keys[name],f.Account(0,b'',f.Pubkey.default()))
 metas=[f.AccountMeta(keys[a['name']],a.get('signer',False),a.get('writable',False)) for a in IX['accounts']]
 for name in c.get('wrong_keys',[]):
  idx=next(i for i,a in enumerate(IX['accounts']) if a['name']==name);old=metas[idx];key=f.Pubkey(bytes([77+idx])*32);ac=vm.get_account(old.pubkey)
  if ac is not None:vm.set_account(key,f.Account(10**7,ac.data,ac.owner,ac.executable) if ac.executable else ac)
  metas[idx]=f.AccountMeta(key,old.is_signer,old.is_writable)
 for name in c.get('readonly',[]):
  idx=next(i for i,a in enumerate(IX['accounts']) if a['name']==name);old=metas[idx];metas[idx]=f.AccountMeta(old.pubkey,old.is_signer,False)

 trade=f.Instruction(P,bytes(IX['discriminator'])+struct.pack('<QQ',c.get('amount',500000000),c.get('minimum',0)),metas);tx=f.Transaction.new_signed_with_payer([*f.ixs[:-1],trade],USER.pubkey(),[USER],vm.latest_blockhash());tx.verify();res=vm.send_transaction(tx);failed=isinstance(res,f.FailedTransactionMetadata);meta=res.meta() if failed else res
 def snap(a):return None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':None if a.executable else base64.b64encode(a.data).decode(),'executable':a.executable}
 return {'error':str(res.err()) if failed else None,'accounts':{str(k):snap(vm.get_account(k)) for k in tx.message.account_keys if k!=P},'events':[l[14:] for l in meta.logs() if l.startswith('Program data: ')],'inner':json.loads(meta.to_json())['inner_instructions'],'return_data':json.loads(meta.to_json()).get('return_data'),'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'signatures_verified':True}
def cases():
 cases=[{'name':'native'},{'name':'zero','amount':0},{'name':'slippage','minimum':10**12},{'name':'token','token_quote':True},{'name':'token22','token_quote':True,'token22':True},{'name':'cashback','curve_bytes':[[82,1]]},{'name':'holder','curve_bytes':[[124,1]]}]
 for token in [False,True]:
  for name in ['associated_quote_fee_recipient','associated_quote_buyback_fee_recipient','associated_quote_user','associated_creator_vault','associated_user_volume_accumulator','associated_quote_bonding_curve','sharing_config','user_volume_accumulator']:
   cases.append({'name':f'absent_{name}_{token}','token_quote':token,'absent':[name]})
  for name in ['quote_mint','quote_token_program','sharing_config','user_volume_accumulator','associated_quote_fee_recipient','associated_quote_buyback_fee_recipient','associated_quote_user','associated_creator_vault','associated_user_volume_accumulator','associated_quote_bonding_curve']:
   cases.append({'name':f'wrong_{name}_{token}','token_quote':token,'wrong_keys':[name]})
 for token in [False,True]:
  for name in ['quote_mint','associated_quote_bonding_curve','associated_quote_user','associated_quote_fee_recipient','associated_creator_vault','user_volume_accumulator']:
   for mut in [{'system_owner':True},{'length':0},{'bytes':[[0,0]]}]:cases.append({'name':f'mut_{name}_{token}_{mut}','token_quote':token,'account_mutations':{name:mut}})
 for name in ['associated_quote_bonding_curve','associated_quote_user','associated_quote_fee_recipient','associated_creator_vault']:
  cases.append({'name':'token_authority_'+name,'token_quote':True,'account_mutations':{name:{'bytes':[[32,99]]}}})
 for token in [False,True]:
  for flags in [[],[[82,1]],[[124,1]]]:
   for amount in [0,1,35767,10**9,10**9+1]:cases.append({'name':f'amount_{token}_{flags}_{amount}','token_quote':token,'curve_bytes':flags,'amount':amount})
 cases += [{'name':'sharing_native','sharing':True},{'name':'sharing_token','sharing':True,'token_quote':True}]
 for token in [False,True]:
  for mut in [{'bytes':[[0,0]]},{'system_owner':True},{'length':0},{'bytes':[[10,0]]},{'bytes':[[9,0]]}]:cases.append({'name':f'sharing_mut_{token}_{mut}','sharing':True,'token_quote':token,'account_mutations':{'sharing_config':mut}})
 for name in ['global','base_mint','bonding_curve','associated_base_bonding_curve','associated_base_user','fee_config']:
  for mut in [{'system_owner':True},{'length':0},{'bytes':[[0,0]]}]:cases.append({'name':f'context_{name}_{mut}','account_mutations':{name:mut}})
 for name in ['fee_recipient','buyback_fee_recipient','creator_vault','associated_quote_bonding_curve','associated_quote_user','user_volume_accumulator']:
  cases.append({'name':'readonly_'+name,'readonly':[name]})
 cases += [{'name':'volume_stored_user','account_mutations':{'user_volume_accumulator':{'bytes':[[8,99]]}}},{'name':'volume_zero_user','account_mutations':{'user_volume_accumulator':{'bytes':[[i,0] for i in range(8,40)]}}}]
 for token in [False,True]:
  cases.append({'name':f'mayhem_{token}','token_quote':token,'reserved':True,'curve_bytes':[[81,1]]})
  cases.append({'name':f'creator_zero_{token}','token_quote':token,'curve_bytes':[[i,0] for i in range(49,81)]})
 for n in [81,83,115,125,140,141,165,166]:cases.append({'name':f'curve_length_{n}','account_mutations':{'bonding_curve':{'length':n}}})
 for n in [81,166]:cases.append({'name':f'curve_rent_{n}','amount':1,'account_mutations':{'bonding_curve':{'length':n,'lamports':100000}}})
 for token22 in [False,True]:
  for name in ['associated_quote_fee_recipient','associated_creator_vault','associated_user_volume_accumulator']:
   cases.append({'name':f'ata_creation_{name}_{token22}','token_quote':True,'token22':token22,'absent':[name]})
 cases.append({'name':'sharing_data_unrelated_creator','sharing_data_only':True})
 for token in [False,True]:
  for bps in [0,1,500,10000,10001]:cases.append({'name':f'configured_fee_{token}_{bps}','token_quote':token,'curve_bytes':[(115+i,v) for i,v in enumerate(struct.pack('<Q',bps))]})
 for bps in [0,500]:cases.append({'name':f'exotic_fee_{bps}','token_quote':True,'exotic':True,'curve_bytes':[(115+i,v) for i,v in enumerate(struct.pack('<Q',bps))]})
 # Frozen fixture output before quote transfer fees is 13,804. Exercise both
 # sides of the original program's observed net-output slippage boundary.
 for bps,net in [(0,13804),(100,13665),(250,13458),(10000,0)]:
  for minimum in sorted({0,max(0,net-1),net,net+1,13804}):
   cases.append({'name':f'transfer_fee_{bps}_minimum_{minimum}','token_quote':True,'token22':True,'transfer_fee_bps':bps,'minimum':minimum})
 for max_fee in [0,1,7]:
  cases.append({'name':f'transfer_fee_cap_{max_fee}','token_quote':True,'token22':True,'transfer_fee_bps':250,'max_fee':max_fee})
 for flags in [[[82,1]],[[124,1]]]:
  cases.append({'name':f'transfer_fee_flags_{flags}','token_quote':True,'token22':True,'transfer_fee_bps':250,'curve_bytes':flags})
 return cases

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=f.pathlib.Path);ap.add_argument('--output',type=f.pathlib.Path,required=True);a=ap.parse_args();rows=[]
 for c in cases():
  o=run(c);r={'case':c,'original':o}
  if a.candidate:
   b=run(c,a.candidate);diff=[k for k in ['error','accounts','events','inner','return_data'] if o[k]!=b[k]];r.update(candidate=b,match=not diff,different_fields=diff)
  rows.append(r)
 d={'scope':'Bounded offline sell_v2 synthetic state; normal test-owned signatures and genuine captured dependency CPIs. Full binary equality unproven. Executable bytes excluded from semantic snapshot comparison; ELF hashes recorded separately.','original_sha256':hashlib.sha256((R/'evidence/original/pump/deployed.so').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest() if a.candidate else None,'harness_sha256':hashlib.sha256(f.pathlib.Path(__file__).read_bytes()).hexdigest(),'fixture_import_sha256':hashlib.sha256(f.pathlib.Path(f.__file__).read_bytes()).hexdigest(),'case_count':len(rows),'cases':rows,'mismatches':[i for i,r in enumerate(rows) if r.get('match') is False]};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print([(r['case']['name'],r['original']['error'],r.get('different_fields')) for r in rows]);
 if d['mismatches']:raise SystemExit(1)
if __name__=='__main__':main()
