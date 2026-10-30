#!/usr/bin/env python3
"""SBF v2 trading differential using captured token dependencies and fee-config state."""
import sys
sys.path.insert(0,'scripts')
from pump_amm_liquidity_differential import *
from pump_amm_reusable_harness import acquire_harness, pin_program
FEES=Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
feeconfig=Pubkey.from_string(f['keys']['fee_config']);buyback=Pubkey.from_string(f['accounts']['buyback_fee_recipient']['address']);volume=Pubkey.find_program_address([b'user_volume_accumulator',bytes(PAYER.pubkey())],PROGRAM)[0]
def trade(name,amount,limit,overrides=None,candidate=None,unsigned=False,payload_length=None):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,filepath in [(TOKEN,'evidence/dependencies/spl_token/deployed.so'),(TOKEN22,'evidence/dependencies/spl_token_2022/deployed.so'),(FEES,'evidence/original/pump_fees/deployed.so')]:h.vm.add_program_from_file(pid,ROOT/filepath)
 glob=bytearray(RAW);glob[56]=0;h.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'],bytes(glob),PROGRAM))
 for n,row in f['accounts'].items():h.vm.set_account(Pubkey.from_string(row['address']),Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
 for k,m,native in [(userbase,base,False),(userquote,quote,True)]:h.vm.set_account(k,Account(10**15+2039280 if native else 10**9,token(m,PAYER.pubkey(),10**15,native),TOKEN))
 h.vm.set_account(volume,Account(0,b'',Pubkey.default()))
 ix=next(x for x in IDL['instructions'] if x['name']==name)
 keys=[pool,PAYER.pubkey(),CONFIG_KEY,base,quote,userbase,userquote,vaultbase,vaultquote,TOKEN,TOKEN,Pubkey.default(),volume,feeconfig,buyback,EVENT,PROGRAM]
 metas=[AccountMeta(k,bool(row.get('signer')),bool(row.get('writable'))) for k,row in zip(keys,ix['accounts'])]
 if overrides:overrides(h,metas)
 data=bytes(ix['discriminator'])+struct.pack('<QQ',amount,limit)
 watch=[metas[i].pubkey for i in [0,1,2,3,4,5,6,7,8,12,13,14]]
 before={str(k):h.vm.get_account(k) for k in watch}
 if payload_length is not None:data=data[:payload_length]
 payer=OUTSIDER if unsigned else PAYER
 if unsigned:metas[1]=AccountMeta(PAYER.pubkey(),False,True)
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,metas)],payer.pubkey(),[payer],h.vm.latest_blockhash());r=h.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 states={}
 for k in watch:
  a=h.vm.get_account(k);b=before[str(k)];states[str(k)]={'data_hex':bytes(a.data).hex() if a else None,'lamports':a.lamports if a else 0,'owner':str(a.owner) if a else None,'token_delta':int.from_bytes(a.data[64:72],'little')-int.from_bytes(b.data[64:72],'little') if a and b and k not in [pool,volume] else None}
 return {'error':str(r.err()) if failed else None,'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions'],'states':states}

def trade_transferfee(key,bps=100,maximum=2**64-1):
 def ov(h,m):
  transferfee(key,bps,maximum)(h,m);idx=9 if key==base else 10;m[idx]=AccountMeta(TOKEN22,False,False)
  if key==quote:
   a=h.vm.get_account(buyback);owner=Pubkey.from_bytes(a.data[32:64]);newkey=Pubkey.find_program_address([bytes(owner),bytes(TOKEN22),bytes(quote)],Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'))[0];d=bytearray(a.data[:165])+bytes([2])+struct.pack('<HHQ',2,8,0);h.vm.set_account(newkey,Account(a.lamports,bytes(d),TOKEN22));m[14]=AccountMeta(newkey,False,True)
 return ov

PUMP=Pubkey.from_string(json.load(open('evidence/upstream/pump.json', encoding='utf-8'))['address'])
def rekey_pool(quote_key,canonical=True,index=0):
 def apply(h,m):
  old=h.vm.get_account(pool);data=bytearray(old.data)
  creator=Pubkey.find_program_address([b'pool-authority',bytes(base)],PUMP)[0] if canonical else OUTSIDER.pubkey()
  newpool,bump=Pubkey.find_program_address([b'pool',struct.pack('<H',index),bytes(creator),bytes(base),bytes(quote_key)],PROGRAM)
  data[8]=bump;data[9:11]=struct.pack('<H',index);data[11:43]=bytes(creator);data[75:107]=bytes(quote_key);h.vm.set_account(newpool,Account(old.lamports,bytes(data),old.owner));m[0]=AccountMeta(newpool,False,True)
  oldmint=h.vm.get_account(quote);h.vm.set_account(quote_key,oldmint);m[4]=AccountMeta(quote_key,False,False)
  for key in [vaultbase,vaultquote,userquote]:
   a=h.vm.get_account(key);d=bytearray(a.data)
   if key!=vaultbase:d[:32]=bytes(quote_key)
   if key!=userquote:d[32:64]=bytes(newpool)
   h.vm.set_account(key,Account(a.lamports,bytes(d),a.owner))
  a=h.vm.get_account(buyback);owner=Pubkey.from_bytes(a.data[32:64]);recipient=Pubkey.find_program_address([bytes(owner),bytes(TOKEN),bytes(quote_key)],Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'))[0];d=bytearray(a.data);d[:32]=bytes(quote_key);h.vm.set_account(recipient,Account(a.lamports,bytes(d),a.owner));m[14]=AccountMeta(recipient,False,True)
 return apply

def custom_fee_table(tiers):
 def apply(h,m):
  a=h.vm.get_account(feeconfig);raw=bytes(a.data[:41])+struct.pack('<QQQ',25,5,0)+struct.pack('<I',len(tiers))
  for threshold,fees in tiers:raw+=threshold.to_bytes(16,'little')+struct.pack('<QQQ',*fees)
  raw+=struct.pack('<I',0)+bytes(24);h.vm.set_account(feeconfig,Account(a.lamports,raw.ljust(4097,b'\0'),a.owner))
 return apply

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);args=p.parse_args();rows=[]
 def test(name,label,**kw):
  params=dict(amount=10**7 if name=='buy_exact_quote_in_v2' else 10**10,limit=10**9 if name=='buy_v2' else 1);params.update(kw)
  a=trade(name,**params);b=trade(name,candidate=args.candidate,**params)
  a['events']=[l for l in a['logs'] if l.startswith('Program data: ')];b['events']=[l for l in b['logs'] if l.startswith('Program data: ')]
  diff=[k for k in a if k!='logs' and a[k]!=b[k]]
  rows.append({'instruction':name,'case':label,'original':a,'candidate':b,'match':not diff,'mismatched_fields':diff})
 for n in ['buy_v2','sell_v2','buy_exact_quote_in_v2']:
  for amount in [0,1,2,3,4,5,10,100,1000,10**7,10**10,int(f['pool_base_vault_amount_raw']),int(f['pool_base_vault_amount_raw'])+1,2**64-1]:test(n,'amount='+str(amount),amount=amount)
  for limit in [0,1,2**64-1]:test(n,'limit='+str(limit),limit=limit)
  test(n,'unsigned',unsigned=True)
  for length in range(24):test(n,'payload-length='+str(length),payload_length=length)
  for index in [0,1,5,6,7,8,12,14]:test(n,'readonly='+str(index),overrides=meta_mutation(index,'readonly'))
  for index in [0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]:test(n,'substitute='+str(index),overrides=meta_mutation(index,'substitute'))
  for k in [base,quote]:
   for bps in [0,1,100,9999,10000]:
    for maximum in [0,1,123,2**64-1]:test(n,'transfer-fee='+str((k,bps,maximum)),overrides=trade_transferfee(k,bps,maximum))
  for off,value in [(243,b'\x01'),(244,b'\x01'),(270,b'\x01'),(211,bytes(32)),(261,struct.pack('<Q',100)),(245,(10**9).to_bytes(16,'little',signed=True)),(245,(-10**13).to_bytes(16,'little',signed=True))]:test(n,'pool='+str((off,value.hex())),overrides=mutate(pool,off,value))
  for key in [pool,CONFIG_KEY,base,quote,userbase,userquote,vaultbase,vaultquote,feeconfig,buyback]:
   test(n,'wrong-owner='+str(key),overrides=mutate(key,0,b'',owner=Pubkey.default()))
  for k,off,value,length,owner in [(feeconfig,0,b'',0,None),(feeconfig,0,b'',2511,None),(feeconfig,0,b'',None,PROGRAM),(feeconfig,0,bytes(8),None,None),(buyback,32,bytes(32),None,None),(buyback,0,bytes(32),None,None),(userbase,32,bytes(32),None,None),(userquote,32,bytes(32),None,None)]:test(n,'field='+str((k,off,value.hex(),length,owner)),overrides=mutate(k,off,value,length,owner))
  for key,offset in [(vaultbase,64),(vaultquote,64),(userbase,64),(userquote,64),(base,36)]:
   for value in [0,1,2**64-1]:test(n,'token-amount='+str((key,offset,value)),overrides=mutate(key,offset,struct.pack('<Q',value)))
  for value in [-2**127,-10**13,-125882,0,1,10**9,2**64,2**127-1]:test(n,'virtual='+str(value),overrides=mutate(pool,245,value.to_bytes(16,'little',signed=True)))
  for flags in [0,1,2,4,8,16,31,255]:test(n,'disable='+str(flags),overrides=mutate(CONFIG_KEY,56,bytes([flags])))
  for key in [quote,Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'),Pubkey.from_bytes(bytes([90])*32)]:
   for canonical in [False,True]:
    for length in [65,69,1068,1069,2511,2512,3000,4072,4073,4096,4097]:test(n,'quote-layout='+str((key,canonical,length)),overrides=combine(rekey_pool(key,canonical),mutate(feeconfig,0,b'',length)))
  for length in [0,7,8,210,211,243,244,245,261,270,271,286,287,300]:test(n,'pool-layout='+str(length),overrides=mutate(pool,0,b'',length))
  for length in [211,245,287,300]:
   def low_pool(h,m,length=length):
    account=h.vm.get_account(pool);h.vm.set_account(pool,Account(1,bytes(account.data[:length]),account.owner))
   test(n,'pool-low-rent='+str(length),overrides=low_pool)
  for length in [0,7,8,40,73,89,90,136,137,138]:
   def existing(h,m,length=length):
    raw=bytes(next(x for x in IDL['accounts'] if x['name']=='UserVolumeAccumulator')['discriminator'])+bytes(PAYER.pubkey())+bytes(97)
    h.vm.set_account(volume,Account(10**9,raw[:length].ljust(length,b'\0'),PROGRAM))
   test(n,'existing-volume-length='+str(length),overrides=existing)
  for offset,value in [(8,bytes(OUTSIDER.pubkey())),(40,b'\x01'),(41,struct.pack('<Q',123)),(49,struct.pack('<Q',456)),(57,struct.pack('<Q',789)),(65,struct.pack('<Q',1234)),(73,b'\x01'),(74,struct.pack('<Q',123)),(82,struct.pack('<Q',456))]:
   def existing_field(h,m,offset=offset,value=value):
    raw=bytearray(bytes(next(x for x in IDL['accounts'] if x['name']=='UserVolumeAccumulator')['discriminator'])+bytes(PAYER.pubkey())+bytes(97));raw[offset:offset+len(value)]=value;h.vm.set_account(volume,Account(10**9,bytes(raw),PROGRAM))
   test(n,'existing-volume-field='+str((offset,value.hex())),overrides=existing_field)
  for tiers in [[],[(0,(0,0,0))],[(0,(10,20,30))],[(2**120,(10,20,30)),(0,(40,50,60))],[(0,(10,20,30)),(0,(40,50,60))],[(0,(10000,10000,10000))],[(0,(2**64-1,0,0))]]:test(n,'fee-table='+str(tiers),overrides=custom_fee_table(tiers))
  for off in [261,271,279]:
   for value in [0,1,10**9,2**64-1]:test(n,'pool-fees='+str((off,value)),overrides=mutate(pool,off,struct.pack('<Q',value)))
  for value in [0,1,9999,10000,10001,2**64-1]:test(n,'buyback-bps='+str(value),overrides=mutate(CONFIG_KEY,899,struct.pack('<Q',value)))
 failures=[i for i,r in enumerate(rows) if not r['match']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report={'scope':'SBF v2 buy/sell/exact-quote: committed account bytes, lamports, errors, exact token/System/event CPIs. Captured token dependency binaries; synthetic signer and balance fixtures. Not whole-program or exhaustive extension equivalence.','candidate_sha256':sha(pin_program(args.candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(pathlib.Path(__file__)),'harness_sha256':sha(ROOT/'scripts/pump_amm_reusable_harness.py'),'case_count':len(rows),'mismatches':failures,'cases':rows}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'case_count':len(rows),'mismatch_count':len(failures),'mismatches':failures[:50]}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
